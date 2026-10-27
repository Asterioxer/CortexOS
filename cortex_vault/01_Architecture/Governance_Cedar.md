---
title: "Governance & Cedar Safety Policies"
type: "architecture"
tags:
  - cortex/governance
  - cortex/cedar
  - cortex/safety
  - cortex/checkpoints
last_updated: "2026-10-27"
status: "verified"
---

# 🛡️ Governance & Cedar Safety Policies

CortexOS enforces mathematical containment boundaries using formal Amazon Cedar policy specifications located at [`config/policies.cedar`](file:///c:/Users/soham/Desktop/self-conscious/config/policies.cedar).

Every action proposed by System 1 reflexes or System 2 local LLM reasoning passes through [`cortex/governance/policy_engine.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/governance/policy_engine.py) before execution.

---

## The 5 Formal Cedar Authorization Rules

```cedar
// RULE 1: DENY all access to secret identity and credential directories
forbid (
    principal,
    action in [Action::"read", Action::"write", Action::"delete"],
    resource in [Resource::"~/.ssh", Resource::"~/.aws", Resource::"~/.gnupg", Resource::"config/policies.cedar"]
);

// RULE 2: DENY delegation depth greater than 2 to avoid unbounded recursive subagents
forbid (
    principal,
    action,
    resource
)
when {
    context.delegation_depth > 2
};

// RULE 3: ESCALATE (Human-in-the-Loop) irreversible, destructive, or remote operations
permit (
    principal,
    action in [
        Action::"git_push_remote",
        Action::"send_external_email",
        Action::"modify_production_system",
        Action::"financial_transaction",
        Action::"delete_directory_recursive"
    ],
    resource
)
when {
    context.human_approval == true
};

// RULE 4: ALLOW read-only operations across normal project files
permit (
    principal,
    action in [Action::"file_read", Action::"directory_list", Action::"git_status", Action::"inspect_accessibility_tree"],
    resource
)
unless {
    resource.is_credential == true
};

// RULE 5: ALLOW local reversible modifications within the active working directory when backed by pre-task shadow checkpoint
permit (
    principal,
    action in [Action::"file_write", Action::"file_edit", Action::"run_sandboxed_script", Action::"crystallize_skill"],
    resource
)
when {
    context.checkpoint_active == true &&
    resource.in_workspace == true &&
    resource.is_policy_file == false
};
```

---

## Policy Evaluation & Verdict States

The `PolicyEngine.evaluate(action, context)` evaluates within sub-millisecond execution time (<2.5ms) and produces three definitive verdicts:

1. **`ALLOW`**:
   - The action is provably safe and bounded within workspace containment (e.g. read-only telemetry, directory listings, audio volume, sandboxed script execution, git status).
   - Proceeds immediately to somatic execution without latency.
2. **`ESCALATE` (Interactive Human Hold Card)**:
   - Destructive operations, remote network pushes, credential modifications, or directory deletions.
   - Halts execution and dispatches a structured **Hold Card** across WebSockets to the web dashboard:
     ```json
     {
       "type": "hold_card",
       "action": "git_push_remote",
       "reversibility": "LOW",
       "blast_radius": "HIGH",
       "prompt": "Operator approval required for remote repository push."
     }
     ```
   - The user must explicitly click `[APPROVE]` or `[REJECT]`.
3. **`DENY`**:
   - Outright prohibited actions: accessing `~/.ssh`, `~/.aws`, `~/.gnupg`, modifying `config/policies.cedar`, or exceeding delegation recursion depth $> 2$.

---

## Git Shadow Checkpoint Manager ([`cortex/governance/checkpoint.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/governance/checkpoint.py))
- Before executing any state-mutating action or synthesized skill, CortexOS creates a hidden, zero-overhead git shadow tree:
  `refs/checkpoints/<task_id>/<label>`
- Shadow checkpoints do not alter user branch history, commit logs, or working branches.
- If a synthesized tool or command fails, the system triggers `restore_checkpoint()`, atomically resetting the tree to its exact pre-execution state.

## StallBreaker & Panic Circuit ([`cortex/embodiment/stall_breaker.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/embodiment/stall_breaker.py))
- Emergency hardware circuit capable of freezing all autonomous execution.
- Triggered by clicking `[ 🚨 PANIC STOP ]` on the dashboard or calling `POST /api/governance/panic`.
- Instantly freezes child processes, locks the workspace tree, and logs a panic snapshot to `.cortex/panic_snapshot.git`.

---
## Related Notes
- [[01_Architecture/System_Architecture|System Architecture]]
- [[04_Skills_Catalog/Autonomy_Boundaries|Autonomy Boundaries]]
- [[06_Self_Evolution/Autonomy_Boundaries_and_Escalation|Autonomy Boundaries and Escalation]]
- [[02_Pair_Programming/Execution_Playbooks|Execution Playbooks]]
