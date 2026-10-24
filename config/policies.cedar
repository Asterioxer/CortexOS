// CortexOS Deterministic Cedar Authorization Policies
// Principal: CortexOS Agent or Subagent
// Action: Tool execution or system call
// Resource: File, network target, or process

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
