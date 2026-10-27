---
title: "Cross-Platform System Services & Daemon Autostart"
type: "services_startup"
tags:
  - cortex/system_state
  - cortex/startup
  - cortex/daemon
last_updated: "2026-10-26"
status: "verified"
---

# 🚀 Cross-Platform System Services & Daemon Autostart

Complete ground truth for background daemon lifecycle, boot hooks, and cross-platform process isolation across Windows, Linux, and macOS.

## 🪟 Windows Boot & Service Architecture
- **Autostart Mechanism**: Dual-registration via Windows Registry & Startup Folder.
  - **Registry Key**: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` -> `CortexOS_Daemon` pointing to `wscript.exe cortex_daemon_startup.vbs`.
  - **Startup Script**: `cortex_daemon_startup.vbs` located in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`.
- **Silent Headless Spawning**: Spawns `.venv\Scripts\pythonw.exe cortex/server.py` with `WshShell.Run(..., 0, False)` to ensure zero intrusive terminal popups during Windows logon.
- **LAN Binding**: Binds to `0.0.0.0:8000`, broadcasting across primary Wi-Fi (`10.234.160.224`, dynamically detected via `cortex/system_state/network.py`).

## 🐧 Linux Systemd & XDG Autostart
- **Service Unit**: `~/.config/systemd/user/cortexos.service` (`WantedBy=default.target`, `Restart=always`).
- **Desktop Entry**: `~/.config/autostart/cortexos.desktop` for graphical desktop environments.

## 🍎 macOS Launchd Daemon
- **Launch Agent**: `~/Library/LaunchAgents/com.cortexos.daemon.plist` (`RunAtLoad=true`, `KeepAlive=true`).

---
> [!NOTE] Health Watchdogs
> The [[01_Architecture/Autonomous_Daemons|StallBreaker Sentinel]] periodically pings the HTTP and WebSocket endpoints to guarantee that the system daemon never hangs silently.
