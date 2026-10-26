"""CortexOS Ground-Truth System Cartographer.

Deeply probes, maps, and continuously indexes the operator's actual machine hardware,
operating system kernel, installed toolchains, network interfaces, and filesystem workspaces.
Generates and maintains grounded Obsidian Vault notes in '05_System_State/' with exact
hardware specs, versions, paths, and detected environmental diffs.
"""

from __future__ import annotations

import os
import sys
import platform
import socket
import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import psutil


class SystemCartographer:
    """Probes host hardware, OS, toolchains, and filesystems; persists grounded notes to Obsidian."""

    COMMON_TOOLS = [
        "python", "node", "npm", "git", "go", "docker", "code", "winget",
        "javac", "java", "ffmpeg", "mpv", "cargo", "rustc", "adb"
    ]

    def __init__(self, vault_path: Optional[str | Path] = None):
        if vault_path is None:
            self.vault_path = Path(__file__).resolve().parent.parent.parent / "cortex_vault"
        else:
            self.vault_path = Path(vault_path)
        self.state_dir = self.vault_path / "05_System_State"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.vault_path.parent / ".cortex" / "cartography_cache.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    def probe_hardware(self) -> Dict[str, Any]:
        """Probe CPU, GPUs, RAM, and Disk storage."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # CPU info
        cpu_info = {
            "model": platform.processor() or "Unknown Processor",
            "physical_cores": psutil.cpu_count(logical=False) or 0,
            "logical_threads": psutil.cpu_count(logical=True) or 0,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "architecture": platform.machine()
        }

        # Query Windows CIM for detailed CPU name if available
        if sys.platform == "win32":
            try:
                cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
                if res.returncode == 0 and res.stdout.strip():
                    cpu_info["model"] = res.stdout.strip().splitlines()[0]
            except Exception:
                pass

        # GPUs info
        gpus: List[Dict[str, Any]] = []
        if sys.platform == "win32":
            try:
                cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, AdapterRAM | ConvertTo-Json"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if res.returncode == 0 and res.stdout.strip():
                    parsed = json.loads(res.stdout.strip())
                    if isinstance(parsed, dict):
                        parsed = [parsed]
                    for g in parsed:
                        raw_ram = g.get("AdapterRAM") or 0
                        vram_gb = round(raw_ram / (1024**3), 2) if raw_ram else 0.0
                        gpus.append({
                            "name": g.get("Name", "Unknown GPU"),
                            "driver_version": g.get("DriverVersion", "N/A"),
                            "vram_gb": vram_gb
                        })
            except Exception:
                pass

        # Disks info
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent_used": usage.percent
                })
            except Exception:
                continue

        return {
            "cpu": cpu_info,
            "gpus": gpus,
            "memory": {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "percent": mem.percent
            },
            "swap": {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "percent": swap.percent
            },
            "disks": disks
        }

    def probe_os_environment(self) -> Dict[str, Any]:
        """Probe Operating System, kernel build, user context, and shell environments."""
        user = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"
        home = str(Path.home())
        hostname = socket.gethostname()

        os_caption = f"{platform.system()} {platform.release()}"
        build_number = platform.version()

        if sys.platform == "win32":
            try:
                cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Caption"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
                if res.returncode == 0 and res.stdout.strip():
                    os_caption = res.stdout.strip().splitlines()[0]
            except Exception:
                pass

        env_vars_summary = {
            "USER": user,
            "HOSTNAME": hostname,
            "HOME": home,
            "SYSTEMROOT": os.environ.get("SystemRoot", "C:\\Windows"),
            "APPDATA": os.environ.get("APPDATA", ""),
            "LOCALAPPDATA": os.environ.get("LOCALAPPDATA", ""),
            "PROGRAMDATA": os.environ.get("ProgramData", "C:\\ProgramData"),
            "TEMP": os.environ.get("TEMP", ""),
        }

        # Check available shells
        shells = {}
        for sh in ["powershell", "pwsh", "cmd", "bash", "wsl"]:
            p = shutil.which(sh)
            if p:
                shells[sh] = p

        return {
            "caption": os_caption,
            "release": platform.release(),
            "version": build_number,
            "architecture": platform.machine(),
            "hostname": hostname,
            "user": user,
            "home": home,
            "shells": shells,
            "env_summary": env_vars_summary
        }

    def probe_toolchains(self) -> Dict[str, Any]:
        """Inspect compilers, runtimes, package managers, and developer utilities."""
        tools: Dict[str, Dict[str, str]] = {}
        for tool_name in self.COMMON_TOOLS:
            path = shutil.which(tool_name)
            if not path:
                continue

            version_str = "Installed"
            try:
                # Run version check with short timeout
                v_args = ["--version"]
                if tool_name in ["go"]:
                    v_args = ["version"]
                elif tool_name in ["ffmpeg"]:
                    v_args = ["-version"]

                res = subprocess.run([path] + v_args, capture_output=True, text=True, timeout=3)
                out = (res.stdout or res.stderr).strip().splitlines()
                if out:
                    version_str = out[0].strip()
            except Exception:
                pass

            tools[tool_name] = {
                "path": path,
                "version": version_str
            }

        return tools

    def probe_network(self) -> Dict[str, Any]:
        """Probe network interfaces, active local IP addresses, and routing."""
        interfaces: Dict[str, List[str]] = {}
        try:
            addrs = psutil.net_if_addrs()
            for iface_name, addr_list in addrs.items():
                ipv4s = [
                    a.address for a in addr_list
                    if a.family == socket.AF_INET and not a.address.startswith("127.")
                ]
                if ipv4s:
                    interfaces[iface_name] = ipv4s
        except Exception:
            pass

        # Identify primary LAN IP
        primary_ip = "127.0.0.1"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                primary_ip = s.getsockname()[0]
        except Exception:
            for iface, ips in interfaces.items():
                if "wi-fi" in iface.lower() or "ethernet" in iface.lower():
                    if ips:
                        primary_ip = ips[0]
                        break

        return {
            "primary_lan_ip": primary_ip,
            "interfaces": interfaces,
            "hostname": socket.gethostname()
        }

    def probe_workspaces(self) -> Dict[str, Any]:
        """Scan operator's Desktop and primary development directories."""
        desktop = Path.home() / "Desktop"
        projects: List[Dict[str, Any]] = []

        if desktop.exists() and desktop.is_dir():
            for item in sorted(desktop.iterdir()):
                if not item.is_dir():
                    continue
                name = item.name
                if name.startswith(".") or name.startswith("$"):
                    continue

                has_git = (item / ".git").exists()
                file_count = 0
                sample_files = []
                try:
                    entries = list(item.iterdir())
                    file_count = len(entries)
                    sample_files = [e.name for e in entries[:5]]
                except PermissionError:
                    pass

                # Categorize project
                category = "General Development"
                name_lower = name.lower()
                if any(k in name_lower for k in ["ai", "agent", "ollama", "qwen", "llm", "hanu", "voice", "xai"]):
                    category = "AI / Cognitive Systems"
                elif any(k in name_lower for k in ["token", "blc", "solidity", "blockchain", "crypto"]):
                    category = "Blockchain & Web3"
                elif any(k in name_lower for k in ["stock", "trading", "signal"]):
                    category = "Quantitative & Finance"
                elif any(k in name_lower for k in ["ctf", "cf", "codevita", "dsa", "cfs"]):
                    category = "Algorithms & Security / CTFs"
                elif any(k in name_lower for k in ["docker", "aws", "spring", "app"]):
                    category = "Cloud & Backend / DevOps"
                elif any(k in name_lower for k in ["flutter", "dart", "game", "graphics"]):
                    category = "Mobile & Interactive Graphics"

                projects.append({
                    "name": name,
                    "path": str(item),
                    "has_git": has_git,
                    "items_count": file_count,
                    "category": category,
                    "samples": sample_files
                })

        return {
            "desktop_path": str(desktop),
            "total_projects": len(projects),
            "projects": projects
        }

    def run_full_cartography_scan(self) -> Dict[str, Any]:
        """Execute comprehensive machine cartography and detect state diffs."""
        t0 = time.time()
        hw = self.probe_hardware()
        os_env = self.probe_os_environment()
        tools = self.probe_toolchains()
        net = self.probe_network()
        ws = self.probe_workspaces()
        dt = (time.time() - t0) * 1000

        current_snapshot = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scan_latency_ms": round(dt, 2),
            "hardware": hw,
            "os_environment": os_env,
            "toolchains": tools,
            "network": net,
            "workspaces": ws
        }

        diffs = self._compute_diff(current_snapshot)
        self._save_cache(current_snapshot)
        self.generate_ground_truth_notes(current_snapshot)

        return {
            "snapshot": current_snapshot,
            "diffs": diffs,
            "latency_ms": dt
        }

    def _compute_diff(self, current: Dict[str, Any]) -> List[str]:
        """Compare current scan against previous snapshot to track environmental evolution."""
        if not self.cache_file.exists():
            return ["Initial cartography baseline established across all system vectors."]

        diffs: List[str] = []
        try:
            prev = json.loads(self.cache_file.read_text(encoding="utf-8"))
            # Toolchains diff
            prev_tools = set(prev.get("toolchains", {}).keys())
            curr_tools = set(current.get("toolchains", {}).keys())
            added_tools = curr_tools - prev_tools
            removed_tools = prev_tools - curr_tools
            if added_tools:
                diffs.append(f"Newly installed toolchains detected: {', '.join(added_tools)}")
            if removed_tools:
                diffs.append(f"Toolchains removed: {', '.join(removed_tools)}")

            # Projects diff
            prev_projs = {p["name"] for p in prev.get("workspaces", {}).get("projects", [])}
            curr_projs = {p["name"] for p in current.get("workspaces", {}).get("projects", [])}
            new_projs = curr_projs - prev_projs
            if new_projs:
                diffs.append(f"New workspace projects detected on Desktop: {', '.join(new_projs)}")

            # IP diff
            prev_ip = prev.get("network", {}).get("primary_lan_ip")
            curr_ip = current.get("network", {}).get("primary_lan_ip")
            if prev_ip and curr_ip and prev_ip != curr_ip:
                diffs.append(f"Primary LAN IP mutated: {prev_ip} -> {curr_ip}")

            # Disk diff (>5% change)
            prev_disks = {d["device"]: d["percent_used"] for d in prev.get("hardware", {}).get("disks", [])}
            for d in current.get("hardware", {}).get("disks", []):
                dev = d["device"]
                if dev in prev_disks:
                    delta = abs(d["percent_used"] - prev_disks[dev])
                    if delta >= 5.0:
                        diffs.append(f"Storage volume {dev} capacity delta: {prev_disks[dev]}% -> {d['percent_used']}%")

        except Exception as e:
            diffs.append(f"Notice: Cartography diff evaluation error: {e}")

        if not diffs:
            diffs.append("No material environmental mutations detected; system state nominal.")

        return diffs

    def _save_cache(self, snapshot: Dict[str, Any]) -> None:
        """Persist snapshot cache for historical diffing."""
        try:
            self.cache_file.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        except Exception:
            pass

    def generate_ground_truth_notes(self, snap: Dict[str, Any]) -> None:
        """Render grounded, wikilinked Obsidian notes into '05_System_State/'."""
        ts = snap["timestamp"]
        hw = snap["hardware"]
        os_env = snap["os_environment"]
        tools = snap["toolchains"]
        net = snap["network"]
        ws = snap["workspaces"]

        # 1. Hardware_Topology.md
        hw_gpus_md = "\n".join([
            f"- **{g['name']}**: Driver `{g['driver_version']}`, VRAM: `{g['vram_gb']} GB`"
            for g in hw["gpus"]
        ]) or "- Integrated GPU display pipeline"

        hw_disks_md = "\n".join([
            f"| `{d['device']}` | `{d['fstype']}` | {d['used_gb']} GB | {d['free_gb']} GB | {d['total_gb']} GB | {d['percent_used']}% |"
            for d in hw["disks"]
        ])

        hw_content = f"""---
title: "Host Hardware Topology & Substrate"
type: "hardware_topology"
tags:
  - cortex/system_state
  - cortex/hardware
  - cortex/somatosensory
last_scanned: "{ts}"
status: "verified"
---

# 🖥️ Host Hardware Topology & Substrate

Authoritative ground-truth hardware profile probed by [[01_Architecture/Embodiment_Somatosensory|System Cartographer]] on `{ts}`.

## 🎛️ Central Processing Unit (CPU)
- **Model**: `{hw['cpu']['model']}`
- **Architecture**: `{hw['cpu']['architecture']}`
- **Physical Cores**: `{hw['cpu']['physical_cores']}` physical execution cores
- **Logical Threads**: `{hw['cpu']['logical_threads']}` concurrent hardware threads
- **Live Utilization**: `{hw['cpu']['cpu_percent']}%`

## 🎮 Graphical Processing Units (GPUs)
{hw_gpus_md}

## 🧠 Physical Memory (RAM) & Swap
- **Total Physical RAM**: `{hw['memory']['total_gb']} GB`
- **Available RAM**: `{hw['memory']['available_gb']} GB`
- **RAM In Use**: `{hw['memory']['used_gb']} GB` ({hw['memory']['percent']}%)
- **Swap / Pagefile**: `{hw['swap']['total_gb']} GB` ({hw['swap']['percent']}% utilized)

## 💽 Storage & Partitions
| Mount | Filesystem | Used | Free | Total | Utilization |
|---|---|---|---|---|---|
{hw_disks_md}

---
> [!NOTE] Self-Autonomy Relevance
> CortexOS uses this hardware topology to dynamically scale its thread pools, throttle background cognitive consolidation when RAM headroom is tight, and assign local LLM inference tasks based on available VRAM.
"""
        (self.state_dir / "Hardware_Topology.md").write_text(hw_content, encoding="utf-8")

        # 2. OS_and_Kernel_Environment.md
        shells_md = "\n".join([f"- **`{name}`**: `{path}`" for name, path in os_env["shells"].items()])
        os_content = f"""---
title: "Operating System & Kernel Environment"
type: "os_environment"
tags:
  - cortex/system_state
  - cortex/os
  - cortex/windows
last_scanned: "{ts}"
status: "verified"
---

# 🪟 Operating System & Kernel Environment

Grounded OS execution context for operator `{os_env['user']}` on host `{os_env['hostname']}`.

## ⚙️ Operating System Release
- **Caption**: `{os_env['caption']}`
- **Release Version**: `{os_env['release']}` (Kernel Build `{os_env['version']}`)
- **CPU Architecture**: `{os_env['architecture']}`
- **Host Machine Name**: `{os_env['hostname']}`
- **Logged-in User**: `{os_env['user']}`
- **Home Directory**: `{os_env['home']}`

## 🐚 Available Shell Runtimes
{shells_md}

## 📁 System Paths & Directories
- **SystemRoot**: `{os_env['env_summary']['SYSTEMROOT']}`
- **Roaming APPDATA**: `{os_env['env_summary']['APPDATA']}`
- **Local APPDATA**: `{os_env['env_summary']['LOCALAPPDATA']}`
- **ProgramData**: `{os_env['env_summary']['PROGRAMDATA']}`
- **Temp Directory**: `{os_env['env_summary']['TEMP']}`

---
> [!TIP] Startup & Daemon Linking
> Governed startup scripts and VBS daemon autostart launchers are detailed in [[01_Architecture/Startup_Service_Daemon|Startup Service Daemon]] and [[03_Decisions_ADR/ADR-001-Dual-Boot-Autostart|ADR-001 Dual Boot Autostart]].
"""
        (self.state_dir / "OS_and_Kernel_Environment.md").write_text(os_content, encoding="utf-8")

        # 3. Toolchains_and_Compilers.md
        tools_rows = "\n".join([
            f"| **`{name}`** | `{info['version']}` | `{info['path']}` |"
            for name, info in sorted(tools.items())
        ])
        tools_content = f"""---
title: "Installed Developer Toolchains & Compilers"
type: "toolchains"
tags:
  - cortex/system_state
  - cortex/toolchains
  - cortex/compilers
last_scanned: "{ts}"
status: "verified"
---

# 🛠️ Installed Developer Toolchains & Compilers

Comprehensive registry of developer compilers, language runtimes, package managers, and system utilities available for autonomous execution.

| Tool | Version / Banner | Binary Executable Path |
|---|---|---|
{tools_rows}

## ⚡ Execution Capabilities
- **Python Runtime**: Can execute asynchronous workers, cognitive ticks, data science pipelines, and ML inference.
- **Node.js & NPM**: Capable of launching React/Next/Vue frontend servers and executing JavaScript tooling.
- **Go Compiler**: Capable of building concurrent microservices and native Windows binaries.
- **Docker Engine**: Capable of orchestrating containerized services, databases, and isolated testing sandboxes.
- **FFmpeg & MPV**: Multi-media transcoding, audio stream generation, and real-time playback.
- **VS Code**: Primary operator IDE; can be opened directly via [[02_Pair_Programming/Pair_Programming_Copilot|Pair Copilot]].

---
> [!NOTE] Anti-Hallucination Grounding
> Before dispatching shell commands, the cognitive agent checks this table to ensure the required executable binary exists on host PATH.
"""
        (self.state_dir / "Toolchains_and_Compilers.md").write_text(tools_content, encoding="utf-8")

        # 4. Network_and_Interfaces.md
        iface_rows = []
        for iface, ips in sorted(net["interfaces"].items()):
            iface_rows.append(f"- **`{iface}`**: {', '.join(ips)}")
        iface_md = "\n".join(iface_rows) or "- Local loopback only"

        net_content = f"""---
title: "Network Adapters & LAN Interfaces"
type: "network_interfaces"
tags:
  - cortex/system_state
  - cortex/network
  - cortex/lan
last_scanned: "{ts}"
status: "verified"
---

# 🌐 Network Adapters & LAN Interfaces

Network topology and socket routing for universal multi-device access.

## 📡 Primary Endpoints
- **Primary LAN IP**: `{net['primary_lan_ip']}`
- **Universal Gateway URL**: `http://{net['primary_lan_ip']}:8000` *(accessible on mobile/tablet devices over Wi-Fi)*
- **Local Loopback**: `http://127.0.0.1:8000`
- **Duplex WebSocket**: `ws://{net['primary_lan_ip']}:8000/ws`

## 🔌 Active Network Adapters
{iface_md}

---
> [!NOTE] Multi-Device Pairing
> Devices on the same Wi-Fi subnet connect to `http://{net['primary_lan_ip']}:8000` to interact with the CortexOS live dashboard, voice stream, and pair copilot.
"""
        (self.state_dir / "Network_and_Interfaces.md").write_text(net_content, encoding="utf-8")

        # 5. Filesystem_and_Workspaces.md
        proj_rows = "\n".join([
            f"| **`{p['name']}`** | {p['category']} | {'✓' if p['has_git'] else '✗'} | {p['items_count']} | `{p['path']}` |"
            for p in ws["projects"]
        ])
        fs_content = f"""---
title: "Operator Workspaces & Project Filesystem Map"
type: "workspaces_map"
tags:
  - cortex/system_state
  - cortex/workspaces
  - cortex/projects
last_scanned: "{ts}"
status: "verified"
---

# 🗂️ Operator Workspaces & Project Filesystem Map

Taxonomy of operator project directories discovered across `{ws['desktop_path']}` ({ws['total_projects']} total projects indexed).

| Project Directory | Category | Git Tracked | Items | Full Path |
|---|---|---|---|---|
{proj_rows}

## 🎯 Key Domain Clusters
1. **AI & Cognitive Systems**:
   - `self-conscious`: Active CortexOS project (Cognitive pipeline, Obsidian Vault, Autonomous Daemons).
   - `voice-lab`: Voice experiments, `autonomous_agent.py`, `ada_local`, `assistant_memory`.
   - `qwen3.6-setup-streaming` & `ollama_testing`: Local LLM runner scripts and streaming pipelines.
   - `Discovery_AI_Agent`, `HanuAI`, `nl-to-sql-assistant`.
   - `evolution_of_human-agent_approval_boundaries...`: Academic research papers on human-agent approval boundaries and trajectory collapse mitigation.
2. **Blockchain & Web3**:
   - `blockchain`, `Solidity`, `BLC_TheFracture`, `Token_BLC`, `Token_ERC1155`, `Token_ERC721`.
3. **Algorithms & Security / CTFs**:
   - `CFs` (Codeforces), `Codevita`, `dsa`, `ctfs` (RSA decryption guides), `Go` (Conway Game of Life).
4. **Cloud & DevOps**:
   - `Docker`, `AWS`, `SpringBoot`, `Workout_tracker`.

---
> [!TIP] Pair Copilot Context
> [[02_Pair_Programming/Pair_Programming_Copilot|Pair Copilot]] uses this map to instantly navigate to the right project directory, inspect relevant source code, and assist with active coding tasks.
"""
        (self.state_dir / "Filesystem_and_Workspaces.md").write_text(fs_content, encoding="utf-8")
