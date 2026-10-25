"""
Dynamic Context & Ollama Inference Engine
Handles auto-adjustable context windows, fast GPU offload optimization, and model dispatch.
"""
import urllib.request
import json
import time
import subprocess
from typing import Dict, Any, Optional, List, Tuple

class AdaptiveContextEngine:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url.rstrip("/")
        
        # Hardware-tuned profiles for RTX 3050 (4GB VRAM) + 24GB System RAM
        self.profiles = {
            "voice": {
                "num_ctx": 1536,
                "num_predict": 256,
                "temperature": 0.2,
                "description": "Ultra-fast voice & quick command execution (low VRAM cache)"
            },
            "balanced": {
                "num_ctx": 4096,
                "num_predict": 512,
                "temperature": 0.3,
                "description": "Standard tool calling, file management, and computer control"
            },
            "deep": {
                "num_ctx": 8192,
                "num_predict": 2048,
                "temperature": 0.5,
                "description": "Extended reasoning, coding, and comprehensive problem solving"
            }
        }
        self.active_profile = "balanced"
        self.ensure_ollama_running()

    def ensure_ollama_running(self) -> bool:
        """Checks if Ollama is online; if not, automatically launches 'ollama serve' in background."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags")
            with urllib.request.urlopen(req, timeout=1.0):
                return True
        except Exception:
            pass

        print("[*] Ollama server offline. Automatically launching 'ollama serve' in background...")
        try:
            import shutil
            import os

            ollama_bin = "ollama"
            default_path = r"C:\Users\soham\AppData\Local\Programs\Ollama\ollama.exe"
            if shutil.which("ollama"):
                ollama_bin = "ollama"
            elif os.path.exists(default_path):
                ollama_bin = default_path

            DETACHED_PROCESS = 0x00000008
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(
                [ollama_bin, "serve"],
                creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            t0 = time.time()
            while time.time() - t0 < 8.0:
                time.sleep(0.4)
                try:
                    req = urllib.request.Request(f"{self.ollama_url}/api/tags")
                    with urllib.request.urlopen(req, timeout=1.0):
                        print("[+] Ollama server started and ready!")
                        return True
                except Exception:
                    continue
        except Exception as e:
            print(f"[!] Could not auto-launch Ollama: {e}")
        return False

    def _post_json(self, endpoint: str, payload: Dict[str, Any], timeout: Optional[float] = None):
        """Performs a POST request to Ollama with automatic self-healing startup and retry."""
        url = f"{self.ollama_url}{endpoint}"
        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, data=data_bytes, headers=headers)

        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError as e:
            err_str = str(e)
            if "10061" in err_str or "Connection refused" in err_str or "refused" in err_str.lower():
                print("[*] Ollama connection refused. Auto-launching 'ollama serve'...")
                if self.ensure_ollama_running():
                    req_retry = urllib.request.Request(url, data=data_bytes, headers=headers)
                    return urllib.request.urlopen(req_retry, timeout=timeout)
            raise e

    def estimate_tokens(self, text: str) -> int:
        """Rough token count estimation (~4 characters per token)."""
        return max(1, len(text) // 4)

    def auto_select_options(
        self,
        prompt: str,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        user_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically adjusts num_ctx and num_predict based on prompt size,
        tool presence, and user preference.
        """
        if user_preference and user_preference in self.profiles:
            cfg = self.profiles[user_preference].copy()
            del cfg["description"]
            return cfg

        total_text = prompt + (system or "")
        est_tokens = self.estimate_tokens(total_text)
        if tools:
            # Add estimated tokens for tool schemas
            est_tokens += len(tools) * 75

        # Auto-adjust rules:
        if est_tokens < 300 and not tools:
            # Quick dialogue or voice query -> Voice/Fast mode
            mode = "voice"
        elif est_tokens < 1500:
            # Moderate prompt, tool calling, or system action
            mode = "balanced"
        else:
            # Large code file, multi-turn history, or complex document
            mode = "deep"

        cfg = self.profiles[mode].copy()
        del cfg["description"]
        return cfg

    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        profile: Optional[str] = None,
        custom_ctx: Optional[int] = None,
        custom_predict: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generates a text completion with dynamic context adjustment."""
        options = self.auto_select_options(prompt, system=system, user_preference=profile)
        
        if custom_ctx:
            options["num_ctx"] = custom_ctx
        if custom_predict:
            options["num_predict"] = custom_predict
        if temperature is not None:
            options["temperature"] = temperature

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "24h",
            "options": options
        }
        if system:
            payload["system"] = system

        t0 = time.time()
        with self._post_json("/api/generate", payload) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            data["total_client_time"] = time.time() - t0
            data["applied_options"] = options
            return data

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        profile: Optional[str] = None,
        custom_ctx: Optional[int] = None,
        custom_predict: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Sends a chat completion with tools and dynamic context adaptation."""
        combined_text = " ".join([m.get("content", "") for m in messages])
        options = self.auto_select_options(combined_text, tools=tools, user_preference=profile)

        if custom_ctx:
            options["num_ctx"] = custom_ctx
        if custom_predict:
            options["num_predict"] = custom_predict
        if temperature is not None:
            options["temperature"] = temperature

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": "24h",
            "options": options
        }
        if tools:
            payload["tools"] = tools

        t0 = time.time()
        with self._post_json("/api/chat", payload) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            data["total_client_time"] = time.time() - t0
            data["applied_options"] = options
            return data

    def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        profile: Optional[str] = None,
        custom_ctx: Optional[int] = None,
        custom_predict: Optional[int] = None,
        temperature: Optional[float] = None
    ):
        """
        Streams chat completion tokens from Ollama.
        Yields dict: {"content": str, "tool_calls": list, "done": bool, "raw": dict}
        """
        combined_text = " ".join([m.get("content", "") for m in messages])
        options = self.auto_select_options(combined_text, tools=tools, user_preference=profile)

        if custom_ctx:
            options["num_ctx"] = custom_ctx
        if custom_predict:
            options["num_predict"] = custom_predict
        if temperature is not None:
            options["temperature"] = temperature

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "keep_alive": "24h",
            "options": options
        }
        if tools:
            payload["tools"] = tools

        with self._post_json("/api/chat", payload) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue
                try:
                    data = json.loads(line_str)
                except Exception:
                    continue

                msg = data.get("message", {})
                content = msg.get("content", "")
                tool_calls = msg.get("tool_calls", [])
                done = data.get("done", False)

                yield {
                    "content": content,
                    "tool_calls": tool_calls,
                    "done": done,
                    "raw": data
                }

if __name__ == "__main__":
    engine = AdaptiveContextEngine()
    print("Testing Adaptive Context Engine...")
    print("\n--- 1. Testing Voice Mode Auto-Selection on Short Prompt ---")
    short_q = "What time is it in Tokyo?"
    opts = engine.auto_select_options(short_q)
    print(f"Auto-selected options for '{short_q}':\n  {opts}")

    print("\n--- 2. Testing Balanced Mode Auto-Selection on Tool Calling Prompt ---")
    tool_q = "List files in C:\\Users\\soham\\Desktop and check storage"
    opts_tool = engine.auto_select_options(tool_q, tools=[{"type": "function", "function": {"name": "list_files"}}])
    print(f"Auto-selected options for tool call:\n  {opts_tool}")

    print("\n--- 3. Testing Real Dynamic Request with qwen2.5:3b ---")
    res = engine.generate(
        model="qwen2.5:3b",
        prompt="Reply with exactly three words: Ready for commands.",
        profile="voice"
    )
    print(f"Client time: {res['total_client_time']:.2f}s | Context: {res['applied_options']['num_ctx']}")
    print(f"Response: {res.get('response', '').strip()}")
