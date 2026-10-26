import os
import sys
import platform
import subprocess
import socket
import time
import signal
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

try:
    import psutil
except ImportError:
    psutil = None

# Windows registry access (available natively on Windows)
if sys.platform == "win32":
    try:
        import winreg
    except ImportError:
        winreg = None
else:
    winreg = None


class ServiceManager:
    """Cross-platform autonomous background daemon and OS boot autostart manager.
    
    Supports:
      - Windows 10/11: User Startup Registry (HKCU Run) & Startup Folder Headless VBScript
      - Linux: systemd user units (~/.config/systemd/user/cortexos.service) & XDG autostart
      - macOS (Darwin): launchd LaunchAgents (~/Library/LaunchAgents/com.cortexos.daemon.plist)
      - Universal LAN Network Binding: Binds to 0.0.0.0 and surfaces local + network IPs.
    """

    SERVICE_NAME = "CortexOS_Daemon"
    SERVICE_LABEL = "com.cortexos.daemon"

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path(__file__).resolve().parent.parent.parent
        self.os_type = platform.system().lower()  # 'windows', 'linux', 'darwin'
        
        # Locate python & pythonw executables
        self.python_exe = Path(sys.executable).resolve()
        if self.os_type == "windows":
            # Prefer pythonw.exe in the same directory to suppress console window popup
            pythonw = self.python_exe.parent / "pythonw.exe"
            self.daemon_python = pythonw if pythonw.exists() else self.python_exe
        else:
            self.daemon_python = self.python_exe

        self.server_script = (self.workspace_root / "cortex" / "server.py").resolve()
        
        # Runtime states and logs
        self.cortex_dir = self.workspace_root / ".cortex"
        self.logs_dir = self.cortex_dir / "logs"
        self.pid_file = self.cortex_dir / "daemon.pid"
        self.log_file = self.logs_dir / "daemon.log"

    def ensure_directories(self) -> None:
        """Ensures that .cortex/ and .cortex/logs directories exist."""
        self.cortex_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    # ==================== NETWORK & IP DISCOVERY ====================

    def get_primary_lan_ip(self) -> str:
        """Determines the primary local network IPv4 address accessible by other devices."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Connecting to a public UDP address does not send packets, but routes through the primary network adapter
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "127.0.0.1"

    def get_network_info(self, port: Optional[int] = None) -> Dict[str, Any]:
        """Returns comprehensive network binding and endpoint information."""
        active_port = port or int(os.environ.get("CORTEX_PORT", "8000"))
        active_host = os.environ.get("CORTEX_HOST", "0.0.0.0")
        primary_ip = self.get_primary_lan_ip()
        hostname = socket.gethostname()

        all_ips = ["127.0.0.1"]
        try:
            _, _, host_ips = socket.gethostbyname_ex(hostname)
            for ip in host_ips:
                if ip not in all_ips and not ip.startswith("127."):
                    all_ips.append(ip)
        except Exception:
            if primary_ip not in all_ips:
                all_ips.append(primary_ip)

        return {
            "hostname": hostname,
            "bind_host": active_host,
            "port": active_port,
            "primary_ip": primary_ip,
            "all_ips": all_ips,
            "local_url": f"http://127.0.0.1:{active_port}",
            "network_url": f"http://{primary_ip}:{active_port}",
            "accessible_on_lan": active_host in ["0.0.0.0", "::"],
            "platform": platform.platform()
        }

    # ==================== DAEMON PROCESS RUNTIME ====================

    def is_running(self, port: int = 8000) -> Tuple[bool, Optional[int]]:
        """Checks if the CortexOS daemon is actively running via PID file or socket check."""
        # 1. Check PID file
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text(encoding="utf-8").strip())
                if psutil and psutil.pid_exists(pid):
                    proc = psutil.Process(pid)
                    if proc.is_running() and "python" in proc.name().lower():
                        return True, pid
                elif not psutil:
                    try:
                        os.kill(pid, 0)
                        return True, pid
                    except OSError:
                        pass
            except Exception:
                pass

        # 2. Check if port is actively listening
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                try:
                    s.connect(("127.0.0.1", port))
                    found_pid = None
                    if psutil:
                        try:
                            for conn in psutil.net_connections(kind="inet"):
                                if conn.laddr and conn.laddr.port == port and conn.pid:
                                    found_pid = conn.pid
                                    break
                        except Exception:
                            pass
                    return True, found_pid
                except (socket.timeout, OSError):
                    pass
        except Exception:
            pass

        return False, None

    def start_daemon(self, host: str = "0.0.0.0", port: int = 8000) -> Dict[str, Any]:
        """Spawns the CortexOS background daemon detached from the current terminal."""
        running, pid = self.is_running(port=port)
        if running:
            net = self.get_network_info(port=port)
            return {
                "status": "ALREADY_RUNNING",
                "pid": pid,
                "message": f"CortexOS daemon is already active on PID {pid}.",
                "local_url": net["local_url"],
                "network_url": net["network_url"]
            }

        self.ensure_directories()
        env = os.environ.copy()
        env["CORTEX_HOST"] = host
        env["CORTEX_PORT"] = str(port)
        env["PYTHONUNBUFFERED"] = "1"

        log_out = open(self.log_file, "a", encoding="utf-8", buffering=1)

        cmd = [str(self.daemon_python), str(self.server_script)]

        if self.os_type == "windows":
            # Windows detached background flags
            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            proc = subprocess.Popen(
                cmd,
                cwd=str(self.workspace_root),
                env=env,
                stdout=log_out,
                stderr=subprocess.STDOUT,
                creationflags=creationflags,
                close_fds=False
            )
        else:
            # POSIX detached daemon
            proc = subprocess.Popen(
                cmd,
                cwd=str(self.workspace_root),
                env=env,
                stdout=log_out,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True
            )

        # Write PID file
        self.pid_file.write_text(str(proc.pid), encoding="utf-8")

        # Allow daemon 1.5 seconds to bind socket
        time.sleep(1.5)
        net = self.get_network_info(port=port)

        return {
            "status": "SUCCESS",
            "pid": proc.pid,
            "executable": str(self.daemon_python),
            "host": host,
            "port": port,
            "local_url": net["local_url"],
            "network_url": net["network_url"],
            "log_file": str(self.log_file),
            "message": f"CortexOS daemon started successfully (PID: {proc.pid})."
        }

    def stop_daemon(self, port: int = 8000) -> Dict[str, Any]:
        """Terminates the running CortexOS background daemon."""
        running, pid = self.is_running(port=port)
        if not running and not self.pid_file.exists():
            return {"status": "NOT_RUNNING", "message": "No active CortexOS daemon detected."}

        terminated = False
        target_pid = pid

        if not target_pid and self.pid_file.exists():
            try:
                target_pid = int(self.pid_file.read_text(encoding="utf-8").strip())
            except Exception:
                target_pid = None

        if target_pid:
            try:
                if psutil and psutil.pid_exists(target_pid):
                    p = psutil.Process(target_pid)
                    # Terminate children as well
                    for child in p.children(recursive=True):
                        try:
                            child.terminate()
                        except Exception:
                            pass
                    p.terminate()
                    gone, alive = psutil.wait_procs([p], timeout=3)
                    if alive:
                        for a in alive:
                            a.kill()
                    terminated = True
                else:
                    if self.os_type == "windows":
                        subprocess.run(["taskkill", "/F", "/PID", str(target_pid)], capture_output=True)
                    else:
                        os.kill(target_pid, signal.SIGTERM)
                    terminated = True
            except Exception as e:
                return {"status": "ERROR", "error": f"Failed to stop PID {target_pid}: {e}"}

        # Clear PID file
        if self.pid_file.exists():
            try:
                self.pid_file.unlink()
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "stopped_pid": target_pid,
            "message": f"CortexOS daemon (PID {target_pid}) stopped."
        }

    # ==================== OS AUTOSTART CONFIGURATION ====================

    def is_autostart_enabled(self) -> Dict[str, Any]:
        """Checks if CortexOS is configured to start up automatically on system boot / logon."""
        if self.os_type == "windows":
            return self._windows_is_autostart()
        elif self.os_type == "darwin":
            return self._darwin_is_autostart()
        elif self.os_type == "linux":
            return self._linux_is_autostart()
        return {"enabled": False, "platform": self.os_type, "method": "unsupported"}

    def install_autostart(self, host: str = "0.0.0.0", port: int = 8000) -> Dict[str, Any]:
        """Installs and enables automatic system background startup for the current operating system."""
        self.ensure_directories()
        if self.os_type == "windows":
            return self._windows_install_autostart(host=host, port=port)
        elif self.os_type == "darwin":
            return self._darwin_install_autostart(host=host, port=port)
        elif self.os_type == "linux":
            return self._linux_install_autostart(host=host, port=port)
        return {"status": "ERROR", "message": f"Unsupported platform: {self.os_type}"}

    def uninstall_autostart(self) -> Dict[str, Any]:
        """Removes automatic system background startup for the current operating system."""
        if self.os_type == "windows":
            return self._windows_uninstall_autostart()
        elif self.os_type == "darwin":
            return self._darwin_uninstall_autostart()
        elif self.os_type == "linux":
            return self._linux_uninstall_autostart()
        return {"status": "ERROR", "message": f"Unsupported platform: {self.os_type}"}

    def is_autostart_configured(self) -> bool:
        """Returns True if autostart is currently enabled."""
        return bool(self.is_autostart_enabled().get("enabled", False))

    def install(self, host: str = "0.0.0.0", port: int = 8000) -> bool:
        """Convenience method to install autostart, returning True on success."""
        res = self.install_autostart(host=host, port=port)
        return res.get("status") == "SUCCESS"

    def uninstall(self) -> bool:
        """Convenience method to uninstall autostart, returning True on success."""
        res = self.uninstall_autostart()
        return res.get("status") == "SUCCESS"

    # ------------------- Windows Implementation -------------------

    def _windows_is_autostart(self) -> Dict[str, Any]:
        reg_active = False
        startup_file_active = False

        # 1. Check HKCU Run registry
        if winreg:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ) as key:
                    winreg.QueryValueEx(key, self.SERVICE_NAME)
                    reg_active = True
            except (FileNotFoundError, OSError):
                reg_active = False

        # 2. Check Startup folder VBS
        appdata = os.environ.get("APPDATA")
        if appdata:
            startup_dir = Path(appdata) / r"Microsoft\Windows\Start Menu\Programs\Startup"
            vbs_file = startup_dir / "cortexos_daemon.vbs"
            startup_file_active = vbs_file.exists()

        enabled = reg_active or startup_file_active
        method = "registry+startup_folder" if (reg_active and startup_file_active) else ("registry" if reg_active else ("startup_folder" if startup_file_active else "none"))
        return {
            "enabled": enabled,
            "platform": "windows",
            "method": method,
            "registry_active": reg_active,
            "startup_folder_active": startup_file_active
        }

    def _windows_install_autostart(self, host: str, port: int) -> Dict[str, Any]:
        appdata = os.environ.get("APPDATA")
        installed_methods = []

        # 1. Create headless VBScript launcher in Startup folder
        if appdata:
            startup_dir = Path(appdata) / r"Microsoft\Windows\Start Menu\Programs\Startup"
            startup_dir.mkdir(parents=True, exist_ok=True)
            vbs_file = startup_dir / "cortexos_daemon.vbs"

            # VBScript executes pythonw.exe completely hidden (window style 0, no command prompt)
            vbs_content = (
                f'Set WshShell = CreateObject("WScript.Shell")\r\n'
                f'WshShell.CurrentDirectory = "{self.workspace_root}"\r\n'
                f'Set procEnv = WshShell.Environment("PROCESS")\r\n'
                f'procEnv("CORTEX_HOST") = "{host}"\r\n'
                f'procEnv("CORTEX_PORT") = "{port}"\r\n'
                f'WshShell.Run """{self.daemon_python}"" ""{self.server_script}""", 0, False\r\n'
            )
            vbs_file.write_text(vbs_content, encoding="utf-8")
            installed_methods.append("startup_folder_vbs")

        # 2. Register in HKCU Run Key for redundancy
        if winreg:
            try:
                run_cmd = f'"{self.daemon_python}" "{self.server_script}"'
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, self.SERVICE_NAME, 0, winreg.REG_SZ, run_cmd)
                installed_methods.append("hkcu_run_registry")
            except Exception as e:
                pass

        return {
            "status": "SUCCESS",
            "platform": "windows",
            "methods": installed_methods,
            "executable": str(self.daemon_python),
            "script": str(self.server_script),
            "host": host,
            "port": port,
            "message": "CortexOS successfully configured as Windows background daemon on startup (Headless VBS & User Registry)."
        }

    def _windows_uninstall_autostart(self) -> Dict[str, Any]:
        removed = []

        # 1. Remove from HKCU Run Key
        if winreg:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, self.SERVICE_NAME)
                    removed.append("hkcu_run_registry")
            except (FileNotFoundError, OSError):
                pass

        # 2. Remove VBS from Startup folder
        appdata = os.environ.get("APPDATA")
        if appdata:
            vbs_file = Path(appdata) / r"Microsoft\Windows\Start Menu\Programs\Startup\cortexos_daemon.vbs"
            if vbs_file.exists():
                try:
                    vbs_file.unlink()
                    removed.append("startup_folder_vbs")
                except Exception:
                    pass

        return {
            "status": "SUCCESS",
            "platform": "windows",
            "removed_methods": removed,
            "message": "CortexOS background startup removed from Windows."
        }

    # ------------------- Linux Implementation -------------------

    def _linux_is_autostart(self) -> Dict[str, Any]:
        home = Path.home()
        systemd_unit = home / ".config" / "systemd" / "user" / "cortexos.service"
        desktop_entry = home / ".config" / "autostart" / "cortexos.desktop"
        
        systemd_active = systemd_unit.exists()
        desktop_active = desktop_entry.exists()
        
        return {
            "enabled": systemd_active or desktop_active,
            "platform": "linux",
            "method": "systemd_user" if systemd_active else ("xdg_autostart" if desktop_active else "none")
        }

    def _linux_install_autostart(self, host: str, port: int) -> Dict[str, Any]:
        home = Path.home()
        systemd_dir = home / ".config" / "systemd" / "user"
        systemd_dir.mkdir(parents=True, exist_ok=True)
        unit_file = systemd_dir / "cortexos.service"

        unit_content = f"""[Unit]
Description=CortexOS Cognitive Operating System Daemon
After=network.target

[Service]
Type=simple
WorkingDirectory={self.workspace_root}
ExecStart={self.python_exe} {self.server_script}
Restart=always
RestartSec=5
Environment=CORTEX_HOST={host}
Environment=CORTEX_PORT={port}
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""
        unit_file.write_text(unit_content, encoding="utf-8")

        # Try enabling systemd service
        try:
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
            subprocess.run(["systemctl", "--user", "enable", "cortexos"], check=False)
        except Exception:
            pass

        # Fallback XDG autostart desktop entry
        autostart_dir = home / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = autostart_dir / "cortexos.desktop"
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=CortexOS Cognitive Daemon
Exec={self.python_exe} {self.server_script}
Path={self.workspace_root}
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
"""
        desktop_file.write_text(desktop_content, encoding="utf-8")

        return {
            "status": "SUCCESS",
            "platform": "linux",
            "systemd_unit": str(unit_file),
            "message": "CortexOS successfully configured as Linux user systemd service and XDG autostart."
        }

    def _linux_uninstall_autostart(self) -> Dict[str, Any]:
        home = Path.home()
        unit_file = home / ".config" / "systemd" / "user" / "cortexos.service"
        desktop_file = home / ".config" / "autostart" / "cortexos.desktop"

        try:
            subprocess.run(["systemctl", "--user", "disable", "cortexos"], check=False)
        except Exception:
            pass

        if unit_file.exists():
            unit_file.unlink()
        if desktop_file.exists():
            desktop_file.unlink()

        return {"status": "SUCCESS", "platform": "linux", "message": "CortexOS autostart removed from Linux."}

    # ------------------- macOS Implementation -------------------

    def _darwin_is_autostart(self) -> Dict[str, Any]:
        plist = Path.home() / "Library" / "LaunchAgents" / f"{self.SERVICE_LABEL}.plist"
        return {
            "enabled": plist.exists(),
            "platform": "darwin",
            "method": "launchd_agent" if plist.exists() else "none"
        }

    def _darwin_install_autostart(self, host: str, port: int) -> Dict[str, Any]:
        launch_dir = Path.home() / "Library" / "LaunchAgents"
        launch_dir.mkdir(parents=True, exist_ok=True)
        plist_file = launch_dir / f"{self.SERVICE_LABEL}.plist"

        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.SERVICE_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.python_exe}</string>
        <string>{self.server_script}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{self.workspace_root}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{self.log_file}</string>
    <key>StandardErrorPath</key>
    <string>{self.log_file}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>CORTEX_HOST</key>
        <string>{host}</string>
        <key>CORTEX_PORT</key>
        <string>{port}</string>
    </dict>
</dict>
</plist>
"""
        plist_file.write_text(plist_content, encoding="utf-8")
        try:
            subprocess.run(["launchctl", "load", "-w", str(plist_file)], check=False)
        except Exception:
            pass

        return {
            "status": "SUCCESS",
            "platform": "darwin",
            "plist": str(plist_file),
            "message": "CortexOS successfully configured as macOS launchd LaunchAgent."
        }

    def _darwin_uninstall_autostart(self) -> Dict[str, Any]:
        plist_file = Path.home() / "Library" / "LaunchAgents" / f"{self.SERVICE_LABEL}.plist"
        if plist_file.exists():
            try:
                subprocess.run(["launchctl", "unload", "-w", str(plist_file)], check=False)
            except Exception:
                pass
            plist_file.unlink()

        return {"status": "SUCCESS", "platform": "darwin", "message": "CortexOS autostart removed from macOS."}

    # ==================== STATUS SUMMARY ====================

    def status(self, port: int = 8000) -> Dict[str, Any]:
        """Returns a comprehensive snapshot of daemon running state, boot config, and network endpoints."""
        running, pid = self.is_running(port=port)
        autostart = self.is_autostart_enabled()
        net = self.get_network_info(port=port)

        mem_mb = 0.0
        cpu_pct = 0.0
        uptime = 0.0
        if running and pid and psutil and psutil.pid_exists(pid):
            try:
                p = psutil.Process(pid)
                mem_mb = round(p.memory_info().rss / (1024 * 1024), 2)
                cpu_pct = round(p.cpu_percent(interval=0.1), 1)
                uptime = round(time.time() - p.create_time(), 1)
            except Exception:
                pass

        return {
            "running": running,
            "pid": pid,
            "memory_mb": mem_mb,
            "cpu_percent": cpu_pct,
            "uptime_seconds": uptime,
            "autostart": autostart,
            "network": net,
            "platform": self.os_type,
            "executable": str(self.daemon_python),
            "script": str(self.server_script),
            "log_file": str(self.log_file)
        }


_GLOBAL_SERVICE_MANAGER: Optional[ServiceManager] = None


def get_service_manager() -> ServiceManager:
    """Returns singleton ServiceManager instance."""
    global _GLOBAL_SERVICE_MANAGER
    if _GLOBAL_SERVICE_MANAGER is None:
        _GLOBAL_SERVICE_MANAGER = ServiceManager()
    return _GLOBAL_SERVICE_MANAGER
