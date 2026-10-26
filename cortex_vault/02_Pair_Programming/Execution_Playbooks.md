---
title: "Immediate Action Execution Playbooks"
type: "pair_programming"
tags:
  - cortex/playbooks
  - cortex/recipes
last_updated: "2026-10-26"
---

# 📖 Immediate Action Execution Playbooks

Standard recipes and direct execution procedures for common pairing operations:

### 1. Launching Desktop Applications
- **Command / Reflex**: "open <app_name>" (e.g. `open spotify`, `open chrome`, `open code`)
- **Direct Action**: `SystemSomatosensory.launch_application(target)`
- **Mechanism**: Windows `os.startfile(target)` with URI scheme fallback.

### 2. Media Controls
- **Command / Reflex**: "pause music", "next song", "what's playing"
- **Direct Action**: `SystemSomatosensory.control_media("toggle" | "next" | "previous")`

### 3. Full System Audit & Test Run
- **Command / Reflex**: "run tests", "verify all"
- **Direct Action**: `.venv\Scripts\python.exe -m pytest tests/`

### 4. Vault Grounded Search
- **Command / Reflex**: "search vault <query>", "ask vault <question>"
- **Direct Action**: `VaultRAG.retrieve_grounded_context(query)`

### 5. Vault Private Repo Backup Sync
- **Command / Reflex**: "sync vault", "backup vault"
- **Direct Action**: `VaultSync.sync()`
