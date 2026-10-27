---
title: "Autopoietic Procedural Skills Registry"
type: "skills"
tags:
  - cortex/skills
  - cortex/autopoiesis
  - cortex/tools
last_updated: "2026-10-27"
status: "verified"
---

# ⚡ Autopoietic Procedural Skills Registry

The `AutopoieticSkillCrystallizer` ([`cortex/skills/crystallizer.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/skills/crystallizer.py)) dynamically synthesizes, sandbox-verifies, and crystallizes standalone, executable Python tools into [`cortex/skills/library/`](file:///c:/Users/soham/Desktop/self-conscious/cortex/skills/library/).

Every crystallized skill includes an integrity verification hash and operates strictly within Cedar security governance boundaries.

---

## Active Crystallized Skills Catalog

### 1. `codebase_topology_mapper.py`
- **Location**: [`cortex/skills/library/codebase_topology_mapper.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/skills/library/codebase_topology_mapper.py)
- **Integrity Hash**: `4e81b2a9701d`
- **Capability**: AST-driven codebase inspection. Traverses all Python source files (excluding `.venv` and `__pycache__`), parses AST trees, extracts all classes and functions, counts lines of code (LOC), and ranks architectural modules by complexity.
- **Cedar Governance**: `ALLOW (Read-Only Workspace)`

### 2. `disk_space_reclaimer.py`
- **Location**: [`cortex/skills/library/disk_space_reclaimer.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/skills/library/disk_space_reclaimer.py)
- **Integrity Hash**: `7f920da41c5e`
- **Capability**: Audits and reclaims wasted disk capacity. Scans `.pytest_cache`, `__pycache__`, temporary files, and dangling build artifacts across the workspace, reporting freed megabytes without impacting source code.
- **Cedar Governance**: `ALLOW (Bounded Workspace Cleanup)`

### 3. `git_working_tree_auditor.py`
- **Location**: [`cortex/skills/library/git_working_tree_auditor.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/skills/library/git_working_tree_auditor.py)
- **Integrity Hash**: `8b1c4e9023fa`
- **Capability**: Audits the active git branch, latest commit hash, staging status, modified/untracked files, and inspects recent Git Shadow Checkpoints (`refs/checkpoints/*`).
- **Cedar Governance**: `ALLOW (Git State Inspection)`

### 4. `network_port_sentinel.py`
- **Location**: [`cortex/skills/library/network_port_sentinel.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/skills/library/network_port_sentinel.py)
- **Integrity Hash**: `3d4f8a1290bc`
- **Capability**: Probes open TCP/UDP sockets, binds to network interfaces, monitors gateway port `8000` (FastAPI) and port `11434` (Ollama), detecting potential port collisions or socket leaks.
- **Cedar Governance**: `ALLOW (Network Telemetry Query)`

### 5. `process_resource_optimizer.py`
- **Location**: [`cortex/skills/library/process_resource_optimizer.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/skills/library/process_resource_optimizer.py)
- **Integrity Hash**: `2a98e104cd3f`
- **Capability**: Analyzes host operating system processes via `psutil`. Identifies top CPU and memory consumers, monitors thread handles, and flags high-memory orphaned background daemons.
- **Cedar Governance**: `ALLOW (Process Inspection)`

### 6. `system_telemetry_reporter.py`
- **Location**: [`cortex/skills/library/system_telemetry_reporter.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/skills/library/system_telemetry_reporter.py)
- **Integrity Hash**: `1b4a92c304fa`
- **Capability**: Gathers comprehensive somatosensory metrics: CPU utilization, per-core load, DDR4 RAM consumption, GPU VRAM allocation, battery/power posture, and C: drive headroom.
- **Cedar Governance**: `ALLOW (Hardware Telemetry)`

### 7. `tool_cpu_utilization.py`
- **Location**: [`cortex/skills/library/tool_cpu_utilization.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/skills/library/tool_cpu_utilization.py)
- **Capability**: Micro-utility providing immediate, sub-millisecond CPU percentage sampling.
- **Cedar Governance**: `ALLOW`

### 8. `tool_inspect_active_git_branc.py`
- **Location**: [`cortex/skills/library/tool_inspect_active_git_branc.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/skills/library/tool_inspect_active_git_branc.py)
- **Capability**: Micro-utility for rapid Git branch resolution and HEAD verification.
- **Cedar Governance**: `ALLOW`

---

## Skill Synthesis Lifecycle (Autopoietic Loop)
1. **Perception**: An unknown capability is requested during a cognitive tick.
2. **Generation**: The local LLM or Crystallizer synthesizes Python code in a sandboxed staging directory.
3. **Execution Verification**: The tool is executed in [`cortex/governance/sandbox.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/governance/sandbox.py) against unit tests.
4. **Crystallization**: If execution succeeds with code 0, it is promoted to `cortex/skills/library/` and registered into the active skill index.

---
## Related Notes
- [[01_Architecture/Governance_Cedar|Cedar Security Governance]]
- [[06_Self_Evolution/Skill_Synthesis_Engine|Skill Synthesis Engine]]
- [[04_Skills_Catalog/Trigger_Registry|Deterministic Trigger Registry]]
