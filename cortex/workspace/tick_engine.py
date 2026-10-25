import asyncio
import json
import math
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple
import numpy as np
from cortex.embodiment.system_somatosensory import SystemSomatosensory

TransitionTag = Literal["[THINK_MORE]", "[RESPONSE]", "[NO_OP]"]

class TickResult(str):
    """
    Subclasses str for 100% backward compatibility with equality checks
    while carrying full structured cognitive telemetry for interactive clients.
    """
    transition: TransitionTag
    tick_id: int
    winning_thought: Any
    action_executed: Optional[Dict[str, Any]]
    action_result: Optional[Dict[str, Any]]
    user_response: str
    entropy: float
    temperature: float
    uncertainty: Dict[str, Any]
    hold_card: Optional[Dict[str, Any]]
    candidates: List[Any]

    def __new__(
        cls,
        transition: TransitionTag,
        tick_id: int = 0,
        winning_thought: Any = None,
        action_executed: Optional[Dict[str, Any]] = None,
        action_result: Optional[Dict[str, Any]] = None,
        user_response: str = "",
        entropy: float = 1.0,
        temperature: float = 0.4,
        uncertainty: Optional[Dict[str, Any]] = None,
        hold_card: Optional[Dict[str, Any]] = None,
        candidates: Optional[List[Any]] = None
    ):
        obj = str.__new__(cls, transition)
        obj.transition = transition
        obj.tick_id = tick_id
        obj.winning_thought = winning_thought
        obj.action_executed = action_executed
        obj.action_result = action_result
        obj.user_response = user_response
        obj.entropy = entropy
        obj.temperature = temperature
        obj.uncertainty = uncertainty or {}
        obj.hold_card = hold_card
        obj.candidates = candidates or []
        return obj

@dataclass
class GlobalWorkspaceState:
    tick_id: int = 0
    p_self: str = (
        "I am CortexOS, an autonomous, self-learning cognitive operating system "
        "embodied on this laptop. I think in the first person ('I'). I prioritize "
        "deterministic reversibility, epistemic provenance, and calibrated restraint. "
        "When I lack a capability, I synthesize and verify new modular tools."
    )
    stm_buffer: List[str] = field(default_factory=list)
    stm_token_limit: int = 4000
    base_temperature: float = 0.4
    current_temperature: float = 0.4
    semantic_clusters: List[np.ndarray] = field(default_factory=list)

class IntrinsicDriveMonitor:
    """Quantifies Shannon Entropy of Thought H(W) to break reasoning deadlocks."""
    def __init__(self, num_clusters: int = 6, temp_tau: float = 0.25):
        self.num_clusters = num_clusters
        self.tau = temp_tau

    def compute_entropy_and_regulate(
        self, winning_vec: np.ndarray, state: GlobalWorkspaceState
    ) -> float:
        norm_vec = winning_vec / (np.linalg.norm(winning_vec) + 1e-9)
        if len(state.semantic_clusters) < self.num_clusters:
            state.semantic_clusters.append(norm_vec)
            return 1.0  # Warmup phase

        distances = np.array([
            1.0 - float(np.dot(norm_vec, c)) for c in state.semantic_clusters
        ])
        
        logits = -distances / self.tau
        logits -= np.max(logits)
        exp_logits = np.exp(logits)
        probs = exp_logits / (np.sum(exp_logits) + 1e-12)

        entropy = -float(np.sum(probs * np.log(probs + 1e-12)))
        max_entropy = math.log(self.num_clusters)
        normalized_entropy = entropy / max_entropy

        closest_idx = int(np.argmin(distances))
        c_updated = 0.85 * state.semantic_clusters[closest_idx] + 0.15 * norm_vec
        state.semantic_clusters[closest_idx] = c_updated / (np.linalg.norm(c_updated) + 1e-9)

        if normalized_entropy < 0.35:
            state.current_temperature = min(1.1, state.base_temperature + 0.45)
        else:
            state.current_temperature = state.base_temperature

        return normalized_entropy

class HASSUMUncertaintyGate:
    """Evaluates Semantic Density and Semantic Entropy across candidate thoughts."""
    @staticmethod
    def evaluate_samples(embeddings: List[np.ndarray]) -> Dict[str, Any]:
        if len(embeddings) < 2:
            return {"semantic_density": 1.0, "semantic_entropy": 0.0, "pass": True}
        normed = [e / (np.linalg.norm(e) + 1e-9) for e in embeddings]
        sim_matrix = np.inner(normed, normed)
        upper_tri = sim_matrix[np.triu_indices(len(normed), k=1)]
        
        semantic_density = float(np.mean(upper_tri))
        
        eigvals = np.linalg.eigvalsh(sim_matrix) / len(normed)
        eigvals = np.clip(eigvals, 1e-12, 1.0)
        semantic_entropy = -float(np.sum(eigvals * np.log(eigvals))) / math.log(len(normed))

        passed = (semantic_density >= 0.68) and (semantic_entropy <= 0.42)
        return {
            "semantic_density": round(semantic_density, 3),
            "semantic_entropy": round(semantic_entropy, 3),
            "pass": passed
        }

class GWACognitiveTickEngine:
    """Executes the 4-phase synchronized Global Workspace Cognitive Tick."""
    def __init__(
        self,
        llm_client,
        memory_substrate,
        working_memory,
        skill_engine,
        policy_gate,
        somatosensory: Optional[SystemSomatosensory] = None
    ):
        self.llm = llm_client
        self.memory = memory_substrate
        self.wm = working_memory
        self.skills = skill_engine
        self.policy = policy_gate
        self.somato = somatosensory or SystemSomatosensory()
        self.state = GlobalWorkspaceState()
        self.drive = IntrinsicDriveMonitor()

    async def run_cognitive_tick(
        self,
        external_input: Optional[str] = None,
        human_approval: bool = False
    ) -> TickResult:
        self.state.tick_id += 1
        
        # PHASE 1: PERCEIVE & RETRIEVE (Attention Spotlight)
        rag_queries = await self.llm.generate_attention_queries(
            stm=self.state.stm_buffer[-5:], external_input=external_input
        )
        rag_context = await self.memory.retrieve_hybrid_context(rag_queries)
        
        # Invariant State Injection: S_t = STM_t U INPUT_t U RAG_t U P_Self
        global_state_prompt = self._compile_global_state(external_input, rag_context)

        # Dual-Process Check: Try System 1 Fast Path first if input matches routine reflex
        sys1_decision = await self.llm.evaluate_system1_fastpath(global_state_prompt)
        if sys1_decision["confidence"] >= 0.85 and sys1_decision["action"]:
            action_result, hold_card = await self._execute_governed_action(
                sys1_decision["action"], human_approval=human_approval
            )
            trace_str = f"[Tick {self.state.tick_id} | Sys1 Fast-Path] I reflexively executed: {sys1_decision['action']}"
            self.state.stm_buffer.append(trace_str)
            self.wm.core_memory_append("scratchpad_stm", trace_str)
            
            articulation = await self.llm.generate_articulation(
                global_state_prompt=global_state_prompt,
                winning_thought=None,
                action_result=action_result,
                external_input=external_input
            )
            return TickResult(
                transition="[RESPONSE]",
                tick_id=self.state.tick_id,
                action_executed=sys1_decision["action"],
                action_result=action_result,
                user_response=articulation,
                hold_card=hold_card,
                temperature=self.state.current_temperature
            )

        # PHASE 2: THINK (System 2 Divergent Generator + Convergent Critic Swarm)
        candidates = await self.llm.generate_candidate_thoughts(
            global_state_prompt, n=3, temperature=self.state.current_temperature
        )
        candidate_vecs = [await self.llm.embed(c.thought_text) for c in candidates]
        
        # HASSUM Metacognitive Uncertainty Checkpoint
        uq = HASSUMUncertaintyGate.evaluate_samples(candidate_vecs)
        candidates = await self.llm.critique_candidates(global_state_prompt, candidates)

        # PHASE 3: ARBITRATE (Metacognitive Executive)
        winning_thought, tag, rationale = await self.llm.arbitrate_winner(
            global_state_prompt, candidates, uq_metrics=uq
        )
        
        winner_idx = min(winning_thought.id, len(candidate_vecs) - 1)
        winner_vec = candidate_vecs[winner_idx]
        h_w = self.drive.compute_entropy_and_regulate(winner_vec, self.state)

        # PHASE 4: UPDATE & ARTICULATE
        trace_str = (
            f"[Tick {self.state.tick_id} | H(W)={h_w:.2f} | UQ_Pass={uq['pass']}] "
            f"I thought: {winning_thought.thought_text} (Rationale: {rationale})"
        )
        self.state.stm_buffer.append(trace_str)
        self.wm.core_memory_append("scratchpad_stm", trace_str)
        
        # Execute action if approved or proposed
        action_result = None
        hold_card = None
        if tag == "[RESPONSE]" and winning_thought.proposed_action:
            action_result, hold_card = await self._execute_governed_action(
                winning_thought.proposed_action, human_approval=human_approval
            )

        # Log episode to Tier 1 SQLite
        self.memory.record_raw_episode(
            event_type="cognitive_tick",
            tick_id=self.state.tick_id,
            input_payload=external_input or "heartbeat",
            thought_trace=trace_str,
            action_taken=str(winning_thought.proposed_action),
            outcome=tag
        )

        await self._check_stm_compression()

        # Articulate user-facing response via Response Node
        user_response = await self.llm.generate_articulation(
            global_state_prompt=global_state_prompt,
            winning_thought=winning_thought,
            action_result=action_result,
            external_input=external_input
        )

        return TickResult(
            transition=tag,
            tick_id=self.state.tick_id,
            winning_thought=winning_thought,
            action_executed=winning_thought.proposed_action,
            action_result=action_result,
            user_response=user_response,
            entropy=h_w,
            temperature=self.state.current_temperature,
            uncertainty=uq,
            hold_card=hold_card,
            candidates=candidates
        )

    def _compile_global_state(self, ext_input: Optional[str], rag_ctx: str) -> str:
        blocks = self.wm.compile()
        stm_text = "\n".join(self.state.stm_buffer[-10:])
        somato_str = self.somato.get_summary_snapshot()
        return (
            f"<core_self>\n{self.state.p_self}\n</core_self>\n"
            f"<memory_blocks>\n{blocks}\n</memory_blocks>\n"
            f"<retrieved_ltm>\n{rag_ctx}\n</retrieved_ltm>\n"
            f"<working_stage_stm>\n{stm_text}\n</working_stage_stm>\n"
            f"<hardware_somatosensory>\n{somato_str}\n</hardware_somatosensory>\n"
            f"<current_perception>\n{ext_input or 'Internal heartbeat wake-up.'}\n</current_perception>"
        )

    async def _check_stm_compression(self):
        approx_tokens = sum(len(x) // 4 for x in self.state.stm_buffer)
        if approx_tokens > self.state.stm_token_limit:
            verbose_history = "\n".join(self.state.stm_buffer[:-3])
            await self.memory.extract_and_store_engrams(verbose_history)
            dense_summary = await self.llm.summarize_stm(verbose_history)
            self.state.stm_buffer = [f"[Compressed Prior STM]: {dense_summary}"] + self.state.stm_buffer[-3:]
            self.wm.memory_rethink("scratchpad_stm", f"[Compressed Context]: {dense_summary}")

    async def _execute_governed_action(
        self, action: Dict[str, Any], human_approval: bool = False
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Evaluates policy and executes action if ALLOW, or returns hold_card if ESCALATE."""
        verdict = self.policy.evaluate(
            action, {"checkpoint_active": True, "human_approval": human_approval}
        )
        if verdict.status.value == "ESCALATE":
            return None, verdict.serialized_hold_card

        if verdict.status.value == "DENY":
            return {"status": "DENIED", "reason": verdict.reason}, None

        # ALLOW: Execute concrete OS/repo action
        action_type = action.get("action", "")
        resource = action.get("resource", "")

        try:
            if action_type == "get_telemetry":
                telem = self.somato.get_hardware_telemetry()
                return {"action": "get_telemetry", "telemetry": telem, "status": "SUCCESS"}, None

            elif action_type == "get_gpu":
                gpu = self.somato.get_hardware_telemetry()["gpu"]
                return {"action": "get_gpu", "gpu": gpu, "status": "SUCCESS"}, None

            elif action_type == "get_cpu":
                cpu = self.somato.get_hardware_telemetry()["cpu"]
                return {"action": "get_cpu", "cpu": cpu, "status": "SUCCESS"}, None

            elif action_type == "get_ram":
                ram = self.somato.get_hardware_telemetry()["ram"]
                return {"action": "get_ram", "ram": ram, "status": "SUCCESS"}, None

            elif action_type == "get_battery":
                batt = self.somato.get_hardware_telemetry()["battery"]
                return {"action": "get_battery", "battery": batt, "status": "SUCCESS"}, None

            elif action_type == "get_processes":
                procs = self.somato.get_processes(top_n=action.get("top_n", 8))
                return {"action": "get_processes", "processes": procs, "status": "SUCCESS"}, None

            elif action_type == "find_process":
                q = action.get("query") or resource or ""
                matches = self.somato.find_process(q)
                return {"action": "find_process", "query": q, "matches": matches, "status": "SUCCESS"}, None

            elif action_type == "command_run":
                cmd = action.get("command") or resource
                res = self.somato.run_command(cmd)
                return {"action": "command_run", "command": cmd, "stdout": res["stdout"], "stderr": res["stderr"], "exit_code": res["exit_code"], "status": res["status"]}, None

            elif action_type == "git_status":
                proc = subprocess.run(["git", "status", "-s"], capture_output=True, text=True)
                return {"action": "git_status", "stdout": proc.stdout or "Working tree clean.", "status": "SUCCESS"}, None

            elif action_type == "directory_list":
                target = resource
                if target in ["desktop", "Desktop"]:
                    target = str(self.somato.desktop_dir)
                elif target in ["downloads", "Downloads"]:
                    target = str(self.somato.downloads_dir)
                items = self.somato.list_directory(target or ".")
                return {"action": "directory_list", "target": target, "items": items[:25], "count": len(items), "status": "SUCCESS"}, None

            elif action_type == "file_read":
                res = self.somato.read_file_content(resource)
                return {"action": "file_read", "path": resource, "preview": res.get("content", "")[:500], "total_lines": res.get("total_lines", 0), "status": res.get("status", "SUCCESS")}, None

            elif self.skills:
                skill_res = await self.skills.execute_or_synthesize(action)
                return skill_res, None

        except Exception as e:
            return {"status": "EXECUTION_EXCEPTION", "error": str(e)}, None

        return {"status": "NOOP"}, None
