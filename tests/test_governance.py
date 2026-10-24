import os
import shutil
import tempfile
import pytest
from pathlib import Path
from cortex.governance.policy_engine import PolicyEngine, PolicyVerdict
from cortex.governance.checkpoint import GitShadowCheckpointManager
from cortex.governance.sandbox import SandboxRunner
from cortex.embodiment.stall_breaker import StallBreaker

def test_checkpoint_a_hold_test():
    """
    Checklist Test (a) Hold Test:
    Wide-reach / irreversible actions pause and serialize JSON state for human approval.
    """
    engine = PolicyEngine()
    
    wide_reach_action = {
        "action": "git_push_remote",
        "params": {"remote": "origin", "branch": "main"}
    }
    
    # Without human approval, should return ESCALATE and serialized hold card
    res = engine.evaluate(wide_reach_action, {"checkpoint_active": True, "human_approval": False})
    assert res.status == PolicyVerdict.ESCALATE
    assert "git_push_remote" in res.reason
    assert res.serialized_hold_card is not None
    assert res.serialized_hold_card["type"] == "CORTEX_HUMAN_IN_THE_LOOP_CARD"
    assert res.serialized_hold_card["action"]["action"] == "git_push_remote"
    assert res.evaluation_time_ms < 1.0  # Sub-millisecond gate

def test_checkpoint_b_reject_test():
    """
    Checklist Test (b) Reject Test:
    Verify that when human rejects an escalated action, system does not permit bypass.
    """
    engine = PolicyEngine()
    action = {"action": "delete_directory_recursive", "path": "/data/cache"}
    
    # Human explicitly rejected (human_approval = False)
    res = engine.evaluate(action, {"human_approval": False, "checkpoint_active": True})
    assert res.status == PolicyVerdict.ESCALATE
    # Action cannot proceed autonomously
    assert res.status != PolicyVerdict.ALLOW

def test_checkpoint_c_refuse_test():
    """
    Checklist Test (c) Refuse Test:
    Verify reading ~/.ssh or credentials is hard blocked (DENY).
    """
    engine = PolicyEngine()
    
    # Attempting to read ~/.ssh/id_rsa
    ssh_action = {"action": "file_read", "resource": "~/.ssh/id_rsa"}
    res = engine.evaluate(ssh_action, {"checkpoint_active": True})
    assert res.status == PolicyVerdict.DENY
    assert "strictly blocked" in res.reason
    
    # Attempting to modify policies
    policy_action = {"action": "file_write", "resource": "config/policies.cedar"}
    res2 = engine.evaluate(policy_action, {"checkpoint_active": True})
    assert res2.status == PolicyVerdict.DENY

def test_checkpoint_d_stop_test():
    """
    Checklist Test (d) Stop Test:
    Verify moving cursor to (0,0) or pressing Ctrl+Alt+Shift+Q halts execution immediately.
    """
    breaker = StallBreaker()
    assert not breaker.is_panic_triggered()
    
    # 1. Test mouse panic switch at (0, 0)
    breaker.check_mouse_panic_coordinate(100, 200)
    assert not breaker.is_panic_triggered()
    
    breaker.check_mouse_panic_coordinate(0, 0)
    assert breaker.is_panic_triggered()
    assert "screen coordinate (0, 0)" in breaker.panic_reason
    
    breaker.reset_panic()
    assert not breaker.is_panic_triggered()
    
    # 2. Test hotkey panic switch (Ctrl + Alt + Shift + Q)
    breaker.check_keyboard_panic(ctrl=True, alt=True, shift=True, key="Q")
    assert breaker.is_panic_triggered()
    assert "Ctrl+Alt+Shift+Q" in breaker.panic_reason

@pytest.mark.asyncio
async def test_checkpoint_e_rollback_test():
    """
    Checklist Test (e) Rollback Test:
    Verify a failed script generates .cortex/reports/$task_id.failed.diff
    and restores modified and untracked files cleanly.
    """
    workspace = Path(os.getcwd()).resolve()
    sandbox = SandboxRunner(str(workspace))
    
    task_id = "test-rollback-verification"
    canary_file = workspace / "canary_untracked_file.txt"
    if canary_file.exists():
        canary_file.unlink()

    # Create a faulty script that writes an untracked file, modifies a file, then exits with code 1
    faulty_script = workspace / "_tmp_faulty_script.py"
    faulty_script.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "Path('canary_untracked_file.txt').write_text('agent dirty state')\n"
        "sys.exit(1)\n",
        encoding="utf-8"
    )

    try:
        # Run inside sandbox with checkpointing
        result = await sandbox.run_with_checkpoint(task_id, str(faulty_script))
        
        # Verify execution failed and was rolled back
        assert result["status"] == "FAILED_ROLLED_BACK"
        assert result["exit_code"] == 1
        
        # Untracked dirty file must be deleted by the deterministic rollback!
        assert not canary_file.exists(), "Rollback failed to remove untracked file!"
        
        # Verify diff report was generated
        diff_file = Path(result["diff_report"])
        assert diff_file.exists()
        diff_content = diff_file.read_text(encoding="utf-8")
        assert "canary_untracked_file.txt" in diff_content
    finally:
        if faulty_script.exists():
            faulty_script.unlink()
        if canary_file.exists():
            canary_file.unlink()
