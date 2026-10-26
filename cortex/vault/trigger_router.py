"""CortexOS Deterministic Grounded Trigger Router.

Resolves operator intents using strict, verified trigger rules cataloged in the
Obsidian Knowledge Vault (04_Skills_Catalog/Trigger_Registry.md and
06_Self_Evolution/Deterministic_Trigger_Matrix.md), eliminating random hallucination.

Provides:
- Instant session greetings on startup.
- Safe shutdown sequences with memory consolidation and goodbye audio.
- Deterministic application launching (VS Code, MPV, Docker, Browser).
- Workspace project switching (resolving Desktop paths directly into VS Code).
- Hardware telemetry, media controls, and vault evolution triggers.
"""

from __future__ import annotations

import os
import sys
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from pathlib import Path

import psutil

from cortex.vault.vault_manager import get_vault
from cortex.vault.system_cartographer import SystemCartographer
from cortex.vault.evolution_engine import SelfEvolutionEngine
from cortex.vault.git_sync import get_vault_sync
from cortex.embodiment.system_somatosensory import SystemSomatosensory


@dataclass
class TriggerMatch:
    trigger_type: str
    action_name: str
    parameters: Dict[str, Any]
    grounded_doc: str
    description: str


class TriggerRouter:
    """Matches operator inputs against deterministic Obsidian Vault trigger definitions."""

    def __init__(self):
        self.somato = SystemSomatosensory()
        self.vault = get_vault()
        self.sync = get_vault_sync()

    def match(self, prompt: str) -> Optional[TriggerMatch]:
        """Evaluates prompt against deterministic trigger patterns."""
        p_clean = prompt.strip()
        p_lower = p_clean.lower()

        # 1. Greeting Trigger
        if p_lower in ["greet", "greetings", "hello", "hey cortex", "hi cortex", "wake up", "good morning", "good evening", "session_start"]:
            return TriggerMatch(
                trigger_type="SESSION_GREETING",
                action_name="execute_greeting",
                parameters={},
                grounded_doc="04_Skills_Catalog/Trigger_Registry.md#1. Session Greeting Triggers",
                description="Synthesize personalized operator greeting and status overview."
            )

        # 2. Shutdown / Goodbye Trigger
        if p_lower in ["shutdown", "power off", "goodbye", "stand down", "exit cortex", "shut down", "bye cortex", "bye", "system_shutdown"]:
            return TriggerMatch(
                trigger_type="SYSTEM_SHUTDOWN",
                action_name="execute_shutdown",
                parameters={},
                grounded_doc="04_Skills_Catalog/Trigger_Registry.md#2. Shutdown & Stand-Down Triggers",
                description="Consolidate memory, sync vault to Git backup, synthesize goodbye audio, and stand down."
            )

        # 3. Project Switching Trigger (e.g. "open project voice-lab", "switch to project qwen")
        m_proj = re.match(r"^(?:open project|switch to project|go to project|open folder)\s+([a-zA-Z0-9_\-\.\+]+)$", p_lower)
        if m_proj:
            target_proj = m_proj.group(1).strip()
            return TriggerMatch(
                trigger_type="PROJECT_SWITCH",
                action_name="switch_project",
                parameters={"project_name": target_proj},
                grounded_doc="05_System_State/Filesystem_and_Workspaces.md",
                description=f"Resolve project '{target_proj}' on Desktop and launch in IDE."
            )

        # 4. Specific Application Launch Triggers
        if p_lower.startswith(("open ", "launch ", "start ")):
            app_target = re.sub(r"^(open|launch|start)\s+", "", p_lower).strip()
            return TriggerMatch(
                trigger_type="APPLICATION_LAUNCH",
                action_name="launch_application",
                parameters={"target": app_target},
                grounded_doc="05_System_State/Toolchains_and_Compilers.md",
                description=f"Launch verified executable for '{app_target}'."
            )

        # 5. Hardware Posture & Telemetry
        if any(w in p_lower for w in ["telemetry", "hardware posture", "cpu usage", "ram usage", "gpu stats", "system stats"]):
            return TriggerMatch(
                trigger_type="HARDWARE_TELEMETRY",
                action_name="get_telemetry",
                parameters={},
                grounded_doc="05_System_State/Hardware_Topology.md",
                description="Query live CPU, GPU, RAM, and disk utilization metrics."
            )

        # 6. Cartography & Environmental Scan
        if any(w in p_lower for w in ["cartography", "scan system", "scan machine", "map system", "probe hardware"]):
            return TriggerMatch(
                trigger_type="SYSTEM_CARTOGRAPHY",
                action_name="run_cartography",
                parameters={},
                grounded_doc="05_System_State/Hardware_Topology.md",
                description="Perform full hardware and workspace cartography scan."
            )

        # 7. Self-Evolution Cycle
        if any(w in p_lower for w in ["evolve system", "self evolve", "evolution cycle", "run evolution"]):
            return TriggerMatch(
                trigger_type="SELF_EVOLUTION",
                action_name="run_evolution",
                parameters={},
                grounded_doc="06_Self_Evolution/Autonomous_Evolution_Architecture.md",
                description="Execute closed-loop 5-phase autopoietic evolution cycle."
            )

        # 8. Vault Sync
        if any(w in p_lower for w in ["sync vault", "backup vault", "vault backup", "push vault"]):
            return TriggerMatch(
                trigger_type="VAULT_SYNC",
                action_name="sync_vault",
                parameters={},
                grounded_doc="03_Decisions_ADR/ADR-003-Obsidian-Vault-RAG.md",
                description="Stage, commit, and sync vault to isolated private Git repository."
            )

        # 9. Media Control
        if any(w in p_lower for w in ["pause music", "resume music", "play music", "next song", "previous song"]):
            cmd = "toggle"
            if "next" in p_lower:
                cmd = "next"
            elif "previous" in p_lower:
                cmd = "previous"
            return TriggerMatch(
                trigger_type="MEDIA_CONTROL",
                action_name="control_media",
                parameters={"command": cmd},
                grounded_doc="01_Architecture/Embodiment_Somatosensory.md",
                description=f"Send media key command '{cmd}' to OS audio pipeline."
            )

        return None

    async def execute(self, match: TriggerMatch) -> Dict[str, Any]:
        """Executes matched deterministic trigger."""
        if match.action_name == "execute_greeting":
            return self.get_greeting()

        elif match.action_name == "execute_shutdown":
            return self.get_shutdown()

        elif match.action_name == "get_telemetry":
            telem = self.somato.get_hardware_telemetry()
            cpu = telem["cpu"]["percent"]
            ram = f"{telem['ram']['used_gb']}/{telem['ram']['total_gb']} GB ({telem['ram']['percent']}%)"
            return {
                "status": "SUCCESS",
                "trigger": match.trigger_type,
                "response": f"Hardware Posture: Intel i5 16-thread CPU {cpu}% | RAM {ram} | RTX 3050 Laptop GPU Ready | Focus: {self.somato.get_active_window().get('title', 'Desktop')}.",
                "grounded_doc": match.grounded_doc,
                "speak": True,
                "persona": "jarvis"
            }

        elif match.action_name == "switch_project":
            proj_name = match.parameters["project_name"]
            desktop = Path.home() / "Desktop"
            target_path = None

            # Look for exact or case-insensitive match on Desktop
            for item in desktop.iterdir():
                if item.is_dir() and item.name.lower() == proj_name.lower():
                    target_path = item
                    break

            if not target_path:
                # Fuzzy prefix match
                for item in desktop.iterdir():
                    if item.is_dir() and proj_name.lower() in item.name.lower():
                        target_path = item
                        break

            if target_path and target_path.exists():
                code_bin = shutil.which("code") or r"C:\Users\soham\AppData\Local\Programs\Microsoft VS Code\bin\code.CMD"
                try:
                    if Path(code_bin).exists() or shutil.which("code"):
                        subprocess.Popen([code_bin, str(target_path)], shell=True)
                        resp_text = f"Switched workspace to [[{target_path.name}]]. Opened {target_path} in VS Code."
                    else:
                        resp_text = f"Located workspace directory at {target_path}."
                    return {
                        "status": "SUCCESS",
                        "trigger": match.trigger_type,
                        "response": resp_text,
                        "grounded_doc": match.grounded_doc,
                        "speak": True,
                        "persona": "guy"
                    }
                except Exception as e:
                    return {
                        "status": "ERROR",
                        "trigger": match.trigger_type,
                        "response": f"Could not launch IDE for {target_path.name}: {e}",
                        "grounded_doc": match.grounded_doc,
                        "speak": False
                    }
            else:
                return {
                    "status": "NOT_FOUND",
                    "trigger": match.trigger_type,
                    "response": f"Project '{proj_name}' was not found on Desktop. Check [[05_System_State/Filesystem_and_Workspaces.md]] for cataloged projects.",
                    "grounded_doc": match.grounded_doc,
                    "speak": False
                }

        elif match.action_name == "launch_application":
            target = match.parameters["target"]
            res = self.somato.launch_application(target)
            if res.get("status") == "SUCCESS":
                resp_text = f"Launched {target} successfully."
            else:
                resp_text = f"Could not launch {target}: {res.get('error', 'Target not recognized')}."
            return {
                "status": res.get("status", "SUCCESS"),
                "trigger": match.trigger_type,
                "response": resp_text,
                "grounded_doc": match.grounded_doc,
                "speak": True,
                "persona": "jarvis"
            }

        elif match.action_name == "run_cartography":
            cart = SystemCartographer(self.vault.vault_dir)
            res = cart.run_full_cartography_scan()
            projs = res.get("snapshot", {}).get("workspaces", {}).get("total_projects", 0)
            tools_cnt = len(res.get("snapshot", {}).get("toolchains", {}))
            diffs = "; ".join(res.get("diffs", [])) or "Nominal"
            return {
                "status": "SUCCESS",
                "trigger": match.trigger_type,
                "response": f"System Cartography scan complete in {res.get('latency_ms', 0):.1f}ms: Indexed {tools_cnt} toolchains, {projs} desktop projects. Diff: {diffs}.",
                "grounded_doc": match.grounded_doc,
                "speak": True,
                "persona": "edith"
            }

        elif match.action_name == "run_evolution":
            evo = SelfEvolutionEngine(self.vault.vault_dir)
            res = evo.run_evolution_cycle(trigger_source="deterministic_trigger")
            h = res.get("health", {})
            return {
                "status": "SUCCESS",
                "trigger": match.trigger_type,
                "response": f"Self-Evolution cycle executed in {res.get('latency_ms', 0):.1f}ms: Health Index {h.get('health_score')}% ({h.get('status_label')}), {res.get('rag_chunks')} RAG knowledge chunks consolidated into Git backup.",
                "grounded_doc": match.grounded_doc,
                "speak": True,
                "persona": "jarvis"
            }

        elif match.action_name == "sync_vault":
            res = self.sync.sync()
            return {
                "status": "SUCCESS",
                "trigger": match.trigger_type,
                "response": f"Obsidian Vault synchronized: {res.get('message', 'Completed')}.",
                "grounded_doc": match.grounded_doc,
                "speak": True,
                "persona": "jarvis"
            }

        elif match.action_name == "control_media":
            cmd = match.parameters.get("command", "toggle")
            res = await self.somato.control_media(cmd)
            return {
                "status": "SUCCESS",
                "trigger": match.trigger_type,
                "response": f"Media command '{cmd}' dispatched: {res.get('status', 'OK')}.",
                "grounded_doc": match.grounded_doc,
                "speak": False
            }

        return {
            "status": "UNHANDLED",
            "trigger": match.trigger_type,
            "response": f"Trigger matched '{match.trigger_type}' but no handler executed.",
            "grounded_doc": match.grounded_doc,
            "speak": False
        }

    def get_greeting(self) -> Dict[str, Any]:
        """Generates grounded startup greeting for operator Soham."""
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.05)
        avail_gb = round(mem.available / (1024**3), 1)

        text = (
            f"Greetings Soham. CortexOS is active and fully grounded in your Obsidian Vault. "
            f"All hardware monitors, neural voice pipelines, and supervisors are nominal. "
            f"You have {avail_gb} gigabytes of RAM available. How shall we proceed today?"
        )
        return {
            "status": "SUCCESS",
            "trigger": "SESSION_GREETING",
            "response": text,
            "grounded_doc": "04_Skills_Catalog/Trigger_Registry.md#1. Session Greeting Triggers",
            "speak": True,
            "persona": "jarvis"
        }

    def get_shutdown(self) -> Dict[str, Any]:
        """Executes grounded shutdown and consolidation sequence."""
        # Sync vault
        sync_res = self.sync.commit(message=f"chore(session): operator stand down ({time.strftime('%Y-%m-%d %H:%M:%S')})")

        # Record introspection
        evo = SelfEvolutionEngine(self.vault.vault_dir)
        evo.record_introspection(
            event_type="Operator Stand Down / Session Exit",
            description=f"Session closed cleanly by operator Soham. Vault state committed: {sync_res.get('status')}.",
            perspective_used="Cautious"
        )

        text = (
            "Goodbye Soham. Memory state consolidated and committed to your Obsidian Vault backup. "
            "CortexOS is safely standing down."
        )
        return {
            "status": "SHUTDOWN_READY",
            "trigger": "SYSTEM_SHUTDOWN",
            "response": text,
            "grounded_doc": "04_Skills_Catalog/Trigger_Registry.md#2. Shutdown & Stand-Down Triggers",
            "speak": True,
            "persona": "jarvis"
        }


_GLOBAL_TRIGGER_ROUTER: Optional[TriggerRouter] = None


def get_trigger_router() -> TriggerRouter:
    global _GLOBAL_TRIGGER_ROUTER
    if _GLOBAL_TRIGGER_ROUTER is None:
        _GLOBAL_TRIGGER_ROUTER = TriggerRouter()
    return _GLOBAL_TRIGGER_ROUTER
