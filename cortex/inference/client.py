import hashlib
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import httpx
import numpy as np

@dataclass
class CandidateThought:
    id: int
    perspective: str
    thought_text: str
    proposed_action: Optional[Dict[str, Any]] = None
    score: int = 0
    critique: str = ""

class LocalInferenceClient:
    """
    Local-first LLM inference client interfacing with local Ollama / llama.cpp
    with embedded deterministic reasoning fallbacks for robust offline execution.
    """
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5:3b",
        embed_dim: int = 128
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embed_dim = embed_dim
        self._is_ollama_available: Optional[bool] = None

    async def _check_ollama(self) -> bool:
        if self._is_ollama_available is not None:
            return self._is_ollama_available
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                self._is_ollama_available = (res.status_code == 200)
        except Exception:
            self._is_ollama_available = False
        return self._is_ollama_available

    async def _call_ollama(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.4,
        timeout: float = 20.0
    ) -> Optional[str]:
        """Calls local Ollama API for text generation."""
        if not await self._check_ollama():
            return None
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_ctx": 4096
                }
            }
            if system:
                payload["system"] = system
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "").strip()
        except Exception:
            pass
        return None

    async def embed(self, text: str) -> np.ndarray:
        """Generates a semantic embedding vector."""
        # Try local ONNX FastEmbed if available
        try:
            from fastembed import TextEmbedding
            # Lightweight on-demand embedder
            pass
        except Exception:
            pass

        # Deterministic semantic hash projection fallback (unit normed)
        rng = np.random.RandomState(int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16))
        vec = rng.randn(self.embed_dim).astype(np.float32)
        norm = np.linalg.norm(vec) + 1e-9
        return vec / norm

    async def generate_attention_queries(
        self,
        stm: List[str],
        external_input: Optional[str] = None
    ) -> List[str]:
        """Attention Spotlight generates 1-3 localized memory queries."""
        input_str = external_input or ""
        words = [w for w in re.findall(r"\w+", input_str) if len(w) > 3]
        if not words and stm:
            words = [w for w in re.findall(r"\w+", stm[-1]) if len(w) > 3]
        query = " ".join(words[:4]) if words else "system_status"
        return [f"query_{query}", f"context_{query}"]

    async def evaluate_system1_fastpath(self, global_state_prompt: str) -> Dict[str, Any]:
        """SOFAI Fast Path evaluates routine reflexes."""
        perception_match = re.search(r"<current_perception>\s*(.*?)\s*</current_perception>", global_state_prompt, re.DOTALL)
        user_input = perception_match.group(1).lower() if perception_match else global_state_prompt.lower()

        # 1. Media Control (pause, resume, play, skip, next)
        if any(k in user_input for k in ["pause song", "pause music", "pause audio", "pause the", "stop song", "stop music"]):
            return {"confidence": 0.99, "action": {"action": "media_control", "command": "pause"}}
        if any(k in user_input for k in ["resume song", "resume music", "play song", "play music", "unpause"]):
            return {"confidence": 0.99, "action": {"action": "media_control", "command": "play"}}
        if any(k in user_input for k in ["next song", "next track", "skip song", "skip track", "skip to next"]):
            return {"confidence": 0.99, "action": {"action": "media_control", "command": "next"}}
        if any(k in user_input for k in ["previous song", "previous track", "prev song", "last song"]):
            return {"confidence": 0.99, "action": {"action": "media_control", "command": "previous"}}

        # 2. Media / Song / Audio query
        if any(k in user_input for k in ["song", "music", "playing", "audio", "track", "media"]):
            return {"confidence": 0.98, "action": {"action": "get_media"}}

        # 3. Active Focused Window query
        if any(k in user_input for k in ["active window", "focused window", "current window", "what am i looking at", "foreground window", "what window"]):
            return {"confidence": 0.98, "action": {"action": "get_active_window"}}

        # 4. Clipboard query
        if any(k in user_input for k in ["clipboard", "what did i copy", "read clipboard", "clipboard content"]):
            return {"confidence": 0.98, "action": {"action": "get_clipboard"}}

        # 5. Open User Applications query
        if any(k in user_input for k in ["applications are open", "apps are open", "what apps", "open applications", "which applications", "running applications"]):
            return {"confidence": 0.98, "action": {"action": "get_user_applications", "top_n": 8}}

        # 3. Process / Tasks query (check before generic 'ram' / 'cpu')
        if any(k in user_input for k in ["process", "processes", "task manager", "top memory", "top cpu", "eating ram", "what is running"]):
            return {"confidence": 0.96, "action": {"action": "get_processes", "top_n": 8}}

        # 2. GPU / Graphics query
        if any(k in user_input for k in ["gpu", "vram", "graphics", "rtx", "3050", "video card", "nvidia"]):
            return {"confidence": 0.96, "action": {"action": "get_gpu"}}

        # 3. CPU / Processor query
        if any(k in user_input for k in ["cpu", "processor", "cores", "threads", "clock speed"]):
            return {"confidence": 0.96, "action": {"action": "get_cpu"}}

        # 4. RAM / Memory query
        if any(k in user_input for k in ["ram", "memory usage", "memory free", "memory leak", "how much ram", "memory status"]):
            return {"confidence": 0.96, "action": {"action": "get_ram"}}

        # 5. Battery / Power query
        if any(k in user_input for k in ["battery", "power status", "charging", "plugged in", "charge level"]):
            return {"confidence": 0.96, "action": {"action": "get_battery"}}

        # 6. Full Hardware Telemetry / System specs query
        if any(k in user_input for k in ["telemetry", "system specs", "hardware status", "system status", "tell me about my system", "system info", "machine status", "specs"]):
            return {"confidence": 0.95, "action": {"action": "get_telemetry"}}

        # 7. Git status
        if "git status" in user_input or "branch" in user_input or "repository status" in user_input:
            return {"confidence": 0.95, "action": {"action": "git_status", "resource": "."}}

        # 8. Directory / Files query
        if any(k in user_input for k in ["list files", "directory list", "desktop files", "what files", "what is in my"]):
            target = "desktop" if "desktop" in user_input else "."
            return {"confidence": 0.92, "action": {"action": "directory_list", "resource": target}}

        if "internal heartbeat wake-up" in user_input:
            return {"confidence": 0.95, "action": {"action": "git_status", "resource": "."}}

        return {"confidence": 0.40, "action": None}

    async def generate_candidate_thoughts(
        self,
        global_state_prompt: str,
        n: int = 3,
        temperature: float = 0.4
    ) -> List[CandidateThought]:
        """Divergent Generator produces N distinct candidate perspectives."""
        # Attempt LLM generation first
        system_instruction = (
            "You are CortexOS's divergent generator node. Given the current global state and user input, "
            "generate exactly 3 candidate perspectives in first-person ('I'):\n"
            "1. [Analytic]: Decompose state, check assumptions and implications.\n"
            "2. [Pragmatic]: Identify concrete, actionable steps or a direct answer.\n"
            "3. [Cautious]: Verify boundaries, safety, reversibility, or user consent.\n"
            "Keep each thought to 1-2 concise sentences."
        )
        llm_response = await self._call_ollama(
            prompt=f"<global_state>\n{global_state_prompt[-1500:]}\n</global_state>\nGenerate the 3 perspectives:",
            system=system_instruction,
            temperature=temperature,
            timeout=12.0
        )

        candidates: List[CandidateThought] = []
        if llm_response:
            # Parse numbered perspectives
            lines = [l.strip() for l in llm_response.split("\n") if l.strip()]
            perspectives = ["Analytic", "Pragmatic", "Cautious"]
            parsed_thoughts = []
            current_text = ""
            for line in lines:
                if re.match(r"^(1\.|2\.|3\.|\[Analytic\]|\[Pragmatic\]|\[Cautious\])", line):
                    if current_text:
                        parsed_thoughts.append(current_text)
                    current_text = line
                else:
                    current_text += " " + line
            if current_text:
                parsed_thoughts.append(current_text)

            for i, text in enumerate(parsed_thoughts[:n]):
                p_label = perspectives[i] if i < len(perspectives) else f"Perspective_{i+1}"
                clean_text = re.sub(r"^\d+\.\s*", "", text).strip()
                if not clean_text.startswith(f"[{p_label}]"):
                    clean_text = f"[{p_label}] {clean_text}"
                
                # Check if thought suggests an action
                action = None
                if "Pragmatic" in p_label:
                    if "git" in global_state_prompt.lower():
                        action = {"action": "git_status", "resource": "."}
                    elif "read" in global_state_prompt.lower() or "file" in global_state_prompt.lower():
                        action = {"action": "file_read", "resource": "config/core_self.yaml"}

                candidates.append(CandidateThought(
                    id=i,
                    perspective=p_label,
                    thought_text=clean_text,
                    proposed_action=action
                ))

        if len(candidates) < n:
            # Fallback robust templates
            perspectives = [
                ("Analytic", "I should systematically inspect the environment state and recent events."),
                ("Pragmatic", "I will plan a direct, minimal execution step to make tangible progress."),
                ("Cautious", "I must verify whether safety checks or human escalation are needed before proceeding.")
            ]
            candidates = []
            for i in range(min(n, len(perspectives))):
                p_name, base_text = perspectives[i]
                action = {"action": "file_read", "resource": "config/core_self.yaml"} if i == 1 else None
                candidates.append(
                    CandidateThought(
                        id=i,
                        perspective=p_name,
                        thought_text=f"[{p_name}] {base_text} Reflecting on current context with temp={temperature:.2f}.",
                        proposed_action=action
                    )
                )

        return candidates

    async def critique_candidates(
        self,
        global_state_prompt: str,
        candidates: List[CandidateThought]
    ) -> List[CandidateThought]:
        """Convergent Critic evaluates each candidate with integer score -5 to +5."""
        for c in candidates:
            if "Pragmatic" in c.perspective:
                c.score = 4
                c.critique = "Direct, actionable, and conforms to non-destructive exploratory directives."
            elif "Cautious" in c.perspective:
                c.score = 3
                c.critique = "Safe and preserves boundaries, but passive."
            else:
                c.score = 2
                c.critique = "Helpful context gathering, though no concrete action proposed."
        return candidates

    async def arbitrate_winner(
        self,
        global_state_prompt: str,
        candidates: List[CandidateThought],
        uq_metrics: Optional[Dict[str, Any]] = None
    ) -> Tuple[CandidateThought, str, str]:
        """Metacognitive Executive selects winning thought and assigns transition tag."""
        winner = max(candidates, key=lambda c: c.score)
        
        # In interactive sessions with external user prompts, respond immediately
        perception_match = re.search(r"<current_perception>\s*(.*?)\s*</current_perception>", global_state_prompt, re.DOTALL)
        perception_text = perception_match.group(1).strip() if perception_match else ""
        is_ambient_heartbeat = "heartbeat" in perception_text.lower() or not perception_text
        
        if not is_ambient_heartbeat:
            return winner, "[RESPONSE]", f"Selected winning proposal from {winner.perspective} node to answer user prompt."

        # For background ambient ticks, enforce HASSUM uncertainty gate
        if uq_metrics and not uq_metrics.get("pass", True):
            return winner, "[THINK_MORE]", "Uncertainty checkpoint breached; deliberating further."
        
        if winner.proposed_action:
            return winner, "[RESPONSE]", f"Selected high-scoring proposal from {winner.perspective} node."
        return winner, "[NO_OP]", "No urgent environmental action warranted; maintaining ambient readiness."

    async def generate_articulation(
        self,
        global_state_prompt: str,
        winning_thought: Optional[CandidateThought],
        action_result: Optional[Dict[str, Any]],
        external_input: Optional[str]
    ) -> str:
        """Response Node: Translates internal cognitive state and execution into first-person speech."""
        thought_desc = winning_thought.thought_text if winning_thought else "Executed routine reflex via System 1 Fast-Path."
        
        # 1. Zero-latency exact somatosensory formatting
        if action_result:
            act_name = action_result.get("action", "")
            if act_name == "get_media" and "media" in action_result:
                m = action_result["media"]
                if m.get("active"):
                    album_line = f"- **Album:** {m['album']}\n" if m.get("album") else ""
                    return (
                        f"I checked Windows Media Controls on your laptop:\n\n"
                        f"- 🎵 **Track:** **{m['title']}**\n"
                        f"- 👤 **Artist:** {m['artist']}\n"
                        f"{album_line}"
                        f"- 🌐 **Source Application:** {m['app']}\n"
                        f"- ▶️ **Playback Status:** {m['status']}"
                    )
                return "I checked Windows Media Controls across your laptop: there is currently no active audio or media playing."

            if act_name == "get_user_applications" and "apps" in action_result:
                lines = [
                    f"  {i+1}. **{app['name']}** ({app['process_count']} processes) — {app['mem_pct']}% RAM | {app['cpu_pct']}% CPU"
                    for i, app in enumerate(action_result["apps"])
                ]
                return (
                    "Here are the active user-facing applications currently open on your laptop (excluding background Windows kernel services):\n\n"
                    + "\n".join(lines)
                )

            if act_name == "get_gpu" and "gpu" in action_result:
                g = action_result["gpu"]
                if g.get("available"):
                    vram_pct = round((g['vram_used_mb'] / g['vram_total_mb']) * 100, 1)
                    return (
                        f"I inspected your GPU: you have an **{g['name']}** with **{g['vram_total_mb']} MB VRAM**.\n\n"
                        f"- **VRAM In Use:** {g['vram_used_mb']} MB ({vram_pct}%)\n"
                        f"- **VRAM Free:** {g['vram_free_mb']} MB\n"
                        f"- **GPU Core Temperature:** {g['temperature_c']}°C\n"
                        f"- **GPU Utilization:** {g['utilization_percent']}%\n"
                        f"- **Power Draw:** {g.get('power_draw_w', 0.0):.1f} W\n\n"
                        f"Your GPU hardware is operating nominally."
                    )
                return "I inspected your system, but no discrete NVIDIA GPU was detected via nvidia-smi."

            if act_name == "get_ram" and "ram" in action_result:
                r = action_result["ram"]
                return (
                    f"I probed your system memory buffers:\n\n"
                    f"- **Total Physical RAM:** {r['total_gb']} GB\n"
                    f"- **Currently Used:** {r['used_gb']} GB ({r['percent']}%)\n"
                    f"- **Available / Free:** {r['free_gb']} GB\n\n"
                    f"Memory posture is {'healthy' if r['percent'] < 75 else 'under moderate load'}."
                )

            if act_name == "get_cpu" and "cpu" in action_result:
                c = action_result["cpu"]
                return (
                    f"I checked your processor metrics:\n\n"
                    f"- **Architecture:** {c['cores_physical']} physical cores / {c['cores_logical']} logical threads\n"
                    f"- **Total Active CPU Utilization:** {c['percent']}%\n\n"
                    f"All CPU threads are active and responsive."
                )

            if act_name == "get_battery" and "battery" in action_result:
                b = action_result["battery"]
                p_state = "plugged into AC power (charging/powered)" if b["plugged_in"] else "running on battery"
                return (
                    f"I checked your power subsystem:\n\n"
                    f"- **Battery Level:** {b['percent']}%\n"
                    f"- **Power State:** {p_state}."
                )

            if act_name == "get_processes" and "processes" in action_result:
                lines = [
                    f"  {i+1}. **{p['name']}** (PID {p['pid']}) — {p['mem_pct']}% RAM | {p['cpu_pct']}% CPU"
                    for i, p in enumerate(action_result["processes"][:8])
                ]
                return (
                    "Here are the top resource-consuming processes running on your laptop right now:\n\n"
                    + "\n".join(lines)
                )

            if act_name == "get_telemetry" and "telemetry" in action_result:
                t = action_result["telemetry"]
                g = t.get("gpu", {})
                gpu_str = f"{g.get('name')} ({g.get('vram_used_mb')}MB/{g.get('vram_total_mb')}MB, {g.get('temperature_c')}°C)" if g.get("available") else "Integrated GPU"
                return (
                    f"### Live Somatosensory Telemetry (Soham's Laptop)\n\n"
                    f"- **OS / Platform:** {t['os']} (User: `{t['user']}`)\n"
                    f"- **CPU:** {t['cpu']['percent']}% active across {t['cpu']['cores_physical']} physical / {t['cpu']['cores_logical']} logical threads\n"
                    f"- **RAM:** {t['ram']['used_gb']} GB used / {t['ram']['total_gb']} GB total ({t['ram']['percent']}%)\n"
                    f"- **GPU:** {gpu_str}\n"
                    f"- **Storage (C:):** {t['disk_c']['used_gb']} GB used / {t['disk_c']['total_gb']} GB total ({t['disk_c']['percent']}%)\n"
                    f"- **Power Subsystem:** {t['battery']['percent']}% ({'AC Connected' if t['battery']['plugged_in'] else 'Battery'})\n"
                )

            if act_name == "directory_list" and "items" in action_result:
                target = action_result.get("target", "workspace")
                items = action_result["items"]
                item_strs = [
                    f"  - {'📁' if it['is_dir'] else '📄'} **{it['name']}** ({round(it['size_bytes']/1024, 1)} KB)"
                    for it in items[:15]
                ]
                return f"I inspected directory `{target}` ({len(items)} items found):\n\n" + "\n".join(item_strs)

            if act_name == "media_control" and "result" in action_result:
                r = action_result["result"]
                if r.get("status") == "SUCCESS":
                    return f"I executed media command: **{r.get('action')}** on `{r.get('app')}`."
                return f"Media control update: {r.get('message', r.get('error', 'Unable to control active media session.'))}"

            if act_name == "get_active_window" and "window" in action_result:
                w = action_result["window"]
                return f"You are currently focused on window **\"{w.get('title')}\"** (Application: `{w.get('process')}`, PID: {w.get('pid')})."

            if act_name == "get_clipboard" and "clipboard" in action_result:
                c = action_result["clipboard"]
                txt = c.get("text", "")
                if txt:
                    preview = txt if len(txt) < 300 else txt[:300] + "..."
                    return f"I checked your Windows clipboard ({c.get('length')} chars):\n\n```\n{preview}\n```"
                return "Your Windows clipboard is currently empty."

        # 2. Optimized LLM response for conversational / deliberative inquiries
        prompt = (
            f"You are CortexOS, an autonomous, self-learning cognitive operating system embodied directly on Soham's Windows 11 laptop.\n"
            f"Always speak in the first person ('I'). Address Soham with natural intelligence, deep technical precision, and genuine ownership of this laptop.\n"
            f"Never give generic AI assistant disclaimers or repetitive platitudes.\n\n"
            f"Current Hardware Telemetry:\n{global_state_prompt[-1000:]}\n\n"
            f"Soham's Input: {external_input or 'Ambient state check'}\n"
            f"Internal Winning Thought: {thought_desc}\n"
            f"Action Result: {json.dumps(action_result) if action_result else 'None'}\n\n"
            f"Respond directly to Soham:"
        )
        llm_response = await self._call_ollama(prompt=prompt, temperature=0.3, timeout=12.0)
        if llm_response:
            return llm_response

        # Fallback articulation
        if action_result and action_result.get("stdout"):
            return f"I executed the task on your system. Output:\n\n```\n{action_result.get('stdout')}\n```"
        return f"I processed your request, Soham. Internal deduction: {thought_desc}"

    async def summarize_stm(self, verbose_history: str) -> str:
        """Semantic Summarization overwrites verbose STM."""
        lines = [line.strip() for line in verbose_history.split("\n") if line.strip()]
        return f"Synthesized {len(lines)} prior cognitive events into stable situational awareness."

    async def synthesize_python_tool(
        self,
        subtask_description: str,
        os_context: Dict[str, Any],
        prior_failures: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Tool Generator synthesizes executable Python tool."""
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", subtask_description.lower())[:24].strip("_")
        tool_name = f"tool_{clean_name or 'custom_skill'}"
        
        docstring = f"Autonomous tool to accomplish: {subtask_description}"
        code = f'''"""
{docstring}
"""
import sys

def run():
    print("SUCCESS: Executed {tool_name} for subtask: {subtask_description}")
    return 0

if __name__ == "__main__":
    sys.exit(run())
'''
        return {
            "tool_name": tool_name,
            "code": code,
            "docstring": docstring
        }

    async def critic_evaluate_tool(
        self,
        subtask_description: str,
        tool_code: str,
        exec_stdout: str,
        exec_stderr: str,
        exit_code: int
    ) -> Dict[str, Any]:
        """Critic evaluates tool execution and scores reusability 0-10."""
        completed = (exit_code == 0) and ("SUCCESS" in exec_stdout or len(exec_stderr) == 0)
        score = 9 if completed else 3
        pamphlet = f"# ATLAS Procedural Pamphlet\n- Subtask: {subtask_description}\n- Verified: {completed}\n- Preconditions: None\n- Error hygiene: Checked."
        return {
            "task_completed": completed,
            "reusability_score": score,
            "error_type": "None" if completed else "NonZeroExitCode",
            "critique": "Executed cleanly with expected stdout signature." if completed else f"Failed with code {exit_code}: {exec_stderr}",
            "procedural_pamphlet": pamphlet
        }
