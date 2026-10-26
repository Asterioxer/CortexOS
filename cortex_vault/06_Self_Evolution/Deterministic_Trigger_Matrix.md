---
title: "Deterministic Trigger & Action Execution Matrix"
type: "trigger_matrix"
tags:
  - cortex/evolution
  - cortex/triggers
  - cortex/cedar
last_updated: "2026-10-26"
status: "verified"
---

# ⚡ Deterministic Trigger & Action Execution Matrix

This matrix specifies the deterministic routing table implemented in [[01_Architecture/System_Architecture|TriggerRouter]], mapping grounded inputs to internal Python routines, Cedar security tiers, and voice synthesis rules.

| Trigger Category | Trigger Keywords | Dispatched Action | Cedar Tier | Spoken Persona |
|---|---|---|---|---|
| **Session Greeting** | `greet`, `hello`, `hey cortex`, `session_start` | `execute_greeting()` | Tier 1 (Safe) | `JARVIS` |
| **System Shutdown** | `shutdown`, `goodbye`, `stand down`, `bye` | `execute_shutdown()` | Tier 1 (Safe) | `JARVIS` |
| **Workspace Switching** | `open project <name>`, `switch to <name>` | `switch_project()` | Tier 2 (Logged) | `GUY` |
| **App Launching** | `open code`, `open mpv`, `open docker` | `launch_application()` | Tier 2 (Logged) | `JARVIS` |
| **System Cartography** | `cartography`, `scan system`, `scan machine` | `run_cartography()` | Tier 1 (Safe) | `EDITH` |
| **Self-Evolution** | `evolve system`, `self evolve`, `evolution cycle` | `run_evolution()` | Tier 2 (Logged) | `JARVIS` |
| **Health Introspection** | `system health`, `introspect`, `telemetry` | `get_telemetry()` | Tier 1 (Safe) | `JARVIS` |
| **Vault Private Backup** | `sync vault`, `backup vault` | `sync_vault()` | Tier 1 (Safe) | `JARVIS` |
| **Media Control** | `play music`, `pause music`, `next song` | `control_media()` | Tier 1 (Safe) | None |

---
> [!NOTE] Anti-Hallucination Guarantees
> If an operator request matches any trigger above, it is dispatched immediately via deterministic code paths without invoking speculative LLM generations.
