---
title: "Startup Service Daemon & LAN Gateway"
type: "architecture"
tags:
  - cortex/startup
  - cortex/daemon
  - cortex/network
last_updated: "2026-10-26"
---

# ⚡ Startup Service Daemon & Universal LAN Gateway

CortexOS is designed to boot automatically on logon as a detached system daemon, binding to universal IP addresses (`0.0.0.0`) so it is reachable both locally and from external devices across the local area network (LAN).

## Cross-Platform Service Manager (`ServiceManager`)

Located at `cortex/startup/service_manager.py`:
- **Windows**:
  - `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\CortexOS_Daemon` pointing to `.venv\Scripts\pythonw.exe cortex\server.py`.
  - Headless VBScript runner: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\cortexos_daemon.vbs` running with window style `0` (no console popup).
- **Linux**:
  - Systemd user service: `~/.config/systemd/user/cortexos.service`.
  - XDG autostart desktop entry: `~/.config/autostart/cortexos.desktop`.
- **macOS**:
  - Launchd user agent: `~/Library/LaunchAgents/com.cortexos.daemon.plist`.

## CLI Interface
```bash
python -m cortex.startup status     # Inspect running PID, boot autostart, and LAN URL
python -m cortex.startup start      # Spawns headless detached daemon
python -m cortex.startup stop       # Terminates running daemon
python -m cortex.startup restart    # Safe restart
python -m cortex.startup install    # Enables autostart on system boot
python -m cortex.startup uninstall  # Disables autostart
python -m cortex.startup network    # Lists all LAN and loopback URLs
```

## Universal LAN Discovery
- Uses non-blocking UDP socket route probe (`8.8.8.8:80`) to discover the machine's primary routing network adapter IP (e.g. `172.16.208.224`).
- Enables phone, tablet, and second-machine interaction over Wi-Fi/Ethernet without requiring public internet exposure.
