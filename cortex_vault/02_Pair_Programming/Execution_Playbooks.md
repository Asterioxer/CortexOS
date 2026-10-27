---
title: "Immediate Action Execution Playbooks"
type: "pair_programming"
tags:
  - cortex/playbooks
  - cortex/recipes
  - cortex/operations
last_updated: "2026-10-27"
status: "verified"
---

# 📖 Immediate Action Execution Playbooks

Standard operating procedures, executable shell recipes, and direct programmatic dispatch sequences for all core CortexOS workflows.

---

## Playbook 1: Spawning & Managing the Live Daemon Server
- **Objective**: Run CortexOS as a background system daemon on `http://localhost:8000`.
- **Command Line**:
  ```powershell
  .venv\Scripts\python.exe cortex/server.py
  ```
- **Verification**:
  ```powershell
  # Check port 8000 binding
  Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
  # Test health endpoint
  Invoke-RestMethod -Uri http://localhost:8000/api/llm/models
  ```
- **Service Registration**: Registered in Windows CurrentVersion Run registry via [`cortex/startup/service_manager.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/startup/service_manager.py).

---

## Playbook 2: Switching Desktop Workspace Projects
- **Objective**: Seamlessly switch pair programming context and launch VS Code into any of the 48 desktop directories.
- **Trigger Input**: `"open project voice-lab"`, `"open project qwen"`, `"switch to project HanuAI"`, or click Quick Chips.
- **REST Dispatch**:
  ```http
  POST /api/system/trigger
  Content-Type: application/json

  {"prompt": "open project voice-lab"}
  ```
- **Execution Mechanism**:
  1. [`cortex/vault/trigger_router.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/vault/trigger_router.py) matches `PROJECT_SWITCH`.
  2. Resolves target directory on `C:\Users\soham\Desktop\` via fuzzy directory scan.
  3. Spawns `code "C:\Users\soham\Desktop\<project_name>"`.
  4. Returns confirmation voice instruction under the `Guy` persona.

---

## Playbook 3: Switching Local Ollama Models Dynamically
- **Objective**: Toggle between local LLM engines on the RTX 3050 without restarting the daemon.
- **Trigger**: Click `[ 🤖 OLLAMA: qwen2.5:3b ▾ ]` in header or dispatch API call.
- **REST Dispatch**:
  ```http
  POST /api/llm/select
  Content-Type: application/json

  {"model": "dolphinlabs/llama3.2-3b-uncensored:latest"}
  ```
- **Supported Local Models**:
  - `qwen2.5:3b`: Fast reactive computer control & application launching (1.80 GB VRAM).
  - `dolphinlabs/llama3.2-3b-uncensored:latest`: Conversational, empathetic dialogue (3.19 GB VRAM).
  - `nandhank/qwen3.5-abliterated-truthful:9b`: Heavyweight algorithmic & AST reasoning (6.14 GB hybrid VRAM/RAM).
  - `gemma3:4b`: Structured JSON & schema synthesis (3.11 GB VRAM).

---

## Playbook 4: Full System Cartography & Hardware Scan
- **Objective**: Probe dual GPUs, 12 toolchains, and 48 desktop projects, updating ground-truth vault notes.
- **Trigger**: Click `[ 🗺️ Cartography ]` or prompt `"scan system"`.
- **Programmatic Dispatch**:
  ```python
  from cortex.vault.system_cartographer import SystemCartographer
  carto = SystemCartographer()
  report = carto.run_full_cartography_cycle()
  ```
- **Output Artifacts**: Automatically updates [[05_System_State/Hardware_Topology]], [[05_System_State/Toolchains_and_Compilers]], and [[05_System_State/Filesystem_and_Workspaces]].

---

## Playbook 5: Autopoietic Self-Evolution Cycle
- **Objective**: Execute the 5-phase self-evolution loop to synthesize skills, adapt heuristics, and consolidate memory.
- **Trigger**: Click `[ 🔄 Self-Evolution ]` or prompt `"run self evolution"`.
- **REST Dispatch**:
  ```http
  POST /api/system/trigger
  {"prompt": "run self evolution"}
  ```
- **Phases Executed**:
  1. *Sensing*: Audits hardware pressure, memory leaks, and disk space.
  2. *Introspection*: Appends structured cycle entry to [[06_Self_Evolution/Introspection_Ledger]].
  3. *Heuristic Tuning*: Dynamically updates temperature $\tau$ and perspective weights in [[06_Self_Evolution/Heuristic_Adaptation_Matrix]].
  4. *Skill Synthesis*: Synthesizes and sandbox-verifies any missing capability tools.
  5. *Memory Consolidation*: Commits all deltas to `.cortex/vault_backup.git`.

---

## Playbook 6: Vault Backup Git Synchronization
- **Objective**: Push all markdown notes and memory state to the private Git repository.
- **Trigger**: Click `[ 💾 Vault Sync ]` or prompt `"sync vault"`.
- **CLI Dispatch**:
  ```powershell
  .venv\Scripts\python.exe -c "from cortex.vault.git_sync import get_vault_sync; print(get_vault_sync().commit_and_push('Manual operator backup sync'))"
  ```

---

## Playbook 7: Emergency StallBreaker Panic Halt & Recovery
- **Objective**: Instantly freeze all autonomous OS mutations upon detecting an anomaly.
- **Halt Trigger**: Click `[ 🚨 PANIC STOP ]` or `POST /api/governance/panic`.
- **Recovery Trigger**: Click `[ 🛡️ RESET PANIC ]` or `POST /api/governance/reset_panic`.
- **Rollback Mechanism**: Git Shadow Checkpoints revert workspace to the last verified commit (`refs/checkpoints/panic_snapshot`).

---
## Related Notes
- [[02_Pair_Programming/User_Preferences|Operator Profile & Preferences]]
- [[04_Skills_Catalog/Trigger_Registry|Deterministic Trigger Registry]]
- [[06_Self_Evolution/Autonomous_Evolution_Architecture|Autonomous Evolution Architecture]]
