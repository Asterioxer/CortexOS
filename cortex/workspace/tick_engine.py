import asyncio
import json
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple
import numpy as np

TransitionTag = Literal["[THINK_MORE]", "[RESPONSE]", "[NO_OP]"]

@dataclass
class GlobalWorkspaceState:
    tick_id: int = 0
    # Invariant Core Self injected at every tick to prevent semantic drift
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
    # Dynamic semantic cluster centers for Intrinsic Drive H(W) calculation
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

        # Cosine distance d_{t,k} = 1 - (h_t . C_k) / (||h_t|| ||C_k||)
        distances = np.array([
            1.0 - float(np.dot(norm_vec, c)) for c in state.semantic_clusters
        ])
        
        # Softmax probability distribution across clusters
        logits = -distances / self.tau
        logits -= np.max(logits)
        exp_logits = np.exp(logits)
        probs = exp_logits / (np.sum(exp_logits) + 1e-12)

        # Shannon Information Entropy: H(W) = - sum p(x_k) log p(x_k)
        entropy = -float(np.sum(probs * np.log(probs + 1e-12)))
        max_entropy = math.log(self.num_clusters)
        normalized_entropy = entropy / max_entropy

        # Update closest cluster centroid via exponential moving average
        closest_idx = int(np.argmin(distances))
        c_updated = 0.85 * state.semantic_clusters[closest_idx] + 0.15 * norm_vec
        state.semantic_clusters[closest_idx] = c_updated / (np.linalg.norm(c_updated) + 1e-9)

        # Dynamic temperature regulation: boost temperature if entropy drops (stagnation)
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
        
        # Semantic Density: mean pairwise cosine similarity in embedding space
        semantic_density = float(np.mean(upper_tri))
        
        # Approximate Semantic Entropy via eigenvalue dispersion of similarity kernel
        eigvals = np.linalg.eigvalsh(sim_matrix) / len(normed)
        eigvals = np.clip(eigvals, 1e-12, 1.0)
        semantic_entropy = -float(np.sum(eigvals * np.log(eigvals))) / math.log(len(normed))

        # Gate passes only if responses are tightly clustered (high density) and non-competing (low entropy)
        passed = (semantic_density >= 0.68) and (semantic_entropy <= 0.42)
        return {
            "semantic_density": round(semantic_density, 3),
            "semantic_entropy": round(semantic_entropy, 3),
            "pass": passed
        }

class GWACognitiveTickEngine:
    """Executes the 4-phase synchronized Global Workspace Cognitive Tick."""
    def __init__(self, llm_client, memory_substrate, working_memory, skill_engine, policy_gate):
        self.llm = llm_client
        self.memory = memory_substrate
        self.wm = working_memory
        self.skills = skill_engine
        self.policy = policy_gate
        self.state = GlobalWorkspaceState()
        self.drive = IntrinsicDriveMonitor()

    async def run_cognitive_tick(self, external_input: Optional[str] = None) -> TransitionTag:
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
            await self._execute_governed_action(sys1_decision["action"])
            self.state.stm_buffer.append(
                f"[Tick {self.state.tick_id} | Sys1 Fast-Path] I reflexively executed: {sys1_decision['action']}"
            )
            return "[RESPONSE]"

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
        
        # Update Intrinsic Drive H(W) using winning thought embedding
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

        if tag == "[RESPONSE]" and winning_thought.proposed_action:
            await self._execute_governed_action(winning_thought.proposed_action)

        return tag

    def _compile_global_state(self, ext_input: Optional[str], rag_ctx: str) -> str:
        blocks = self.wm.compile()
        stm_text = "\n".join(self.state.stm_buffer[-10:])
        return (
            f"<core_self>\n{self.state.p_self}\n</core_self>\n"
            f"<memory_blocks>\n{blocks}\n</memory_blocks>\n"
            f"<retrieved_ltm>\n{rag_ctx}\n</retrieved_ltm>\n"
            f"<working_stage_stm>\n{stm_text}\n</working_stage_stm>\n"
            f"<current_perception>\n{ext_input or 'Internal heartbeat wake-up.'}\n</current_perception>"
        )

    async def _check_stm_compression(self):
        """Dual-Layer Memory Bifurcation when STM exceeds threshold theta."""
        approx_tokens = sum(len(x) // 4 for x in self.state.stm_buffer)
        if approx_tokens > self.state.stm_token_limit:
            verbose_history = "\n".join(self.state.stm_buffer[:-3])
            # 1. Epistemic Embedding into LTM
            await self.memory.extract_and_store_engrams(verbose_history)
            # 2. Semantic Summarization overwriting STM
            dense_summary = await self.llm.summarize_stm(verbose_history)
            self.state.stm_buffer = [f"[Compressed Prior STM]: {dense_summary}"] + self.state.stm_buffer[-3:]
            self.wm.memory_rethink("scratchpad_stm", f"[Compressed Context]: {dense_summary}")

    async def _execute_governed_action(self, action: Dict[str, Any]):
        verdict = self.policy.evaluate(action, {"checkpoint_active": True})
        if verdict.status.value == "ALLOW":
            if self.skills:
                await self.skills.execute_or_synthesize(action)
        elif verdict.status.value == "ESCALATE":
            await self.policy.hold_for_human_approval(action, self.state)
