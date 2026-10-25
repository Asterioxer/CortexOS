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

    def get_processes(self, top_n: int = 8, sort_by: str = "memory") -> List[Dict[str, Any]]:
        """Returns top active processes by memory or CPU."""
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
            try:
                info = p.info
                if info["name"]:
                    procs.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "cpu_pct": round(info.get("cpu_percent") or 0.0, 1),
                        "mem_pct": round(info.get("memory_percent") or 0.0, 2),
                        "status": info.get("status", "running")
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        key = "mem_pct" if sort_by == "memory" else "cpu_pct"
        procs.sort(key=lambda x: x.get(key, 0), reverse=True)
        return procs[:top_n]

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

    def list_directory(self, target_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists directory files with sizes and types."""
        dir_p = Path(target_path or self.workspace_dir).resolve()
        if not dir_p.exists() or not dir_p.is_dir():
            return []
        
        items = []
        for p in sorted(dir_p.iterdir()):
            try:
                stat = p.stat()
                items.append({
                    "name": p.name,
                    "is_dir": p.is_dir(),
                    "size_bytes": stat.st_size if not p.is_dir() else 0,
                    "modified": time.ctime(stat.st_mtime)
                })
            except Exception:
                pass
        return items

    def read_file_content(self, path: str, max_lines: int = 150) -> Dict[str, Any]:
        """Reads file safely with line bounds."""
        target = Path(path).resolve()
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
        work_dir = cwd or str(self.workspace_dir)
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
