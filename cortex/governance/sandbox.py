import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from cortex.governance.checkpoint import GitShadowCheckpointManager
from cortex.governance.policy_engine import PolicyEngine, PolicyVerdict

class SandboxRunner:
    """
    Subprocess sandbox runner with deterministic Git rollback and environment sanitization.
    """
    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = Path(workspace_dir or os.getcwd()).resolve()
        self.checkpoint_mgr = GitShadowCheckpointManager(str(self.workspace_dir))
        self.policy_engine = PolicyEngine()

    def get_os_profile(self) -> Dict[str, Any]:
        """Provides environmental somatosensory info to Tool Generator."""
        return {
            "platform": sys.platform,
            "os_name": os.name,
            "workspace": str(self.workspace_dir),
            "python_executable": sys.executable,
        }

    def _sanitize_env(self) -> Dict[str, str]:
        """Strips credentials and tokens from child process environment."""
        clean_env = os.environ.copy()
        denied_env_keys = [
            "AWS_SECRET_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "AWS_SESSION_TOKEN",
            "GITHUB_TOKEN", "GH_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
            "GEMINI_API_KEY", "SSH_AUTH_SOCK"
        ]
        for key in denied_env_keys:
            clean_env.pop(key, None)
        return clean_env

    async def run_with_checkpoint(
        self,
        task_id: str,
        script_path: str,
        args: Optional[List[str]] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Runs a script inside isolated subprocess with pre-task snapshotting and deterministic rollback on error.
        """
        # 1. Pre-execution policy check
        action = {"action": "run_sandboxed_script", "resource": script_path}
        evaluation = self.policy_engine.evaluate(action, {"checkpoint_active": True})
        if evaluation.status == PolicyVerdict.DENY:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Policy DENY: {evaluation.reason}",
                "status": "DENIED"
            }

        # 2. Take deterministic shadow checkpoint
        pre_commit = self.checkpoint_mgr.create_checkpoint(task_id, "pre")

        cmd = [sys.executable, script_path] + (args or [])
        clean_env = self._sanitize_env()

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.workspace_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=clean_env
            )
            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode

            if exit_code != 0:
                # Execution failed: record failed state diff and roll back deterministically
                self.checkpoint_mgr.create_checkpoint(task_id, "failed")
                diff_report = self.checkpoint_mgr.create_failure_report(task_id)
                self.checkpoint_mgr.restore_checkpoint(task_id, "pre")
                return {
                    "exit_code": exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
                    "status": "FAILED_ROLLED_BACK",
                    "diff_report": diff_report
                }

            return {
                "exit_code": 0,
                "stdout": stdout,
                "stderr": stderr,
                "status": "SUCCESS"
            }

        except subprocess.TimeoutExpired as te:
            self.checkpoint_mgr.create_checkpoint(task_id, "failed")
            self.checkpoint_mgr.restore_checkpoint(task_id, "pre")
            return {
                "exit_code": -2,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds.",
                "status": "TIMEOUT_ROLLED_BACK"
            }
        except Exception as e:
            self.checkpoint_mgr.restore_checkpoint(task_id, "pre")
            return {
                "exit_code": -3,
                "stdout": "",
                "stderr": f"Unexpected execution exception: {str(e)}",
                "status": "ERROR_ROLLED_BACK"
            }

    async def run_verified_skill(
        self,
        task_id: str,
        skill_path: str,
        args: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Runs a crystallized, verified skill with safety containment."""
        return await self.run_with_checkpoint(task_id, skill_path, timeout=30)
