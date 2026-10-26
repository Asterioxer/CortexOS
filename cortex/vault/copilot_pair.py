import asyncio
import os
import re
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from cortex.vault.vault_manager import ObsidianVault, get_vault
from cortex.vault.rag_engine import VaultRAG, get_vault_rag
from cortex.vault.git_sync import VaultSync, get_vault_sync
from cortex.embodiment.system_somatosensory import SystemSomatosensory
from cortex.governance.sandbox import SandboxRunner


class PairCopilot:
    """Autonomous Pair Programming Copilot.
    
    Pairs directly with the operator to immediately execute requested actions,
    grounded in the Obsidian Vault to prevent hallucinations.
    """

    def __init__(
        self,
        vault: Optional[ObsidianVault] = None,
        rag: Optional[VaultRAG] = None,
        sync: Optional[VaultSync] = None,
        somatosensory: Optional[SystemSomatosensory] = None,
        sandbox: Optional[SandboxRunner] = None
    ):
        self.vault = vault or get_vault()
        self.rag = rag or get_vault_rag()
        self.sync = sync or get_vault_sync()
        self.somato = somatosensory or SystemSomatosensory()
        self.sandbox = sandbox or SandboxRunner()

    async def execute_pair_request(self, prompt: str) -> Dict[str, Any]:
        """Analyzes operator request, retrieves vault grounding, and immediately executes the appropriate action."""
        prompt_clean = prompt.strip()
        p_lower = prompt_clean.lower()

        # 1. Retrieve grounded context from vault
        grounded_sources = self.rag.search(prompt_clean, top_k=3)
        sources_summary = [f"{s.rel_path}#{s.header}" for s in grounded_sources]

        action_executed = None
        action_result = None
        user_response = ""

        # Intent 1: Vault Sync / Backup
        if any(w in p_lower for w in ["sync vault", "backup vault", "vault backup", "push vault"]):
            res = self.sync.sync()
            action_executed = {"type": "vault_sync"}
            action_result = res
            user_response = f"Obsidian Vault synchronized: {res.get('message', 'Completed')}."

        # Intent 2: Vault Search / Query
        elif p_lower.startswith(("search vault", "vault search", "query vault", "ask vault")):
            q = re.sub(r"^(search vault|vault search|query vault|ask vault)\s*", "", prompt_clean, flags=re.I)
            results = self.rag.search(q, top_k=3)
            action_executed = {"type": "vault_search", "query": q}
            action_result = [r.to_dict() for r in results]
            if results:
                best = results[0]
                user_response = f"Found in [[{best.rel_path}|{best.header}]]:\n\n{best.snippet}"
            else:
                user_response = f"No direct match found in vault for '{q}'."

        # Intent 3: Add Note to Vault
        elif p_lower.startswith(("add note", "record note", "save note", "note that")):
            content_part = re.sub(r"^(add note|record note|save note|note that)\s*:?\s*", "", prompt_clean, flags=re.I)
            title = content_part[:40].replace("\n", " ").strip()
            slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", title).strip("_") or "note"
            rel_path = f"02_Pair_Programming/Notes_{slug}.md"
            note = self.vault.save_note(
                rel_path=rel_path,
                content=content_part,
                title=title,
                frontmatter={"type": "pair_note", "tags": ["cortex/pair_notes", "cortex/copilot"]}
            )
            # Rebuild RAG index
            self.rag._build_index()
            action_executed = {"type": "vault_add_note", "path": rel_path}
            action_result = {"status": "SUCCESS", "path": rel_path}
            user_response = f"Recorded note to [[{rel_path}|{title}]]."

        # Intent 4: Application Launching
        elif p_lower.startswith(("open ", "launch ", "start ")):
            target = re.sub(r"^(open|launch|start)\s+", "", prompt_clean, flags=re.I).strip()
            res = self.somato.launch_application(target)
            action_executed = {"type": "launch_application", "target": target}
            action_result = res
            if res.get("status") == "SUCCESS":
                user_response = f"Launched {target} successfully."
            else:
                user_response = f"Could not launch {target}: {res.get('error', 'Target not recognized')}."

        # Intent 5: Media Control
        elif any(w in p_lower for w in ["pause music", "resume music", "play music", "next song", "previous song", "what song"]):
            cmd = "toggle"
            if "next" in p_lower:
                cmd = "next"
            elif "previous" in p_lower:
                cmd = "previous"
            res = await self.somato.control_media(cmd)
            action_executed = {"type": "media_control", "command": cmd}
            action_result = res
            user_response = f"Media command '{cmd}' executed: {res.get('status', 'OK')}."

        # Intent 6: Hardware & System Telemetry
        elif any(w in p_lower for w in ["telemetry", "hardware", "cpu usage", "ram usage", "battery", "gpu"]):
            telem = self.somato.get_hardware_telemetry()
            action_executed = {"type": "get_telemetry"}
            action_result = telem
            cpu = telem["cpu"]["percent"]
            ram = f"{telem['ram']['used_gb']}/{telem['ram']['total_gb']} GB ({telem['ram']['percent']}%)"
            user_response = f"Hardware Posture: CPU {cpu}% | RAM {ram} | Focused: {self.somato.get_active_window().get('title', 'Unknown')}."

        # Intent 7: Open Applications & Processes
        elif any(w in p_lower for w in ["open applications", "running applications", "what apps are open", "list processes"]):
            apps = self.somato.get_user_applications(top_n=8)
            action_executed = {"type": "get_user_applications"}
            action_result = apps
            app_list = ", ".join(f"{a['name']} ({a['title'][:25]})" for a in apps[:6])
            user_response = f"Open User Applications ({len(apps)}): {app_list or 'None'}."

        # Intent 8: Run Tests / Shell Command
        elif p_lower.startswith(("run test", "run tests", "pytest")):
            res = await self.sandbox.run_command_in_sandbox(".venv\\Scripts\\python.exe -m pytest tests/ -k 'not voice_lab'")
            action_executed = {"type": "run_tests"}
            action_result = res
            user_response = f"Test execution completed (Exit code {res['exit_code']}):\n{res['stdout'][-300:] or res['stderr'][-300:]}"

        # Default: Grounded reasoning using Vault RAG
        else:
            if grounded_sources:
                best = grounded_sources[0]
                user_response = (
                    f"Grounded from [[{best.rel_path}|{best.note_title}]]:\n\n"
                    f"{best.snippet}\n\n"
                    f"Ready to execute any concrete operation. How shall we proceed?"
                )
            else:
                user_response = f"Ready to assist with '{prompt_clean}'. What action would you like me to execute?"

        # Log active pair context to Active_Context.md
        self.vault.update_active_context(
            active_goal=f"Pairing: {prompt_clean[:50]}",
            details={
                "Last Query": prompt_clean,
                "Action Dispatched": action_executed.get("type") if action_executed else "Grounded Guidance",
                "Grounded Sources": ", ".join(sources_summary) or "None"
            }
        )

        return {
            "prompt": prompt_clean,
            "action_executed": action_executed,
            "action_result": action_result,
            "user_response": user_response,
            "grounded_sources": sources_summary
        }


_GLOBAL_PAIR_COPILOT: Optional[PairCopilot] = None


def get_pair_copilot() -> PairCopilot:
    global _GLOBAL_PAIR_COPILOT
    if _GLOBAL_PAIR_COPILOT is None:
        _GLOBAL_PAIR_COPILOT = PairCopilot()
    return _GLOBAL_PAIR_COPILOT
