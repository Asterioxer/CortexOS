"""
Safe Full-System Windows Controller v2.2
Provides comprehensive computer control, live web/news fetching, media playback,
and security guardrails against accessing sensitive credentials.
"""
import subprocess
import os
import sys
import shutil
import webbrowser
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import psutil
import json
import time
import pyautogui
pyautogui.FAILSAFE = False
from bs4 import BeautifulSoup
from typing import Dict, Any, List

# Strict sensitive data blacklists
SENSITIVE_PATHS = [
    r"\.ssh", r"\.aws", r"\.azure", r"\.kube",
    r"login data", r"cookies", r"web data",
    r"wallet\.dat", r"keystore", r"id_rsa", r"id_ed25519",
    r"sam", r"system32\config\sam", r"vaultcmd"
]

SENSITIVE_ENV_KEYS = [
    "api_key", "secret", "password", "token", "private_key", "auth", "credential"
]

WEB_APPS = {
    "linkedin": "https://www.linkedin.com/feed/",
    "youtube": "https://www.youtube.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "claude": "https://claude.ai",
    "chatgpt": "https://chatgpt.com",
    "reddit": "https://www.reddit.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "netflix": "https://www.netflix.com",
    "whatsapp": "https://web.whatsapp.com",
}

APP_MAP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "explorer": "explorer.exe",
    "browser": "start",
    "chrome": "chrome.exe",
    "brave": "brave.exe",
    "braver": "brave.exe",
    "braille": "brave.exe",
    "edge": "msedge.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "vscode": "code",
    "code": "code",
    "taskmanager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "antigravity": r"C:\Users\soham\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Antigravity.lnk",
    "antigravity ide": r"C:\Users\soham\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Antigravity\Antigravity IDE.lnk",
    "anti-gravity": r"C:\Users\soham\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Antigravity.lnk",
    "anti gravity": r"C:\Users\soham\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Antigravity.lnk",
}

class SystemController:
    def __init__(self, sandbox_dir: str = None, require_confirmation: bool = True):
        self.sandbox_dir = sandbox_dir or r"C:\Users\soham\voice-lab\sandbox"
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self.require_confirmation = require_confirmation
        self._voice_callback = None

    def set_voice_callback(self, callback):
        """Sets callback to notify voice engine of persona changes."""
        self._voice_callback = callback

    def switch_persona(self, persona_name: str) -> str:
        """Switches active voice persona."""
        if self._voice_callback:
            return self._voice_callback(persona_name)
        return f"Voice persona switch requested to {persona_name}."

    def is_sensitive_path(self, path: str) -> bool:
        """Checks if a path touches private credentials or sensitive keys."""
        lower = os.path.abspath(path).lower()
        for pattern in SENSITIVE_PATHS:
            if pattern in lower:
                return True
        return False

    def check_connectivity(self) -> bool:
        """Checks if online or offline."""
        try:
            urllib.request.urlopen("https://1.1.1.1", timeout=1.5)
            return True
        except Exception:
            return False

    def open_application(self, app_name: str) -> str:
        """Launches a desktop application or web service."""
        clean = app_name.lower().replace("-", " ").replace("_", " ").strip()
        clean_no_space = clean.replace(" ", "")

        # 1. Check Web Services mapping (LinkedIn, YouTube, X, etc.)
        if clean_no_space in WEB_APPS or clean in WEB_APPS:
            url = WEB_APPS.get(clean_no_space) or WEB_APPS.get(clean)
            webbrowser.open(url)
            return f"Opened {app_name} in your browser."

        # 2. Check explicit APP_MAP
        target = APP_MAP.get(clean) or APP_MAP.get(clean_no_space)
        if target:
            try:
                os.startfile(target)
                return f"Opened {app_name} successfully."
            except Exception:
                pass

        # 3. Dynamic Windows Start Menu (.lnk) Resolution
        search_dirs = [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
        ]
        for d in search_dirs:
            if not os.path.exists(d):
                continue
            for root, dirs, files in os.walk(d):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        base = os.path.splitext(f)[0].lower().replace("-", " ").replace("_", " ").strip()
                        base_no_space = base.replace(" ", "")
                        if clean in base or base in clean or clean_no_space in base_no_space:
                            lnk_path = os.path.join(root, f)
                            try:
                                os.startfile(lnk_path)
                                return f"Opened {app_name} successfully."
                            except Exception as e:
                                return f"Error launching {app_name}: {e}"

        # 4. Check system PATH via shutil.which
        w = shutil.which(clean_no_space) or shutil.which(f"{clean_no_space}.exe")
        if w:
            try:
                os.startfile(w)
                return f"Opened {app_name} successfully."
            except Exception as e:
                return f"Error launching {app_name}: {e}"

        return f"Application '{app_name}' could not be found on your system."

    def close_application(self, app_name: str) -> str:
        """Closes an application by name or process."""
        clean = app_name.lower().strip()
        exe = APP_MAP.get(clean, app_name)
        if not exe.endswith(".exe"):
            exe += ".exe"
        try:
            res = subprocess.run(["taskkill", "/IM", exe, "/F"], capture_output=True, text=True)
            if res.returncode == 0:
                return f"Closed {app_name}."
            else:
                return f"Process {exe} is not currently running."
        except Exception as e:
            return f"Error closing {app_name}: {e}"

    def get_system_stats(self) -> str:
        """Retrieves CPU, RAM, battery, and disk statistics."""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            battery = psutil.sensors_battery()
            bat_str = f"{battery.percent}% ({'Plugged in' if battery.power_plugged else 'On Battery'})" if battery else "Desktop (No Battery)"

            return (
                f"System Health:\n"
                f"  - CPU: {cpu}%\n"
                f"  - RAM: {mem.percent}% used ({mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB)\n"
                f"  - Disk C: {disk.percent}% used ({disk.free // (1024**3)}GB free)\n"
                f"  - Battery: {bat_str}"
            )
        except Exception as e:
            return f"Error retrieving system stats: {e}"

    def set_volume(self, level: int) -> str:
        """Adjusts master audio volume (0-100)."""
        level = max(0, min(100, int(level)))
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", f"$obj = New-Object -ComObject WScript.Shell; 1..50 | % {{ $obj.SendKeys([char]174) }}; 1..{level//2} | % {{ $obj.SendKeys([char]175) }}"], capture_output=True)
            return f"Audio volume adjusted to approximately {level}%."
        except Exception as e:
            return f"Failed to set volume: {e}"

    def mute_volume(self) -> str:
        """Toggles system audio mute."""
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]173)"], capture_output=True)
            return "Audio mute toggled."
        except Exception as e:
            return f"Failed to toggle mute: {e}"

    def take_screenshot(self, filename: str = None) -> str:
        """Takes a full desktop screenshot and saves it in sandbox/screenshots/."""
        try:
            screenshots_dir = os.path.join(self.sandbox_dir, "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            if not filename:
                filename = f"screenshot_{int(time.time())}.png"
            if not filename.endswith(".png"):
                filename += ".png"
            filepath = os.path.join(screenshots_dir, filename)
            try:
                pyautogui.screenshot(filepath)
                return f"Screenshot saved successfully at: {filepath}"
            except Exception as pe:
                err_str = str(pe).lower()
                if "screen grab failed" in err_str or "bitblt" in err_str:
                    return "Screen capture paused: The Windows display is currently locked or asleep."
                return f"Failed to take screenshot: {pe}"
        except Exception as e:
            return f"Failed to take screenshot: {e}"

    def toggle_desktop(self) -> str:
        """Minimizes/restores all windows to show the desktop (Win + D)."""
        try:
            pyautogui.hotkey('win', 'd')
            return "Toggled desktop display (minimized/restored windows)."
        except Exception as e:
            return f"Failed to toggle desktop: {e}"

    def media_control(self, action: str = "play_pause") -> str:
        """Controls media playback: play_pause, next, prev."""
        key_map = {
            "play_pause": 179,
            "play": 179,
            "pause": 179,
            "next": 176,
            "previous": 177,
            "prev": 177
        }
        vk = key_map.get(action.lower().strip(), 179)
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", f"$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]{vk})"], capture_output=True)
            return f"Media control '{action}' performed."
        except Exception as e:
            return f"Failed media control: {e}"

    def open_website(self, url: str, app: str = None) -> str:
        """Opens a website URL in the user's browser."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        if app and "brave" in app.lower():
            try:
                subprocess.Popen(f"start brave \"{url}\"", shell=True)
                return f"Opened {url} in Brave."
            except Exception:
                pass
        webbrowser.open(url)
        return f"Opened {url} in browser."

    def open_chrome_tab(self, url_or_query: str = "") -> str:
        """
        Visually focuses Chrome or launches it, sends Ctrl+T to open a new tab,
        and optionally pastes the URL/query via Ctrl+V and presses Enter.
        """
        import pyperclip
        try:
            # 1. Check if Chrome is running
            chrome_running = any("chrome" in p.name().lower() for p in psutil.process_iter(["name"]))
            if not chrome_running:
                subprocess.Popen("start chrome", shell=True)
                time.sleep(1.2)
            else:
                # Focus Chrome window via PowerShell AppActivate
                try:
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command",
                         "$ws = New-Object -ComObject WScript.Shell; $ws.AppActivate('Google Chrome')"],
                        capture_output=True,
                        timeout=2
                    )
                    time.sleep(0.2)
                except Exception:
                    pass

            # 2. Visually open a new tab with Ctrl + T
            try:
                pyautogui.hotkey('ctrl', 't')
                time.sleep(0.2)
            except Exception:
                pass

            # 3. If url_or_query provided, paste and submit
            target = url_or_query.strip()
            if target:
                if not target.startswith(("http://", "https://")) and any(ext in target for ext in [".com", ".org", ".io", ".net", ".edu", "localhost"]):
                    target = "https://" + target
                elif not target.startswith(("http://", "https://")):
                    target = f"https://www.google.com/search?q={urllib.parse.quote(target)}"

                pyperclip.copy(target)
                time.sleep(0.05)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.05)
                pyautogui.press('enter')
                return f"Opened new Chrome tab with '{target}'."

            return "Opened a new Chrome tab."
        except Exception as e:
            if url_or_query:
                webbrowser.open(url_or_query)
                return f"Opened {url_or_query} in default browser."
            return f"Error opening Chrome tab: {e}"

    def switch_browser_tab(self, tab_number: int = 1) -> str:
        """
        Visually switches to a specific tab in Google Chrome or active browser (1-9)
        by activating the window and sending Ctrl + <number>.
        """
        try:
            tab_num = max(1, min(9, int(tab_number)))
            # Focus Chrome if running
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "$ws = New-Object -ComObject WScript.Shell; $ws.AppActivate('Google Chrome')"],
                    capture_output=True,
                    timeout=2
                )
                time.sleep(0.1)
            except Exception:
                pass

            pyautogui.hotkey('ctrl', str(tab_num))
            return f"Switched to tab {tab_num} in Google Chrome."
        except Exception as e:
            return f"Error switching browser tab: {e}"

    def claude_web_prompt(self, prompt: str) -> str:
        """
        Visually automates Claude AI in Chrome: opens a new tab to https://claude.ai/new,
        waits for page render, pastes transcribed user prompt, and presses Enter.
        """
        import pyperclip
        clean_prompt = prompt.strip()
        if not clean_prompt:
            return "No prompt provided for Claude."

        try:
            # 1. Open Claude in a new Chrome tab
            self.open_chrome_tab("https://claude.ai/new")
            
            # 2. Wait for page load & prompt input focus
            time.sleep(2.5)

            # 3. Put prompt into clipboard and paste into Claude
            pyperclip.copy(clean_prompt)
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)

            # 4. Submit prompt
            pyautogui.press('enter')

            return f"Claude AI loaded in Chrome and prompt submitted: '{clean_prompt[:60]}...'"
        except Exception as e:
            return f"Error automating Claude in Chrome: {e}"

    def open_folder(self, path: str = ".") -> str:
        """Opens a folder in Windows File Explorer."""
        abs_path = os.path.abspath(path)
        if self.is_sensitive_path(abs_path):
            return "ACCESS DENIED: Attempted to open a sensitive credential directory."
        try:
            subprocess.Popen(["explorer.exe", abs_path])
            return f"Opened {abs_path} in File Explorer."
        except Exception as e:
            return f"Failed to open folder: {e}"

    def list_files(self, path: str = ".") -> str:
        """Lists directory contents, filtering sensitive folders."""
        abs_path = os.path.abspath(path)
        if self.is_sensitive_path(abs_path):
            return "ACCESS DENIED: Directory contains protected credentials."
        try:
            entries = os.listdir(abs_path)
            safe_entries = [e for e in entries if not self.is_sensitive_path(os.path.join(abs_path, e))]
            return f"Files in {abs_path}:\n" + "\n".join([f"  - {e}" for e in safe_entries[:40]])
        except Exception as e:
            return f"Error listing directory: {e}"

    def read_file_content(self, path: str) -> str:
        """Reads a text file, enforcing sensitive information protection."""
        abs_path = os.path.abspath(path)
        if self.is_sensitive_path(abs_path):
            return "ACCESS DENIED: This file contains private passwords, tokens, or security credentials."
        if not os.path.isfile(abs_path):
            return f"File does not exist: {abs_path}"

        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if abs_path.endswith((".env", ".config", ".json", ".ini")):
                lower_content = content.lower()
                for key in SENSITIVE_ENV_KEYS:
                    if f"{key}=" in lower_content or f'"{key}"' in lower_content:
                        return "ACCESS DENIED: File contains sensitive API keys or secret credentials."

            return content[:3000] + ("\n... [truncated]" if len(content) > 3000 else "")
        except Exception as e:
            return f"Error reading file: {e}"

    def create_text_file(self, filename: str, content: str) -> str:
        """Creates or writes a file safely."""
        if not os.path.isabs(filename):
            filepath = os.path.join(self.sandbox_dir, filename)
        else:
            filepath = filename

        if self.is_sensitive_path(filepath):
            return "ACCESS DENIED: Cannot overwrite security credentials."

        try:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File created successfully at: {filepath}"
        except Exception as e:
            return f"Failed to create file: {e}"

    def web_search(self, query: str, app: str = None) -> str:
        """Searches the web via browser."""
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        if app and "brave" in app.lower():
            try:
                subprocess.Popen(f"start brave \"{url}\"", shell=True)
                return f"Searching '{query}' in Brave browser."
            except Exception:
                pass
        webbrowser.open(url)
        return f"Searching web for: '{query}'"

    def play_media(self, query: str, app: str = None) -> str:
        """Plays music, songs, or videos on YouTube in the browser."""
        clean = query.strip()
        encoded = urllib.parse.quote(clean)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        if app and "brave" in app.lower():
            try:
                subprocess.Popen(f"start brave \"{url}\"", shell=True)
                return f"Playing '{clean}' in Brave browser on YouTube."
            except Exception:
                pass
        webbrowser.open(url)
        return f"Playing '{clean}' on YouTube."

    def fetch_live_news(self, topic: str = "world breaking news") -> str:
        """Fetches REAL live news headlines and summaries from Google News RSS."""
        clean_topic = topic.strip().lower()
        general_topics = ["world breaking news", "top news", "latest news", "news", "today's top news", "breaking news", "world news", "top headlines"]

        if clean_topic in general_topics or not clean_topic:
            # Use top headlines RSS feed for real global & national breaking news
            url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
            label = "Top Breaking World & National News"
        else:
            encoded = urllib.parse.quote(clean_topic)
            url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
            label = f"Live News Headlines for '{clean_topic}'"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                root = ET.fromstring(resp.read())
                items = root.findall(".//item")[:5]
                if not items:
                    return f"No recent news articles found for '{clean_topic}'."

                news_output = f"{label}:\n"
                for i, item in enumerate(items, 1):
                    title = item.find("title").text if item.find("title") is not None else "Untitled"
                    pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    news_output += f"{i}. {title} ({pub_date[:16]})\n"

                return news_output
        except Exception as e:
            return f"Error fetching live news: {e}"

    def read_webpage(self, url: str) -> str:
        """Reads and extracts text from a webpage URL."""
        if not url.startswith(("http://", "https://")):
            return "Invalid URL. Must start with http:// or https://"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read()
                soup = BeautifulSoup(html, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = " ".join(soup.stripped_strings)
                return text[:2500] + ("\n... [truncated]" if len(text) > 2500 else "")
        except Exception as e:
            return f"Could not read webpage: {e}"

    def run_powershell(self, command: str) -> str:
        """Runs a PowerShell command with security blocks on credential access."""
        cmd_lower = command.lower()
        blocked_terms = ["cmdkey", "vaultcmd", "login data", "sam", "mimikatz", "id_rsa"]
        if any(term in cmd_lower for term in blocked_terms):
            return "SECURITY ALERT: Execution blocked. Attempt to access system credentials."

        destructive_verbs = ["remove-item", "del ", "delete", "rmdir", "rd ", "format", "shutdown", "diskpart"]
        if any(v in cmd_lower for v in destructive_verbs) and self.require_confirmation:
            print(f"\n[⚠️ RISK ALERT] Assistant requested destructive action:\n  PS> {command}")
            confirm = input("Authorize command execution? [y/N]: ").strip().lower()
            if confirm != "y":
                return "Execution aborted by user."

        try:
            res = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30
            )
            out = res.stdout.strip()
            err = res.stderr.strip()
            if res.returncode == 0:
                return out or "Command executed successfully with no output."
            else:
                return f"Command error (Code {res.returncode}): {err}"
        except subprocess.TimeoutExpired:
            return "Command timed out."
        except Exception as e:
            return f"Execution error: {e}"

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """JSON Schema tool definitions for Ollama function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "fetch_live_news",
                    "description": "Fetches real live news headlines and summaries about a topic (e.g. India politics, world news, Rahul Gandhi, tech)",
                    "parameters": {
                        "type": "object",
                        "properties": {"topic": {"type": "string", "description": "News topic or query"}},
                        "required": ["topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "play_media",
                    "description": "Plays a song, music, or video on YouTube in the browser (e.g. Brave or default browser)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Song, artist, or video title to play"},
                            "app": {"type": "string", "description": "Browser or player name, e.g. brave, chrome"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_application",
                    "description": "Opens an app like notepad, calc, chrome, brave, code, or terminal",
                    "parameters": {
                        "type": "object",
                        "properties": {"app_name": {"type": "string", "description": "Application name"}},
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "close_application",
                    "description": "Closes a running application",
                    "parameters": {
                        "type": "object",
                        "properties": {"app_name": {"type": "string", "description": "App or exe to close"}},
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_system_stats",
                    "description": "Gets current CPU, RAM, disk, and battery levels",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_folder",
                    "description": "Opens a folder in File Explorer",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string", "description": "Folder path"}},
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_webpage",
                    "description": "Reads and extracts text from a web article or URL",
                    "parameters": {
                        "type": "object",
                        "properties": {"url": {"type": "string", "description": "Webpage URL"}},
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Searches the web in browser",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "app": {"type": "string", "description": "Browser name (e.g. brave, chrome)"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_volume",
                    "description": "Sets system audio volume from 0 to 100",
                    "parameters": {
                        "type": "object",
                        "properties": {"level": {"type": "integer", "description": "Volume percentage (0-100)"}},
                        "required": ["level"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "take_screenshot",
                    "description": "Takes a screenshot of the user's screen and saves to sandbox/screenshots",
                    "parameters": {
                        "type": "object",
                        "properties": {"filename": {"type": "string", "description": "Optional filename, e.g. snap.png"}}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "toggle_desktop",
                    "description": "Minimizes all windows to show the desktop, or restores them (Win + D)",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mute_volume",
                    "description": "Toggles audio mute on or off",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_website",
                    "description": "Opens a website URL in the browser (e.g. github.com, youtube.com, brave)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Website URL"},
                            "app": {"type": "string", "description": "Browser, e.g. brave, chrome"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "media_control",
                    "description": "Controls music playback: play_pause, next, prev",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "description": "play_pause, next, or prev"}
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_powershell",
                    "description": "Executes a PowerShell command",
                    "parameters": {
                        "type": "object",
                        "properties": {"command": {"type": "string", "description": "PowerShell command"}},
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_chrome_tab",
                    "description": "Visually opens a new tab in Google Chrome and optionally navigates to a URL or search query",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url_or_query": {"type": "string", "description": "URL to open or query to search in the new tab"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "claude_web_prompt",
                    "description": "Visually opens Claude AI (claude.ai) in Chrome, focuses the prompt box, pastes the user prompt, and submits it",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string", "description": "Prompt or question to send to Claude AI"}
                        },
                        "required": ["prompt"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "switch_browser_tab",
                    "description": "Switches to a specific tab in the browser (1 to 9) using Ctrl+<number>",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tab_number": {"type": "integer", "description": "Tab number (1 to 9) to focus"}
                        },
                        "required": ["tab_number"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "switch_persona",
                    "description": "Switches the assistant speaking voice persona (christopher, jenny, guy, aria, neerja, prabhat, eric)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "persona_name": {"type": "string", "description": "Target voice persona name"}
                        },
                        "required": ["persona_name"]
                    }
                }
            }
        ]

    def execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Executes tool safely."""
        handlers = {
            "fetch_live_news": lambda a: self.fetch_live_news(a.get("topic", "world breaking news")),
            "play_media": lambda a: self.play_media(a.get("query", ""), a.get("app")),
            "open_application": lambda a: self.open_application(a.get("app_name", "")),
            "close_application": lambda a: self.close_application(a.get("app_name", "")),
            "get_system_stats": lambda a: self.get_system_stats(),
            "open_folder": lambda a: self.open_folder(a.get("path", ".")),
            "read_webpage": lambda a: self.read_webpage(a.get("url", "")),
            "web_search": lambda a: self.web_search(a.get("query", ""), a.get("app")),
            "set_volume": lambda a: self.set_volume(a.get("level", 50)),
            "mute_volume": lambda a: self.mute_volume(),
            "take_screenshot": lambda a: self.take_screenshot(a.get("filename")),
            "toggle_desktop": lambda a: self.toggle_desktop(),
            "open_website": lambda a: self.open_website(a.get("url", ""), a.get("app")),
            "media_control": lambda a: self.media_control(a.get("action", "play_pause")),
            "run_powershell": lambda a: self.run_powershell(a.get("command", "")),
            "open_chrome_tab": lambda a: self.open_chrome_tab(a.get("url_or_query", "")),
            "switch_browser_tab": lambda a: self.switch_browser_tab(a.get("tab_number", 1)),
            "switch_persona": lambda a: self.switch_persona(a.get("persona_name", "jenny")),
            "claude_web_prompt": lambda a: self.claude_web_prompt(a.get("prompt", ""))
        }
        handler = handlers.get(name)
        if not handler:
            return f"Unknown tool: {name}"
        return handler(args)

if __name__ == "__main__":
    ctrl = SystemController()
    print("Testing Live News Fetch:")
    print(ctrl.fetch_live_news("Rahul Gandhi Jaishankar Marco Rubio"))
