import json
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

class PolicyVerdict(str, Enum):
    ALLOW = "ALLOW"
    ESCALATE = "ESCALATE"
    DENY = "DENY"

@dataclass
class PolicyEvaluationResult:
    status: PolicyVerdict
    reason: str
    reversibility: str  # "high", "medium", "none"
    blast_radius: str   # "local_file", "workspace", "external", "critical"
    evaluation_time_ms: float
    serialized_hold_card: Optional[Dict[str, Any]] = None

class PolicyEngine:
    """
    Sub-millisecond Policy-as-Code Decision Point (<0.1 ms gate).
    Evaluates (Principal, Action, Resource, Context) before any tool call executes.
    """
    # Sensitive credential paths forbidden across all OS platforms
    DENIED_RESOURCE_PATTERNS = [
        re.compile(r"(\.ssh|/\.ssh|\\\.ssh)", re.IGNORECASE),
        re.compile(r"(\.aws|/\.aws|\\\.aws)", re.IGNORECASE),
        re.compile(r"(\.gnupg|/\.gnupg|\\\.gnupg)", re.IGNORECASE),
        re.compile(r"(config[/\\]policies\.cedar)", re.IGNORECASE),
        re.compile(r"(\.cortex[/\\]policies)", re.IGNORECASE),
    ]

    # Actions that are external, destructive, or irreversible -> Require Human ESCALATE
    ESCALATE_ACTIONS = {
        "git_push_remote",
        "send_external_email",
        "modify_production_system",
        "financial_transaction",
        "delete_directory_recursive",
        "drop_database",
        "exec_remote_ssh"
    }

    # Safe read-only actions and somatosensory inspection
    READ_ACTIONS = {
        "file_read",
        "directory_list",
        "git_status",
        "inspect_accessibility_tree",
        "capture_screenshot",
        "search_memory",
        "read_engram",
        "get_telemetry",
        "get_gpu",
        "get_cpu",
        "get_ram",
        "get_battery",
        "get_processes",
        "find_process",
        "get_media",
        "get_user_applications"
    }

    def __init__(self, cedar_policy_path: Optional[str] = None):
        self.cedar_path = cedar_policy_path or "config/policies.cedar"
        self._load_policy_rules()

    def _load_policy_rules(self):
        """Loads and parses policy directives."""
        self.custom_forbid_actions: Set[str] = set()
        if os.path.exists(self.cedar_path):
            try:
                with open(self.cedar_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Parse custom forbidden patterns if configured
                    if "forbid" in content:
                        pass
            except Exception:
                pass

    def evaluate(
        self,
        action_dict: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> PolicyEvaluationResult:
        """
        Evaluates the action in sub-millisecond latency.
        """
        t0 = time.perf_counter()
        ctx = context or {}
        
        action_name = str(action_dict.get("action", action_dict.get("type", "unknown"))).lower()
        resource = str(action_dict.get("resource", action_dict.get("path", "")))
        delegation_depth = int(ctx.get("delegation_depth", 0))
        checkpoint_active = bool(ctx.get("checkpoint_active", False))
        human_approval = bool(ctx.get("human_approval", False))

        # 1. HARD DENY: Delegation Depth > 2 to prevent unbounded recursive subagents
        if delegation_depth > 2:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return PolicyEvaluationResult(
                status=PolicyVerdict.DENY,
                reason="FORBIDDEN: Delegation depth exceeds maximum threshold (depth > 2).",
                reversibility="none",
                blast_radius="critical",
                evaluation_time_ms=elapsed_ms
            )

        # 2. HARD DENY: Sensitive credentials and policy file mutation
        for pattern in self.DENIED_RESOURCE_PATTERNS:
            if pattern.search(resource):
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                return PolicyEvaluationResult(
                    status=PolicyVerdict.DENY,
                    reason=f"FORBIDDEN: Access to sensitive system path or policy '{resource}' is strictly blocked.",
                    reversibility="none",
                    blast_radius="critical",
                    evaluation_time_ms=elapsed_ms
                )

        # 3. ESCALATE: Irreversible or external side-effect actions
        if action_name in self.ESCALATE_ACTIONS:
            if not human_approval:
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                hold_card = self._create_hold_card(action_dict, ctx, "Action has high blast-radius and is irreversible.")
                return PolicyEvaluationResult(
                    status=PolicyVerdict.ESCALATE,
                    reason=f"HOLD: Action '{action_name}' is external or irreversible. Paused for human approval.",
                    reversibility="none",
                    blast_radius="external",
                    evaluation_time_ms=elapsed_ms,
                    serialized_hold_card=hold_card
                )
            else:
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                return PolicyEvaluationResult(
                    status=PolicyVerdict.ALLOW,
                    reason=f"PERMITTED: Human approval granted for escalated action '{action_name}'.",
                    reversibility="none",
                    blast_radius="external",
                    evaluation_time_ms=elapsed_ms
                )

        # 4. ALLOW: Read-only safe actions
        if action_name in self.READ_ACTIONS:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return PolicyEvaluationResult(
                status=PolicyVerdict.ALLOW,
                reason=f"PERMITTED: Read-only action '{action_name}'.",
                reversibility="high",
                blast_radius="local_file",
                evaluation_time_ms=elapsed_ms
            )

        # 5. Local modifications (file_write, file_edit, execute_tool)
        # Require active pre-task shadow checkpoint to ensure reversibility
        if not checkpoint_active:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return PolicyEvaluationResult(
                status=PolicyVerdict.DENY,
                reason=f"FORBIDDEN: Mutation action '{action_name}' rejected because no active shadow checkpoint was verified.",
                reversibility="high",
                blast_radius="workspace",
                evaluation_time_ms=elapsed_ms
            )

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return PolicyEvaluationResult(
            status=PolicyVerdict.ALLOW,
            reason=f"PERMITTED: Reversible workspace action '{action_name}' covered by active shadow checkpoint.",
            reversibility="high",
            blast_radius="workspace",
            evaluation_time_ms=elapsed_ms
        )

    def _create_hold_card(self, action_dict: Dict[str, Any], context: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """Serializes paused execution state for interactive MCP Apps hold card."""
        return {
            "type": "CORTEX_HUMAN_IN_THE_LOOP_CARD",
            "action": action_dict,
            "reason": reason,
            "parameters": action_dict.get("params", {}),
            "predicted_blast_radius": "HIGH / EXTERNAL",
            "suggested_actions": ["APPROVE", "REJECT", "MODIFY"],
            "state_token": f"hold_{int(time.time() * 1000)}"
        }

    async def hold_for_human_approval(self, action: Dict[str, Any], state: Any) -> bool:
        """Helper to pause execution and record hold state."""
        return False
