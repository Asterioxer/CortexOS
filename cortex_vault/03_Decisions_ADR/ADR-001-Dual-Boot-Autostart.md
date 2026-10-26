---
title: "ADR-001: Cross-Platform Boot Autostart via Registry & Headless VBScript"
type: "adr"
tags:
  - cortex/adr
  - cortex/startup
status: "accepted"
date: "2026-10-26"
---

# ADR-001: Cross-Platform Boot Autostart via Registry & Headless VBScript

## Context
The operator requested that CortexOS automatically boot upon system start, operating as an autonomous background daemon across Windows, Linux, and macOS without requiring elevated Administrator/root privileges.

## Decision
- On **Windows**:
  - `schtasks /Create /SC ONLOGON` fails without Administrator elevation.
  - We implemented dual unprivileged mechanisms:
    1. User Registry: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\CortexOS_Daemon`.
    2. Headless VBScript launcher in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\cortexos_daemon.vbs` executing `pythonw.exe` with window style `0`.
- On **Linux**: `systemd` user service unit (`~/.config/systemd/user/cortexos.service`) and standard XDG autostart desktop entry.
- On **macOS**: `launchd` LaunchAgent (`~/Library/LaunchAgents/com.cortexos.daemon.plist`).

## Consequences
CortexOS starts headlessly and silently upon user logon across all operating systems without terminal popups or elevation prompts.
