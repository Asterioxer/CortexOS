---
title: "Deterministic Grounded Trigger Registry"
type: "trigger_registry"
tags:
  - cortex/skills
  - cortex/triggers
  - cortex/deterministic
last_updated: "2026-10-26"
status: "verified"
---

# 🎯 Deterministic Grounded Trigger Registry

Authoritative master catalog of exact, deterministic triggers recognized by CortexOS. The Obsidian Vault acts as the ground-truth trigger rulebase to eliminate random guessing and ungrounded hallucination.

## 1. Session Greeting Triggers
- **Exact Phrases**: `"greet"`, `"greetings"`, `"hello"`, `"hey cortex"`, `"hi cortex"`, `"wake up"`, `"session_start"`.
- **Target Action**: `execute_greeting`
- **Output Persona**: `JARVIS` (Baritone)
- **Response Format**: Personal greeting to operator Soham, live RAM headroom, hardware status overview, and prompt for guidance.

## 2. Shutdown & Stand-Down Triggers
- **Exact Phrases**: `"shutdown"`, `"power off"`, `"goodbye"`, `"stand down"`, `"exit cortex"`, `"shut down"`, `"bye cortex"`, `"system_shutdown"`.
- **Target Action**: `execute_shutdown`
- **Output Persona**: `JARVIS`
- **Execution Sequence**:
  1. Commit all modified notes and memories to `.cortex/vault_backup.git`.
  2. Record clean session exit into [[06_Self_Evolution/Introspection_Ledger|Introspection Ledger]].
  3. Synthesize voice goodbye: *"Goodbye Soham. Memory state consolidated and committed to your vault backup. CortexOS is safely standing down."*
  4. Transition UI to safe Standby mode.

## 3. Project Workspace Switching Triggers
- **Trigger Patterns**:
  - `open project <project_name>`
  - `switch to project <project_name>`
  - `open folder <project_name>`
- **Cataloged Workspaces**: Matches against the 48 desktop directories documented in [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]] and [[05_System_State/Filesystem_and_Workspaces|Filesystem & Workspaces Map]].
- **Action**: Launches VS Code directly into the resolved directory (e.g. `C:\Users\soham\Desktop\voice-lab`, `qwen3.6-setup-streaming`, `HanuAI_Tasks`).

## 4. Grounded Application Launch Triggers
- `"open code"` / `"open vs code"` -> VS Code IDE
- `"open mpv"` -> MPV Media Player
- `"open docker"` -> Docker Desktop
- `"open browser"` -> Default web browser to dashboard
- `"open terminal"` -> PowerShell console

## 5. System Cartography & Evolution Triggers
- `"cartography"` / `"scan machine"` / `"scan system"` -> Comprehensive hardware & toolchain cartography.
- `"evolve system"` / `"self evolve"` / `"evolution cycle"` -> 5-phase autopoietic self-evolution cycle.
- `"system health"` / `"introspect"` -> Real-time Health Index and resource pressure audit.
- `"sync vault"` / `"backup vault"` -> Instant commit and push to private Git backup.

## 6. Media Control Triggers
- `"play music"`, `"pause music"`, `"next song"`, `"previous song"`.
