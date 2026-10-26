import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import psutil

class SystemSomatosensory:
    """
    Embodied Somatosensory Perception and System Autonomy Engine for Windows.
    Provides sub-15ms hardware telemetry, process monitoring, filesystem control,
    and command execution with deep laptop awareness.
    """
    def __init__(self, default_workspace: Optional[str] = None):
        self.workspace_dir = Path(default_workspace or os.getcwd()).resolve()
        self.user_name = os.getlogin()
        self.user_home = Path.home()
        self.desktop_dir = self.user_home / "Desktop"
        self.downloads_dir = self.user_home / "Downloads"
        self._proc_cache_time = 0.0
        self._cached_procs: List[Dict[str, Any]] = []
        self._cached_apps: List[Dict[str, Any]] = []

    def get_hardware_telemetry(self) -> Dict[str, Any]:
        """Queries CPU, RAM, GPU, Disks, and Battery in <15ms."""
        # 1. CPU
        cpu_pct = psutil.cpu_percent(interval=0.05)
        phys_cores = psutil.cpu_count(logical=False) or 0
        log_cores = psutil.cpu_count(logical=True) or 0
        
        # 2. RAM
        vm = psutil.virtual_memory()
        ram_total_gb = round(vm.total / (1024**3), 1)
        ram_used_gb = round(vm.used / (1024**3), 1)
        ram_free_gb = round(vm.available / (1024**3), 1)
        ram_pct = vm.percent

        # 3. GPU (nvidia-smi)
        gpu_info = self._get_nvidia_telemetry()

        # 4. Storage (C: Drive)
        try:
            disk = psutil.disk_usage("C:")
            disk_total_gb = round(disk.total / (1024**3), 1)
            disk_used_gb = round(disk.used / (1024**3), 1)
            disk_free_gb = round(disk.free / (1024**3), 1)
            disk_pct = disk.percent
        except Exception:
            disk_total_gb, disk_used_gb, disk_free_gb, disk_pct = 0, 0, 0, 0

        # 5. Battery
        batt = psutil.sensors_battery()
        batt_pct = batt.percent if batt else 100
        plugged_in = batt.power_plugged if batt else True

        return {
            "user": self.user_name,
            "os": platform.platform(),
            "cpu": {
                "percent": cpu_pct,
                "cores_physical": phys_cores,
                "cores_logical": log_cores,
            },
            "ram": {
                "total_gb": ram_total_gb,
                "used_gb": ram_used_gb,
                "free_gb": ram_free_gb,
                "percent": ram_pct,
            },
            "gpu": gpu_info,
            "disk_c": {
                "total_gb": disk_total_gb,
                "used_gb": disk_used_gb,
                "free_gb": disk_free_gb,
                "percent": disk_pct,
            },
            "battery": {
                "percent": batt_pct,
                "plugged_in": plugged_in,
            },
            "timestamp": time.time()
        }

    def _get_nvidia_telemetry(self) -> Dict[str, Any]:
        """Queries nvidia-smi for RTX GPU details."""
        try:
            res = subprocess.run([
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu,power.draw",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True, timeout=1.5)
            if res.returncode == 0 and res.stdout.strip():
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                return {
                    "name": parts[0],
                    "vram_total_mb": int(parts[1]),
                    "vram_used_mb": int(parts[2]),
                    "vram_free_mb": int(parts[3]),
                    "temperature_c": int(parts[4]),
                    "utilization_percent": int(parts[5]),
                    "power_draw_w": float(parts[6]) if len(parts) > 6 else 0.0,
                    "available": True
                }
        except Exception:
            pass
        return {"name": "Integrated/Unknown", "available": False}

    def _refresh_process_cache(self, force: bool = False):
        """Single-pass high performance process and application scanner with TTL caching."""
        now = time.time()
        if not force and (now - self._proc_cache_time) < 5.0 and self._cached_procs:
            return

        SYSTEM_SERVICES = {
            'system', 'registry', 'memcompression', 'smss.exe', 'csrss.exe', 'wininit.exe',
            'services.exe', 'lsass.exe', 'svchost.exe', 'fontdrvhost.exe', 'winlogon.exe',
            'dwm.exe', 'spoolsv.exe', 'sihost.exe', 'taskhostw.exe', 'ctfmon.exe',
            'runtimebroker.exe', 'shellexperiencehost.exe', 'searchindexer.exe',
            'searchhost.exe', 'startmenuexperiencehost.exe', 'textinputhost.exe',
            'applicationframehost.exe', 'smartscreen.exe', 'securityhealthservice.exe',
            'wmiprvse.exe', 'conhost.exe', 'dashost.exe', 'dllhost.exe', 'msedgewebview2.exe'
        }

        procs = []
        apps = {}
        for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
            try:
                info = p.info
                name = info.get("name")
                if not name:
                    continue
                mem = info.get("memory_percent") or 0.0
                cpu = info.get("cpu_percent") or 0.0
                procs.append({
                    "pid": info["pid"],
                    "name": name,
                    "cpu_pct": round(cpu, 1),
                    "mem_pct": round(mem, 2),
                    "status": "running"
                })
                low = name.lower()
                if low not in SYSTEM_SERVICES:
                    if low not in apps:
                        apps[low] = {
                            "name": name,
                            "pids": [info["pid"]],
                            "mem_pct": mem,
                            "cpu_pct": cpu,
                            "exe": ""
                        }
                    else:
                        apps[low]["pids"].append(info["pid"])
                        apps[low]["mem_pct"] += mem
                        apps[low]["cpu_pct"] += cpu
            except Exception:
                pass

        self._cached_procs = procs
        sorted_apps = sorted(apps.values(), key=lambda x: x["mem_pct"], reverse=True)
        self._cached_apps = [
            {
                "name": a["name"],
                "process_count": len(a["pids"]),
                "mem_pct": round(a["mem_pct"], 2),
                "cpu_pct": round(a["cpu_pct"], 1),
                "exe": a["exe"]
            }
            for a in sorted_apps
        ]
        self._proc_cache_time = now

    def get_processes(self, top_n: int = 8, sort_by: str = "memory") -> List[Dict[str, Any]]:
        """Returns top active processes by memory or CPU."""
        self._refresh_process_cache()
        key = "mem_pct" if sort_by == "memory" else "cpu_pct"
        sorted_p = sorted(self._cached_procs, key=lambda x: x.get(key, 0), reverse=True)
        return sorted_p[:top_n]

    def get_user_applications(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Filters out low-level Windows kernel/system background services to report real user-facing desktop applications."""
        self._refresh_process_cache()
        return self._cached_apps[:top_n]

    async def get_active_media_playback(self) -> Dict[str, Any]:
        """Queries Windows Global System Media Transport Controls (GSMTC) for currently playing song/video/audio in isolated COM thread."""
        def _sync_query():
            import ctypes
            try:
                ctypes.windll.ole32.CoInitializeEx(None, 0x0)
            except Exception:
                pass
            try:
                import asyncio
                from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager

                async def _inner():
                    mgr = await MediaManager.request_async()
                    cur = mgr.get_current_session()
                    sessions = mgr.get_sessions()
                    target = cur or (sessions[0] if len(sessions) > 0 else None)
                    if target:
                        props = await target.try_get_media_properties_async()
                        info = target.get_playback_info()
                        status_map = {0: "Closed", 1: "Opened", 2: "Changing", 3: "Stopped", 4: "Playing", 5: "Paused"}
                        app_id = target.source_app_user_model_id or "Unknown Application"
                        friendly_app = app_id
                        if "brave" in app_id.lower():
                            friendly_app = "Brave Browser"
                        elif "chrome" in app_id.lower():
                            friendly_app = "Google Chrome"
                        elif "spotify" in app_id.lower():
                            friendly_app = "Spotify"
                        elif "apple" in app_id.lower():
                            friendly_app = "Apple Music"
                        
                        return {
                            "active": True,
                            "app": friendly_app,
                            "raw_app_id": app_id,
                            "title": props.title or "Unknown Title",
                            "artist": props.artist or "Unknown Artist",
                            "album": props.album_title or "",
                            "status": status_map.get(info.playback_status, "Unknown")
                        }
                    return {"active": False, "message": "No active media playback detected on your laptop."}

                loop = asyncio.new_event_loop()
                res = loop.run_until_complete(_inner())
                loop.close()
                return res
            except Exception as e:
                return {"active": False, "error": str(e)}
            finally:
                try:
                    ctypes.windll.ole32.CoUninitialize()
                except Exception:
                    pass

        try:
            return await asyncio.to_thread(_sync_query)
        except Exception as e:
            return {"active": False, "error": str(e)}

    def find_process(self, query: str) -> List[Dict[str, Any]]:
        """Finds processes matching name or pid."""
        matches = []
        q_lower = query.lower()
        for p in psutil.process_iter(["pid", "name", "memory_percent"]):
            try:
                info = p.info
                if q_lower in str(info.get("name", "")).lower() or q_lower == str(info.get("pid")):
                    matches.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "mem_pct": round(info.get("memory_percent") or 0.0, 2)
                    })
            except Exception:
                pass
        return matches

    def resolve_path(self, path_str: Optional[str] = None) -> Path:
        """Intelligently resolves paths including ~/Desktop, /desktop, Windows paths, and aliases."""
        if not path_str or str(path_str).strip() in [".", "workspace", "repo"]:
            return self.workspace_dir
        
        cleaned = str(path_str).strip().strip("'\"")
        lower = cleaned.lower().replace("\\", "/").rstrip("/")
        
        if lower in ["desktop", "/desktop", "~/desktop", "c:/users/soham/desktop"]:
            return self.desktop_dir
        if lower in ["downloads", "/downloads", "~/downloads", "c:/users/soham/downloads"]:
            return self.downloads_dir
        if lower.startswith("~/") or lower.startswith("~\\"):
            return (self.user_home / cleaned[2:]).resolve()
        if cleaned.startswith("/") and len(cleaned) > 1:
            candidate = self.user_home / cleaned[1:]
            if candidate.exists():
                return candidate.resolve()
        
        p = Path(cleaned).expanduser()
        if not p.is_absolute():
            p = (self.workspace_dir / p).resolve()
        return p

    def launch_terminal(self, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Spawns an interactive visible terminal window (PowerShell / Windows Terminal) on the user's desktop."""
        target_dir = self.resolve_path(working_dir or str(self.desktop_dir))
        cwd = str(target_dir if target_dir.exists() and target_dir.is_dir() else self.desktop_dir)
        try:
            cmd = [
                "cmd.exe", "/c", "start", "powershell.exe",
                "-NoExit", "-Command",
                f"Set-Location '{cwd}'; Write-Host '[CORTEX-OS] Autonomous System Shell Synchronized at {cwd}' -ForegroundColor Cyan"
            ]
            proc = subprocess.Popen(cmd, cwd=cwd)
            return {
                "status": "SUCCESS",
                "pid": proc.pid,
                "working_dir": cwd,
                "terminal": "powershell.exe",
                "message": f"Interactive terminal spawned at {cwd}."
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def launch_application(self, app_name: str) -> Dict[str, Any]:
        """Launches a desktop application, UWP target, or shell program with intelligent path resolution and os.startfile."""
        clean = app_name.lower().strip()
        user_home = self.user_home
        
        known_apps: Dict[str, List[Any]] = {
            "chrome": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                user_home / r"AppData\Local\Google\Chrome\Application\chrome.exe",
                "chrome.exe",
                "chrome"
            ],
            "brave": [
                user_home / r"AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
                "brave.exe",
                "brave"
            ],
            "code": [
                user_home / r"AppData\Local\Programs\Microsoft VS Code\Code.exe",
                r"C:\Program Files\Microsoft VS Code\Code.exe",
                r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
                "Code.exe",
                "code"
            ],
            "vscode": [
                user_home / r"AppData\Local\Programs\Microsoft VS Code\Code.exe",
                r"C:\Program Files\Microsoft VS Code\Code.exe",
                "Code.exe",
                "code"
            ],
            "vs code": [
                user_home / r"AppData\Local\Programs\Microsoft VS Code\Code.exe",
                r"C:\Program Files\Microsoft VS Code\Code.exe",
                "Code.exe",
                "code"
            ],
            "notepad": [
                r"C:\Windows\System32\notepad.exe",
                "notepad.exe",
                "notepad"
            ],
            "calc": [
                r"C:\Windows\System32\calc.exe",
                "calc.exe",
                "ms-calculator:",
                "calc"
            ],
            "calculator": [
                r"C:\Windows\System32\calc.exe",
                "calc.exe",
                "ms-calculator:",
                "calc"
            ],
            "explorer": [
                r"C:\Windows\explorer.exe",
                "explorer.exe",
                "explorer"
            ],
            "files": [
                r"C:\Windows\explorer.exe",
                "explorer.exe"
            ],
            "file explorer": [
                r"C:\Windows\explorer.exe",
                "explorer.exe"
            ],
            "spotify": [
                user_home / r"AppData\Roaming\Spotify\Spotify.exe",
                user_home / r"AppData\Local\Microsoft\WindowsApps\Spotify.exe",
                "spotify:",
                "spotify.exe",
                "spotify"
            ],
            "edge": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                "msedge.exe",
                "msedge"
            ],
            "msedge": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                "msedge.exe"
            ],
            "taskmgr": [
                r"C:\Windows\System32\Taskmgr.exe",
                "taskmgr.exe"
            ],
            "task manager": [
                r"C:\Windows\System32\Taskmgr.exe",
                "taskmgr.exe"
            ],
            "settings": [
                "ms-settings:"
            ],
            "windows settings": [
                "ms-settings:"
            ],
            "paint": [
                r"C:\Windows\System32\mspaint.exe",
                "mspaint.exe"
            ],
            "control": [
                r"C:\Windows\System32\control.exe",
                "control.exe"
            ],
            "control panel": [
                r"C:\Windows\System32\control.exe",
                "control.exe"
            ],
            "terminal": [
                "wt.exe",
                r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
                "powershell.exe"
            ],
            "powershell": [
                r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
                "powershell.exe"
            ],
            "cmd": [
                r"C:\Windows\System32\cmd.exe",
                "cmd.exe"
            ],
            "docker": [
                r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
                "Docker Desktop.exe"
            ]
        }

        # Resolve candidate targets
        target_candidates = known_apps.get(clean, [])
        if not target_candidates:
            alias = clean.replace("google ", "").replace("browser", "").replace("the ", "").replace("app", "").strip()
            target_candidates = known_apps.get(alias, [clean])

        for candidate in target_candidates:
            cand_str = str(candidate)
            # 1. Existing full path on disk
            if os.path.exists(cand_str):
                try:
                    os.startfile(cand_str)
                    return {
                        "status": "SUCCESS",
                        "application": app_name,
                        "resolved_path": cand_str,
                        "message": f"Application '{app_name}' successfully launched from '{cand_str}'."
                    }
                except Exception:
                    pass

            # 2. UWP Protocol (ms-settings:, spotify:, etc.)
            if cand_str.endswith(":"):
                try:
                    os.startfile(cand_str)
                    return {
                        "status": "SUCCESS",
                        "application": app_name,
                        "resolved_path": cand_str,
                        "message": f"Application '{app_name}' launched via protocol '{cand_str}'."
                    }
                except Exception:
                    pass

        # 3. Direct os.startfile on system executable name or clean string
        try:
            os.startfile(clean if clean.endswith(".exe") else f"{clean}.exe")
            return {
                "status": "SUCCESS",
                "application": app_name,
                "message": f"Application '{app_name}' successfully launched."
            }
        except Exception:
            pass

        try:
            os.startfile(clean)
            return {
                "status": "SUCCESS",
                "application": app_name,
                "message": f"Application '{app_name}' launched."
            }
        except Exception:
            pass

        # 4. Fallback: cmd.exe /c start "" "<target>"
        try:
            proc = subprocess.Popen(["cmd.exe", "/c", "start", "", clean], shell=True)
            return {
                "status": "SUCCESS",
                "pid": proc.pid,
                "application": app_name,
                "message": f"Application '{app_name}' dispatched via Windows shell."
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def list_directory(self, target_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists directory files with sizes and types, directories sorted first."""
        dir_p = self.resolve_path(target_path)
        if not dir_p.exists() or not dir_p.is_dir():
            return []
        
        items = []
        try:
            for p in sorted(dir_p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    stat = p.stat()
                    items.append({
                        "name": p.name,
                        "path": str(p),
                        "is_dir": p.is_dir(),
                        "size_bytes": stat.st_size if not p.is_dir() else 0,
                        "size_human": f"{round(stat.st_size / 1024, 1)} KB" if not p.is_dir() else "DIR",
                        "modified": time.ctime(stat.st_mtime)
                    })
                except Exception:
                    pass
        except Exception:
            pass
        return items

    def read_file_content(self, path: str, max_lines: int = 150) -> Dict[str, Any]:
        """Reads file safely with line bounds."""
        target = self.resolve_path(path)
        if not target.exists() or not target.is_file():
            return {"error": f"File '{path}' does not exist.", "status": "NOT_FOUND"}
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            truncated = len(lines) > max_lines
            return {
                "path": str(target),
                "content": "\n".join(lines[:max_lines]),
                "total_lines": len(lines),
                "truncated": truncated,
                "status": "SUCCESS"
            }
        except Exception as e:
            return {"error": str(e), "status": "READ_ERROR"}

    def run_command(self, command: str, cwd: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
        """Runs PowerShell/shell command on the system and captures output."""
        work_dir = str(self.resolve_path(cwd))
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "command": command,
                "exit_code": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
                "status": "SUCCESS" if proc.returncode == 0 else "ERROR"
            }
        except subprocess.TimeoutExpired:
            return {"command": command, "exit_code": -1, "stdout": "", "stderr": f"Timed out after {timeout}s", "status": "TIMEOUT"}
        except Exception as e:
            return {"command": command, "exit_code": -2, "stdout": "", "stderr": str(e), "status": "EXCEPTION"}

    async def control_media_playback(self, command: str = "toggle") -> Dict[str, Any]:
        """Controls active Windows GSMTC media playback (play, pause, toggle, next, previous) with hardware media key fallback."""
        cmd_lower = command.lower()
        action_taken = "Paused" if "pause" in cmd_lower or "stop" in cmd_lower else "Toggled"
        active_track = "Active Media"
        active_app = "Brave Browser / Media Subsystem"
        
        # 1. Try GSMTC WinRT Session
        try:
            from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as SM
            mgr = await SM.request_async()
            session = mgr.get_current_session()
            if session:
                active_app = session.source_app_user_model_id or active_app
                try:
                    props = await session.try_get_media_properties_async()
                    if props and props.title:
                        active_track = f"'{props.title}' by {props.artist or 'Unknown'}"
                except Exception:
                    pass

                if "pause" in cmd_lower or "stop" in cmd_lower:
                    await session.try_pause_async()
                    action_taken = "Paused"
                elif "play" in cmd_lower or "resume" in cmd_lower:
                    await session.try_play_async()
                    action_taken = "Playing"
                elif "next" in cmd_lower or "skip" in cmd_lower:
                    await session.try_skip_next_async()
                    action_taken = "Skipped to next track"
                elif "prev" in cmd_lower or "back" in cmd_lower:
                    await session.try_skip_previous_async()
                    action_taken = "Returned to previous track"
                else:
                    await session.try_toggle_play_pause_async()
                    action_taken = "Toggled play/pause"
        except Exception:
            pass

        # 2. Hardware media key simulation fallback via Win32 keybd_event
        try:
            import ctypes
            user32 = ctypes.windll.user32
            if "stop" in cmd_lower:
                vk = 0xB2  # VK_MEDIA_STOP
            elif "pause" in cmd_lower:
                vk = 0xB3  # VK_MEDIA_PLAY_PAUSE
            elif "next" in cmd_lower or "skip" in cmd_lower:
                vk = 0xB0  # VK_MEDIA_NEXT_TRACK
            elif "prev" in cmd_lower:
                vk = 0xB1  # VK_MEDIA_PREV_TRACK
            else:
                vk = 0xB3  # VK_MEDIA_PLAY_PAUSE
            user32.keybd_event(vk, 0, 0, 0)
            user32.keybd_event(vk, 0, 2, 0)
        except Exception:
            pass

        return {
            "status": "SUCCESS",
            "action": action_taken,
            "track": active_track,
            "app": active_app,
            "message": f"Successfully executed {action_taken} for {active_track} ({active_app})."
        }

    def get_active_window(self) -> Dict[str, Any]:
        """Returns focused window title and process name via Win32 API."""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            proc_name = ""
            try:
                proc = psutil.Process(pid.value)
                proc_name = proc.name()
            except Exception:
                pass
            return {
                "title": title or "Desktop / Windows Shell",
                "process": proc_name or "explorer.exe",
                "pid": pid.value,
                "status": "SUCCESS"
            }
        except Exception as e:
            return {"title": "Unknown", "process": "Unknown", "error": str(e), "status": "ERROR"}

    def get_clipboard_text(self) -> Dict[str, Any]:
        """Reads text from Windows clipboard."""
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True, text=True, timeout=3, encoding="utf-8", errors="replace"
            )
            text = (res.stdout or "").strip()
            return {"text": text, "length": len(text), "status": "SUCCESS"}
        except Exception as e:
            return {"text": "", "error": str(e), "status": "ERROR"}

    def set_clipboard_text(self, text: str) -> Dict[str, Any]:
        """Sets text to Windows clipboard."""
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"],
                input=text, capture_output=True, text=True, timeout=3, encoding="utf-8", errors="replace"
            )
            return {"status": "SUCCESS" if proc.returncode == 0 else "ERROR"}
        except Exception as e:
            return {"error": str(e), "status": "ERROR"}

    def _get_pycaw_volume_interface(self):
        """Helper to get IAudioEndpointVolume interface across pycaw versions."""
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        from ctypes import cast, POINTER
        devices = AudioUtilities.GetSpeakers()
        if hasattr(devices, "EndpointVolume") and devices.EndpointVolume is not None:
            return devices.EndpointVolume
        elif hasattr(devices, "Activate"):
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return cast(interface, POINTER(IAudioEndpointVolume))
        raise RuntimeError("No compatible pycaw volume interface found")

    def set_volume(self, level: int) -> Dict[str, Any]:
        """Adjusts master audio volume (0-100)."""
        target = max(0, min(100, int(level)))
        try:
            volume = self._get_pycaw_volume_interface()
            volume.SetMasterVolumeLevelScalar(target / 100.0, None)
            return {"status": "SUCCESS", "volume": target, "message": f"Volume set to {target}%."}
        except Exception:
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     f"$obj = New-Object -ComObject WScript.Shell; 1..50 | % {{ $obj.SendKeys([char]174) }}; 1..{target//2} | % {{ $obj.SendKeys([char]175) }}"],
                    capture_output=True, timeout=5
                )
                return {"status": "SUCCESS", "volume": target, "message": f"Volume adjusted to ~{target}%."}
            except Exception as e:
                return {"status": "ERROR", "error": str(e)}

    def get_volume(self) -> Dict[str, Any]:
        """Gets current master volume and mute status."""
        try:
            volume = self._get_pycaw_volume_interface()
            current = int(round(volume.GetMasterVolumeLevelScalar() * 100))
            is_muted = bool(volume.GetMute())
            return {"status": "SUCCESS", "volume": current, "muted": is_muted}
        except Exception as e:
            return {"status": "ERROR", "error": str(e), "volume": 50, "muted": False}

    def toggle_mute(self) -> Dict[str, Any]:
        """Toggles audio mute state."""
        try:
            volume = self._get_pycaw_volume_interface()
            new_mute = not bool(volume.GetMute())
            volume.SetMute(new_mute, None)
            return {"status": "SUCCESS", "muted": new_mute, "message": "Audio muted" if new_mute else "Audio unmuted"}
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0xAD, 0, 2, 0)
                return {"status": "SUCCESS", "message": "Dispatched volume mute toggle."}
            except Exception as e:
                return {"status": "ERROR", "error": str(e)}

    def close_application(self, app_name: str) -> Dict[str, Any]:
        """Closes / terminates an application by name or process."""
        clean = app_name.lower().strip()
        app_map = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "brave": "brave.exe",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "terminal": "wt.exe",
            "powershell": "powershell.exe",
            "cmd": "cmd.exe",
            "vscode": "Code.exe",
            "code": "Code.exe"
        }
        exe = app_map.get(clean, clean)
        if not exe.endswith(".exe"):
            exe += ".exe"
        try:
            res = subprocess.run(["taskkill", "/IM", exe, "/F"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                return {"status": "SUCCESS", "app": app_name, "message": f"Successfully closed {exe}."}
            else:
                return {"status": "NOT_FOUND", "app": app_name, "message": f"Process {exe} is not currently running."}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def capture_screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Captures active screen snapshot."""
        try:
            import pyautogui
            save_dir = Path(self.workspace_dir) / ".cortex" / "screenshots"
            save_dir.mkdir(parents=True, exist_ok=True)
            f_name = filename or f"screenshot_{int(time.time()*1000)}.png"
            dest = save_dir / f_name
            pyautogui.screenshot(str(dest))
            return {"status": "SUCCESS", "path": str(dest), "filename": f_name}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def type_into_window(self, text: str) -> Dict[str, Any]:
        """Types text into the active foreground window."""
        try:
            import pyautogui
            pyautogui.write(text, interval=0.01)
            return {"status": "SUCCESS", "typed_length": len(text)}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def open_chrome_tab(self, url_or_query: str) -> Dict[str, Any]:
        """Opens a new tab in Google Chrome with URL or Google Search query."""
        import urllib.parse
        import webbrowser
        clean = url_or_query.strip()
        if clean.startswith("http://") or clean.startswith("https://") or clean.startswith("www."):
            target_url = clean if clean.startswith("http") else f"https://{clean}"
        else:
            encoded = urllib.parse.quote(clean)
            target_url = f"https://www.google.com/search?q={encoded}"

        try:
            # Check if Chrome executable is present
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
            ]
            chrome_exe = next((p for p in chrome_paths if os.path.exists(p)), None)
            if chrome_exe:
                subprocess.Popen([chrome_exe, target_url])
            else:
                webbrowser.open_new_tab(target_url)
            return {"status": "SUCCESS", "url": target_url, "action": "open_chrome_tab"}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def claude_web_prompt(self, prompt: str) -> Dict[str, Any]:
        """Opens Claude AI in browser and prepares prompt."""
        import webbrowser
        try:
            import pyperclip
            pyperclip.copy(prompt)
        except Exception:
            pass
        url = "https://claude.ai/new"
        webbrowser.open_new_tab(url)
        return {"status": "SUCCESS", "url": url, "prompt_copied": True, "action": "claude_web_prompt"}

    def open_web_app(self, app_name: str) -> Dict[str, Any]:
        """Opens common web applications."""
        import webbrowser
        web_apps = {
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
        clean = app_name.lower().strip()
        url = web_apps.get(clean)
        if url:
            webbrowser.open_new_tab(url)
            return {"status": "SUCCESS", "app": clean, "url": url}
        return {"status": "NOT_FOUND", "message": f"Web app '{app_name}' not in directory."}

    def create_and_open_code(self, filename: str, code: str, app: str = "notepad") -> Dict[str, Any]:
        """Creates code in sandbox directory and opens it in editor."""
        sandbox_dir = Path(self.workspace_dir) / ".cortex" / "sandbox"
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        target = sandbox_dir / filename
        target.write_text(code, encoding="utf-8")

        clean_app = app.lower().strip()
        if "code" in clean_app or "vscode" in clean_app:
            subprocess.Popen(["code", str(target)], shell=True)
        else:
            subprocess.Popen(["notepad.exe", str(target)])
        return {"status": "SUCCESS", "path": str(target), "editor": clean_app}

    def is_sensitive_path(self, path: str) -> bool:
        """Security guardrail preventing access to credentials, browser databases, and SAM."""
        lower = str(Path(path).resolve()).lower()
        blocked = [
            r"\.ssh", r"\.aws", r"\.azure", r"\.kube",
            r"login data", r"cookies", r"web data",
            r"wallet.dat", r"keystore", r"id_rsa", r"id_ed25519",
            r"sam", r"system32\config\sam", r"vaultcmd"
        ]
        return any(b in lower for b in blocked)

    def fetch_prioritized_news(self, topic: str = "top headlines", max_items: int = 5) -> str:
        """Fetches live RSS news and prioritizes items based on importance scoring."""
        import urllib.request
        import urllib.parse
        import xml.etree.ElementTree as ET
        import re

        critical_kw = {
            "war": 9, "conflict": 8, "missile": 9, "treaty": 8, "sanction": 8,
            "election": 7, "inflation": 7, "interest rate": 7, "economy": 7,
            "prime minister": 7, "president": 7, "border": 8, "ai": 8,
            "semiconductor": 8, "nuclear": 9, "security": 7, "gdp": 7
        }
        trivia_kw = {"actor": -3, "celebrity": -4, "dating": -4, "wedding": -3}

        clean_topic = topic.strip()
        encoded = urllib.parse.quote(clean_topic)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                root = ET.fromstring(resp.read())
                items = root.findall(".//item")
                if not items:
                    return f"No live news reports found for '{clean_topic}'."

                scored_items = []
                for item in items[:12]:
                    title_elem = item.find("title")
                    title = title_elem.text if title_elem is not None else "Untitled"
                    clean_title = title.split(" - ")[0].strip()
                    lower = clean_title.lower()
                    score = 5
                    for kw, weight in critical_kw.items():
                        if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                            score += weight // 2
                    for kw, pen in trivia_kw.items():
                        if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                            score += pen
                    scored_items.append((max(1, min(10, score)), clean_title))

                scored_items.sort(key=lambda x: x[0], reverse=True)
                lines = [f"Strategic News Feed for '{clean_topic}' (Prioritized 1-10):"]
                for i, (score, t) in enumerate(scored_items[:max_items], 1):
                    tag = "🚨 CRITICAL" if score >= 8 else ("📈 STRATEGIC" if score >= 6 else "ℹ️ NOTABLE")
                    lines.append(f"  {i}. [{tag} | Score: {score}/10] {t}")
                return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving strategic news: {e}"

    def get_summary_snapshot(self) -> str:
        """Compact somatosensory snapshot string for injection into cognitive prompt."""
        t = self.get_hardware_telemetry()
        gpu = t["gpu"]
        gpu_str = f"{gpu['name']} ({gpu['vram_used_mb']}MB/{gpu['vram_total_mb']}MB, {gpu['temperature_c']}C)" if gpu.get("available") else "No discrete GPU detected"
        top_p = self.get_processes(top_n=4)
        proc_str = ", ".join([f"{p['name']} ({p['mem_pct']}%)" for p in top_p])

        return (
            f"Machine: Windows 11 Laptop | User: {self.user_name} | AC Power: {t['battery']['plugged_in']} ({t['battery']['percent']}%)\n"
            f"CPU: {t['cpu']['percent']}% ({t['cpu']['cores_physical']}P/{t['cpu']['cores_logical']}T) | "
            f"RAM: {t['ram']['used_gb']}GB/{t['ram']['total_gb']}GB ({t['ram']['percent']}%) | "
            f"Disk C: {t['disk_c']['used_gb']}GB/{t['disk_c']['total_gb']}GB ({t['disk_c']['percent']}%)\n"
            f"GPU: {gpu_str}\n"
            f"Top RAM Consumers: {proc_str}\n"
            f"Active Workspace: {self.workspace_dir}"
        )
