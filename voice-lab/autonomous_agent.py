"""
Autonomous Agentic Workflow & Self-Learning Engine v3.0
Implements:
1. Dual-Model Architecture: Fast Orchestrator (qwen2.5:3b) + Deep Self-Corrector (qwen3.5 9b abliterated)
2. Self-Learning Memory Loop: Caches successful workflows in assistant_memory/learned_skills.json
3. Superb Laptop Control: Creates code files, launches them directly in Notepad/VSCode, or injects via clipboard/pyautogui
4. Self-Healing Recovery: When a script fails, the heavy model diagnoses stderr and automatically fixes it
"""
import os
import sys
import json
import time
import subprocess
import urllib.request
import pyperclip
import pyautogui
from typing import Dict, Any, Optional, List

import re

OLLAMA_URL = "http://localhost:11434"

BLOCKED_SECURITY_TERMS = [
    "cmdkey", "vaultcmd", "login data", "sam", "mimikatz",
    "id_rsa", "id_ed25519", "wallet.dat", "keystore", ".aws/credentials"
]

def is_safe_powershell(command: str) -> bool:
    """Blocks any PowerShell attempt to access private tokens or system SAM."""
    cmd_lower = command.lower()
    return not any(term in cmd_lower for term in BLOCKED_SECURITY_TERMS)

class SelfLearningMemory:
    def __init__(self, memory_dir: str = r"C:\Users\soham\voice-lab\assistant_memory"):
        self.memory_dir = memory_dir
        os.makedirs(self.memory_dir, exist_ok=True)
        self.skills_file = os.path.join(self.memory_dir, "learned_skills.json")
        self.skills = self._load_skills()

    def _load_skills(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.skills_file):
            try:
                with open(self.skills_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def find_matching_skill(self, user_intent: str) -> Optional[Dict[str, Any]]:
        """Finds if a similar intent was already mastered in memory."""
        query_words = set(user_intent.lower().split())
        for item in self.skills:
            stored_words = set(item.get("intent", "").lower().split())
            intersection = query_words.intersection(stored_words)
            # If 60%+ overlap in key words
            if len(intersection) >= max(2, int(len(stored_words) * 0.6)):
                return item
        return None

    def record_success(self, intent: str, action_type: str, code_or_cmd: str, notes: str = ""):
        """Saves verified successful solution to long-term memory."""
        record = {
            "intent": intent,
            "action_type": action_type,
            "code_or_cmd": code_or_cmd,
            "notes": notes,
            "timestamp": time.time()
        }
        self.skills.append(record)
        try:
            with open(self.skills_file, "w", encoding="utf-8") as f:
                json.dump(self.skills, f, indent=2)
            print(f"[Memory Updated] Mastered new skill for intent: '{intent}'")
        except Exception as e:
            print(f"[!] Memory save error: {e}")

class AutonomousAgent:
    def __init__(
        self,
        fast_model: str = "qwen2.5:3b",
        heavy_model: str = "nandhank/qwen3.5-abliterated-truthful:9b",
        sandbox_dir: str = r"C:\Users\soham\voice-lab\sandbox"
    ):
        self.fast_model = fast_model
        self.heavy_model = heavy_model
        self.sandbox_dir = sandbox_dir
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self.memory = SelfLearningMemory()

    def _query_ollama(self, model: str, prompt: str, system: str = "") -> str:
        """Queries local Ollama model."""
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"num_ctx": 3072, "temperature": 0.1}
        }
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "").strip()
        except Exception as e:
            return f"Error: {e}"

    def _extract_coding_task(self, prompt: str) -> str:
        """Extracts the pure programming task from conversational instruction."""
        p = prompt
        patterns = [
            r"^(?:please\s+)?(?:can you\s+)?(?:open\s+notepad\s+and\s+)?(?:write|code|create|generate|make)\s+(?:a|an)?\s*(?:program|script|code|file|function)?\s*(?:to|for|that|which)?\s*",
            r"^(?:open\s+notepad\s+and\s+)"
        ]
        for pat in patterns:
            p = re.sub(pat, "", p, flags=re.IGNORECASE).strip()
        return p or prompt

    def _clean_code_fences(self, code: str) -> str:
        """Strips markdown fences and tags if model outputs them."""
        clean = code.strip()
        if "```" in clean:
            parts = clean.split("```")
            if len(parts) >= 3:
                inner = parts[1]
                if "\n" in inner:
                    clean = inner.split("\n", 1)[1]
                else:
                    clean = inner
            elif len(parts) == 2:
                clean = parts[1]
                if "\n" in clean:
                    clean = clean.split("\n", 1)[1]
        return clean.strip()

    def write_code_to_notepad(self, program_description: str) -> str:
        """Generates pure code and opens it directly in Notepad."""
        clean_task = self._extract_coding_task(program_description)
        print(f"[*] Brainstorming pure code implementation for: '{clean_task}' using {self.fast_model}...")
        
        sys_prompt = (
            "You are an expert software developer. "
            "Write ONLY the pure, complete, and syntactically valid source code for the requested task. "
            "STRICT RULES:\n"
            "1. Output ONLY the source code. Never include markdown code fences (```) or conversational remarks.\n"
            "2. NEVER write code that calls notepad.exe, cmd.exe, or OS shell wrappers unless explicitly requested as part of the software logic.\n"
            "3. Include helpful comments and a clean main entrypoint."
        )
        raw_code = self._query_ollama(self.fast_model, f"Task: {clean_task}", sys_prompt)
        code = self._clean_code_fences(raw_code)

        # Determine extension
        ext = ".py"
        lower_code = code.lower()
        if "include <iostream>" in lower_code or "#include <" in lower_code:
            ext = ".cpp"
        elif "public static void main" in lower_code:
            ext = ".java"
        elif "<!doctype html>" in lower_code or "<html" in lower_code:
            ext = ".html"
        elif "function" in lower_code and ("console.log" in lower_code or "document." in lower_code):
            ext = ".js"

        filename = f"program_{int(time.time())}{ext}"
        filepath = os.path.join(self.sandbox_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code.strip())

        # Copy to clipboard for instant pasting anywhere
        try:
            pyperclip.copy(code.strip())
        except Exception:
            pass

        # Open directly in Notepad
        subprocess.Popen(["notepad.exe", filepath])
        print(f"[+] Created {filepath} and opened in Notepad!")
        
        # Record skill in memory
        self.memory.record_success(
            intent=f"write program for {clean_task}",
            action_type="create_and_open_in_notepad",
            code_or_cmd=code.strip()[:200]
        )
        
        return f"I generated the program and opened it in Notepad for you."

    def execute_with_self_healing(self, user_intent: str) -> str:
        """
        Executes an autonomous command. If it fails, engages the heavy model
        to self-heal and repair the command, then records the lesson to memory.
        """
        # 1. Check if user wants code in Notepad
        intent_lower = user_intent.lower()
        if "notepad" in intent_lower and any(w in intent_lower for w in ["write", "code", "program", "script", "create"]):
            return self.write_code_to_notepad(user_intent)

        # 2. Check Self-Learning Memory
        matching_skill = self.memory.find_matching_skill(user_intent)
        if matching_skill:
            print(f"[Memory Hit] Found pre-learned strategy from memory!")
            cached_cmd = matching_skill.get("code_or_cmd")
            if matching_skill.get("action_type") == "powershell":
                if not is_safe_powershell(cached_cmd):
                    return "SECURITY ALERT: Cached command touches protected credentials. Aborted."
                res = subprocess.run(["powershell", "-NoProfile", "-Command", cached_cmd], capture_output=True, text=True)
                if res.returncode == 0:
                    return f"Executed learned strategy: {res.stdout.strip() or 'Success'}"

        # 3. Plan using Fast Model
        print(f"[*] Formulating action plan with {self.fast_model}...")
        planner_sys = (
            "You are an autonomous Windows OS controller. Convert the user command into a single executable PowerShell line. "
            "Output RAW JSON only: {\"command\": \"powershell command\"}"
        )
        plan_raw = self._query_ollama(self.fast_model, user_intent, planner_sys)
        
        cmd = ""
        try:
            if "{" in plan_raw and "}" in plan_raw:
                json_str = plan_raw[plan_raw.find("{"):plan_raw.rfind("}")+1]
                data = json.loads(json_str)
                cmd = data.get("command", "")
        except Exception:
            cmd = ""

        if not cmd:
            cmd = plan_raw.replace("`", "").strip()

        # Guardrails check
        if not is_safe_powershell(cmd):
            return "SECURITY ALERT: Execution blocked. Attempt to access system credentials."

        print(f"[*] Executing plan: {cmd}")
        res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=25)

        # 4. Self-Healing Loop if Failed
        if res.returncode != 0:
            print(f"[!] Execution failed with error: {res.stderr.strip()}")
            print(f"[*] Escalating to Heavy Model ({self.heavy_model}) for self-healing...")
            
            repair_prompt = (
                f"User asked: '{user_intent}'.\n"
                f"Failed command: '{cmd}'.\n"
                f"Error details: {res.stderr.strip()}.\n"
                "Fix this error and output ONLY the corrected single-line PowerShell command inside JSON: "
                "{\"command\": \"fixed_command\"}"
            )
            repair_sys = "You are an elite Windows systems engineer. Fix the command so it runs without error."
            repair_raw = self._query_ollama(self.heavy_model, repair_prompt, repair_sys)
            
            fixed_cmd = ""
            try:
                if "{" in repair_raw and "}" in repair_raw:
                    json_str = repair_raw[repair_raw.find("{"):repair_raw.rfind("}")+1]
                    fixed_cmd = json.loads(json_str).get("command", "")
            except Exception:
                fixed_cmd = repair_raw.strip()

            if fixed_cmd and is_safe_powershell(fixed_cmd):
                print(f"[*] Executing self-healed command: {fixed_cmd}")
                res2 = subprocess.run(["powershell", "-NoProfile", "-Command", fixed_cmd], capture_output=True, text=True, timeout=25)
                if res2.returncode == 0:
                    print("[+] Self-healing successful! Recording to memory.")
                    self.memory.record_success(user_intent, "powershell", fixed_cmd, notes="Repaired via Heavy Model")
                    return f"Action completed successfully: {res2.stdout.strip() or 'Done'}"
                else:
                    return f"Self-healing attempted but returned: {res2.stderr.strip()}"
            else:
                return f"Could not construct a valid safe repair plan: {res.stderr.strip()}"
        else:
            print("[+] Action achieved full success. Recording to memory.")
            self.memory.record_success(user_intent, "powershell", cmd)
            return f"Done: {res.stdout.strip() or 'Completed successfully.'}"

if __name__ == "__main__":
    agent = AutonomousAgent()
    print("Testing Autonomous Agent...")
    result = agent.write_code_to_notepad("write a program to reverse a string in C++")
    print("Result:", result)
