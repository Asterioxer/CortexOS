---
title: "Embodiment & Hardware Somatosensory"
type: "architecture"
tags:
  - cortex/embodiment
  - cortex/somatosensory
  - cortex/hardware
last_updated: "2026-10-26"
---

# 🦾 Embodiment & Hardware Somatosensory

CortexOS does not operate as an isolated sandbox; it is physically embodied on the operator's laptop with direct access to operating system telemetry and control.

## Subsystems

### 1. Hardware Somatosensory (`SystemSomatosensory`)
- **CPU & Memory**: Real-time load %, frequency, core counts, RAM used/available.
- **GPU**: NVIDIA / Intel / AMD vendor inspection, VRAM allocation, temperature.
- **Battery**: AC power connection status, percentage, battery saver mode.
- **Active Window**: Currently focused desktop application title, process name, and PID via Win32 API.
- **Process Topology**: Lists user applications (Chrome, Discord, VS Code, Spotify) and system processes.

### 2. Autonomous Application Execution
- Autonomous capability to launch desktop applications requested by the operator via `os.startfile(app_target)` or shell execution.
- Known application targets:
  - Browsers: `chrome`, `msedge`, `brave`, `firefox`.
  - Development: `code`, `cmd`, `powershell`, `wt`.
  - Media: `spotify`, `vlc`.
  - System: `notepad`, `calc`, `taskmgr`, `explorer`.

### 3. Media Subsystem & Audio Playback
- Integrates with Windows Media Control (GSMTC via `winsdk` / media control key simulator fallback).
- Detects currently playing track title, artist, playback state (PLAYING / PAUSED).
- Provides instant play, pause, next track, and previous track controls.

### 4. Neural Voice Engine & Barge-In
- Multiple neural persona voices (JARVIS, Friday, Christopher, Edith, Neerja, Jenny, Guy).
- Monotonic speech epoch mutex (`activeSpeechEpoch`) preventing voice collision when switching personas or speaking new replies.
- Sub-10ms instant barge-in killswitch (`bargeInStopVoice`) to silence the voice immediately upon operator interrupt.
