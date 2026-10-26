---
title: "Governance & Cedar Safety Policies"
type: "architecture"
tags:
  - cortex/governance
  - cortex/cedar
  - cortex/safety
last_updated: "2026-10-26"
---

# 🛡️ Governance & Cedar Safety Policies

CortexOS enforces strict containment boundaries using Amazon Cedar policy definitions located at `config/policies.cedar`.

## Policy Hierarchy & Decision Engine

Every proposed action from System 1 or System 2 is submitted to `PolicyEngine.evaluate(action, context)`:

1. **`ALLOW`**:
   - Action satisfies safe containment boundaries (e.g. read-only inspections, sandboxed test runs, hardware telemetry, music control, verified skill execution).
   - Proceeds immediately to Stage 9 Execution.

2. **`ESCALATE` (Human Hold Card)**:
   - Destructive actions, system file deletion, arbitrary shell writes to root paths, or foreign code execution.
   - Halts execution and presents an interactive **Human Escalation Hold Card** with options to `[APPROVE]` or `[REJECT]`.

3. **`DENY`**:
   - Outright blocked actions (accessing forbidden credentials, violating sandbox memory boundaries, unauthorized network exfiltration).

## Git Shadow Checkpointing
- Before any file modification or skill execution, `GitShadowCheckpointManager` creates a shadow git checkpoint branch (`refs/cortex/shadow/...`).
- If an operation fails, the system can autonomously roll back to the exact pre-execution working tree state with zero data loss.
