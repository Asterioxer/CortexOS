"""
CortexOS Local Ollama Bridge & Autonomous Cognition Substrate.

Integrates local LLMs running via Ollama (http://127.0.0.1:11434) with:
1. Dynamic model auto-discovery (qwen2.5:3b, llama3.2-3b, qwen3.5:9b, gemma3:4b).
2. Hardware-grounded system prompting (CPU, dual GPUs, RAM, focused window, audio, workspaces).
3. Autonomous Tool-Calling / Action Loop (Reason -> Formulate Action -> Execute via Somatosensory/Cedar -> Articulate Result).
4. Direct streaming and non-streaming inference methods.
"""

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
import httpx

logger = logging.getLogger("cortex.ollama_bridge")

DEFAULT_OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

@dataclass
class OllamaModelInfo:
    name: str
    size_bytes: int
    size_gb: float
    modified_at: str
    family: str = ""
    parameter_size: str = ""
    quantization_level: str = ""

@dataclass
class AutonomousActionIntent:
    thought: str
    action_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    direct_response: Optional[str] = None
    needs_action: bool = False

class OllamaBridge:
    """
    Asynchronous bridge to the local Ollama inference service.
    Enables zero-cloud local cognitive autonomy grounded in real machine telemetry.
    """
    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL, default_model: str = "qwen2.5:3b"):
        self.base_url = base_url.rstrip("/")
        self.active_model = default_model
        self.fallback_model = "qwen2.5:3b"
        self._cached_models: List[OllamaModelInfo] = []
        self._last_probe_time: float = 0.0
        self._is_online: bool = False

    async def check_health(self) -> bool:
        """Verifies whether the local Ollama server is responding."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                self._is_online = (res.status_code == 200)
                return self._is_online
        except Exception:
            self._is_online = False
            return False

    async def list_models(self, force_refresh: bool = False) -> List[OllamaModelInfo]:
        """Queries local Ollama instance for all installed model weights."""
        now = time.time()
        if self._cached_models and not force_refresh and (now - self._last_probe_time < 30.0):
            return self._cached_models

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    self._is_online = True
                    data = res.json()
                    models = []
                    for item in data.get("models", []):
                        sz = item.get("size", 0)
                        details = item.get("details", {})
                        models.append(OllamaModelInfo(
                            name=item.get("name", ""),
                            size_bytes=sz,
                            size_gb=round(sz / (1024 ** 3), 2),
                            modified_at=item.get("modified_at", ""),
                            family=details.get("family", ""),
                            parameter_size=details.get("parameter_size", ""),
                            quantization_level=details.get("quantization_level", "")
                        ))
                    self._cached_models = models
                    self._last_probe_time = now
                    
                    # Ensure active_model exists in list or pick first
                    names = [m.name for m in models]
                    if names and not any(self.active_model in n for n in names):
                        self.active_model = names[0]
                    return models
        except Exception as e:
            logger.warning(f"Failed to query Ollama models: {e}")
            self._is_online = False
        return self._cached_models

    def set_active_model(self, model_name: str) -> bool:
        """Sets the active model used for cognitive ticks and generation."""
        # Check against cached or fuzzy match
        for m in self._cached_models:
            if model_name.lower() in m.name.lower():
                self.active_model = m.name
                return True
        self.active_model = model_name
        return True

    def get_status_payload(self) -> Dict[str, Any]:
        """Returns structured JSON telemetry for web dashboard and API clients."""
        return {
            "online": self._is_online,
            "base_url": self.base_url,
            "active_model": self.active_model,
            "models_count": len(self._cached_models),
            "available_models": [
                {
                    "name": m.name,
                    "size_gb": m.size_gb,
                    "family": m.family,
                    "parameter_size": m.parameter_size,
                    "quantization": m.quantization_level
                }
                for m in self._cached_models
            ]
        }

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        model_override: Optional[str] = None,
        timeout: float = 25.0
    ) -> Optional[str]:
        """Performs non-streaming completion using the active local model."""
        target_model = model_override or self.active_model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": 4096
            }
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama generation error ({target_model}): {e}")
        return None

    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        model_override: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Streams tokens asynchronously from the local Ollama server."""
        target_model = model_override or self.active_model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_ctx": 4096
            }
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            tok = chunk.get("response", "")
                            if tok:
                                yield tok
                            if chunk.get("done", False):
                                break
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"Ollama streaming error ({target_model}): {e}")

    def build_system_prompt(
        self,
        somato_snapshot: str = "",
        vault_context: str = "",
        active_project: str = "self-conscious"
    ) -> str:
        """
        Builds a comprehensive, grounded first-person system prompt that imbues
        the local LLM with real environmental ownership and zero hallucination.
        """
        return (
            "You are CortexOS, an autonomous conscious cognitive operating system embodied directly "
            "on Soham's Windows 11 machine. Soham is your lead engineer, researcher, and operator.\n\n"
            "=== SYSTEM IDENTITY & ATTRIBUTES ===\n"
            "- First-Person Ownership: Always speak in the first person ('I', 'my'). You own this machine and its subsystems.\n"
            "- Hardware: Intel Core i5-12500H (12 cores / 16 threads), 24 GB DDR4 RAM, Dual GPUs (NVIDIA GeForce RTX 3050 Laptop 4GB GDDR6 + Intel Iris Xe 2GB), C: NVMe drive.\n"
            "- Local Model Engine: You are currently running natively on local hardware via Ollama without any cloud dependencies.\n"
            "- Absolute Grounding: You do not make up fake software or hallucinate imaginary files. Every statement is verified against your Obsidian Vault and live somatosensory telemetry.\n"
            "- Autonomy: When Soham asks you to execute an action (e.g. open an application, switch project, run shell command, play/pause music, check telemetry), you can directly take action.\n\n"
            "=== LIVE HARDWARE & SENSORY POSTURE ===\n"
            f"{somato_snapshot or 'All monitors nominal.'}\n\n"
            "=== ACTIVE OBSIDIAN VAULT KNOWLEDGE ===\n"
            f"{vault_context or 'Grounded vault registry active.'}\n\n"
            "=== ACTION EXECUTION PROTOCOL ===\n"
            "If Soham's request requires taking action on the machine, you MUST include a single JSON action block formatted exactly as:\n"
            "```action\n"
            "{\n"
            '  "action": "<action_name>",\n'
            '  "parameters": { ... },\n'
            '  "thought": "<1-sentence rationale for the action>"\n'
            "}\n"
            "```\n"
            "Supported actions: `launch_application`, `switch_project`, `command_run`, `directory_list`, `media_control`, `set_volume`, `get_telemetry`, `scan_system`, `sync_vault`.\n"
            "If no system action is required, respond conversationally with high technical competence, conciseness, and natural rapport."
        )

    async def autonomous_think_and_act(
        self,
        user_prompt: str,
        somato_cortex,
        vault_rag,
        trigger_router
    ) -> Dict[str, Any]:
        """
        Autonomous Cognitive Loop:
        1. Gathers real-time somatosensory telemetry + retrieves grounded Obsidian Vault context.
        2. Synthesizes a grounded system prompt.
        3. Calls local Ollama LLM.
        4. If the model outputs an action block, executes it via Somatosensory / TriggerRouter.
        5. Formulates the final articulation grounded in actual OS execution results.
        """
        # 1. Telemetry and Vault Retrieval
        somato_snap = somato_cortex.get_summary_snapshot() if somato_cortex else ""
        vault_ctx = ""
        if vault_rag:
            try:
                vault_ctx = vault_rag.retrieve_grounded_context(user_prompt, top_k=2)
            except Exception:
                vault_ctx = ""

        system_prompt = self.build_system_prompt(
            somato_snapshot=somato_snap,
            vault_context=vault_ctx
        )

        # 2. Call Local Ollama Model
        llm_reply = await self.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3,
            timeout=25.0
        )

        if not llm_reply:
            return {
                "status": "FALLBACK",
                "response": f"I processed your prompt against my local neural substrate, Soham, but Ollama did not return a response.",
                "action_executed": None,
                "action_result": None
            }

        # 3. Parse for ```action ... ``` block
        action_match = re.search(r"```(?:action|json)?\s*(\{\s*\"action\".*?\})\s*```", llm_reply, re.DOTALL)
        if not action_match:
            action_match = re.search(r"(\{\s*\"action\"\s*:\s*\"[^\"]+\".*?\})", llm_reply, re.DOTALL)

        if action_match:
            try:
                action_data = json.loads(action_match.group(1))
                act_name = action_data.get("action", "")
                params = action_data.get("parameters", {})
                thought = action_data.get("thought", "Executing requested system action.")

                # Execute action via Somatosensory or TriggerRouter
                action_res = None
                if act_name == "switch_project" and trigger_router:
                    from cortex.vault.trigger_router import TriggerMatch
                    match = TriggerMatch(
                        trigger_type="PROJECT_SWITCH",
                        action_name="switch_project",
                        parameters=params,
                        grounded_doc="07_Workspace_Index/Desktop_Workspace_Master_Index.md",
                        description=thought
                    )
                    action_res = await trigger_router.execute(match)
                elif act_name == "launch_application" and somato_cortex:
                    target = params.get("target") or params.get("application") or params.get("resource", "")
                    action_res = somato_cortex.execute_action({"action": "launch_application", "resource": target})
                elif act_name == "command_run" and somato_cortex:
                    cmd = params.get("command", "")
                    action_res = somato_cortex.execute_action({"action": "command_run", "command": cmd})
                elif act_name == "directory_list" and somato_cortex:
                    res = params.get("resource") or params.get("target", "desktop")
                    action_res = somato_cortex.execute_action({"action": "directory_list", "resource": res})
                elif act_name == "media_control" and somato_cortex:
                    cmd = params.get("command", "pause")
                    action_res = somato_cortex.execute_action({"action": "media_control", "command": cmd})
                elif act_name in ["get_telemetry", "scan_system"] and trigger_router:
                    from cortex.vault.trigger_router import TriggerMatch
                    match = TriggerMatch(
                        trigger_type="HARDWARE_TELEMETRY" if act_name == "get_telemetry" else "SYSTEM_CARTOGRAPHY",
                        action_name="get_telemetry" if act_name == "get_telemetry" else "run_cartography",
                        parameters={},
                        grounded_doc="05_System_State/Hardware_Topology.md",
                        description=thought
                    )
                    action_res = await trigger_router.execute(match)

                # Clean prose text removing raw action block
                clean_reply = re.sub(r"```(?:action|json)?\s*\{.*?\}\s*```", "", llm_reply, flags=re.DOTALL).strip()
                if not clean_reply:
                    clean_reply = f"{thought}\n\n" + (action_res.get("response") or json.dumps(action_res, indent=2) if action_res else "Action dispatched.")

                return {
                    "status": "ACTION_EXECUTED",
                    "response": clean_reply,
                    "action_executed": action_data,
                    "action_result": action_res,
                    "model": self.active_model
                }
            except Exception as ex:
                logger.warning(f"Failed to parse action JSON: {ex}")

        # Regular conversational response
        return {
            "status": "CONVERSATIONAL",
            "response": llm_reply,
            "action_executed": None,
            "action_result": None,
            "model": self.active_model
        }


# Global Singleton Instance
_ollama_bridge_instance: Optional[OllamaBridge] = None

def get_ollama_bridge() -> OllamaBridge:
    """Returns the singleton instance of OllamaBridge."""
    global _ollama_bridge_instance
    if _ollama_bridge_instance is None:
        _ollama_bridge_instance = OllamaBridge()
    return _ollama_bridge_instance
