---
title: "Autonomous Supervisors & Daemons"
type: "architecture"
tags:
  - cortex/daemons
  - cortex/runtime
  - cortex/supervisors
last_updated: "2026-10-26"
---

# 🤖 Autonomous Supervisors & Daemons

CortexOS operates 5 continuous background supervisor daemons that ensure real-time responsiveness, safety, memory consolidation, and LAN availability:

## 1. Web & WebSocket Gateway Daemon (`Uvicorn`)
- **Port**: Default `8000` (configurable via `CORTEX_PORT`).
- **Host**: Universal `0.0.0.0` (accessible from localhost and LAN).
- **Function**: Serves the cybernetic single-page dashboard, duplex WebSockets (`/ws`), and REST APIs.

## 2. Ambient Cognitive Tick Worker (`GWA`)
- **Frequency**: Every 15 seconds.
- **Function**: Executes unprompted ambient cognitive ticks when toggled on (`btn-ambient`). Generates spontaneous proactive observations or performs background maintenance when operator is idle.

## 3. StallBreaker Sentinel (`StallBreaker`)
- **Timeout**: 45.0s hardware gate.
- **Function**: Monitors the cognitive loop for infinite loops, deadlocks, or runaway processes. If an action hangs, trips the emergency circuit breaker, halts the offending subprocess, and sounds the panic alarm.

## 4. Digital Sleep Consolidation Daemon (`DigitalSleepPipeline`)
- **Scheduler**: Triggers on AC power and system idle state.
- **Function**: Consolidates raw episodic WAL logs into semantic vectors and bi-temporal graph nodes across 4 memory consolidation stages.

## 5. Cross-Platform System Boot & Network Daemon (`ServiceManager`)
- **Autostart**:
  - Windows: Dual unprivileged `HKCU Run` registry + headless VBScript in `%APPDATA%\...\Startup`.
  - Linux: `systemd` user service + XDG autostart.
  - macOS: `launchd` LaunchAgent (`com.cortexos.daemon.plist`).
- **Universal LAN Gateway**: Automatically probes primary route adapter and broadcasts universal LAN URL (`http://<LAN_IP>:8000`).
