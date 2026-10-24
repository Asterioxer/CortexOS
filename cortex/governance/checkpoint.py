import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class GitShadowCheckpointManager:
    """
    Deterministic Working-Tree Rollback Engine using GIT_INDEX_FILE.
    
    Captures modified and untracked files in under 1 second without moving HEAD.
    Pins commits under refs/checkpoints/$task_id/ to prevent git gc pruning.
    Also snapshots stateful local databases (cortex_memory.sqlite*) and .env.
    """
    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = Path(workspace_dir or os.getcwd()).resolve()
        self.snapshots_dir = self.workspace_dir / ".cortex" / "snapshots"
        self.reports_dir = self.workspace_dir / ".cortex" / "reports"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _run_git(self, args: List[str], env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
        current_env = os.environ.copy()
        if env:
            current_env.update(env)
        proc = subprocess.run(
            ["git"] + args,
            cwd=str(self.workspace_dir),
            capture_output=True,
            text=True,
            env=current_env
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

    def create_checkpoint(self, task_id: str, label: str = "pre") -> str:
        """Creates a deterministic shadow commit pinned under refs/checkpoints/$task_id/$label."""
        # 1. Locate .git directory
        code, git_dir, err = self._run_git(["rev-parse", "--git-dir"])
        if code != 0:
            raise RuntimeError(f"Not a git repository: {err}")

        git_dir_path = (self.workspace_dir / git_dir).resolve()
        real_index = git_dir_path / "index"

        with tempfile.NamedTemporaryFile(delete=False) as tmp_f:
            tmp_index_path = tmp_f.name

        try:
            # 2. Copy current index to temporary index file
            if real_index.exists():
                shutil.copy2(real_index, tmp_index_path)

            shadow_env = {"GIT_INDEX_FILE": tmp_index_path}

            # 3. Stage all modified and untracked files in shadow index
            code, out, err = self._run_git(["add", "-A"], env=shadow_env)
            if code != 0:
                raise RuntimeError(f"Failed to add files to shadow index: {err}")

            # 4. Write tree object
            code, tree_sha, err = self._run_git(["write-tree"], env=shadow_env)
            if code != 0:
                raise RuntimeError(f"Failed to write tree: {err}")

            # 5. Commit tree object pointing to HEAD
            code, commit_sha, err = self._run_git([
                "commit-tree", tree_sha, "-p", "HEAD",
                "-m", f"cortex-checkpoint: {task_id} ({label})"
            ])
            if code != 0:
                # If repository has no HEAD commit yet (empty repo), commit without parent
                code, commit_sha, err = self._run_git([
                    "commit-tree", tree_sha,
                    "-m", f"cortex-checkpoint: {task_id} ({label})"
                ])
                if code != 0:
                    raise RuntimeError(f"Failed to commit tree: {err}")

            # 6. Pin reference under refs/checkpoints/$task_id/$label
            ref_path = f"refs/checkpoints/{task_id}/{label}"
            code, _, err = self._run_git(["update-ref", ref_path, commit_sha])
            if code != 0:
                raise RuntimeError(f"Failed to update ref {ref_path}: {err}")

            # 7. Snapshot stateful files
            target_snapshot_dir = self.snapshots_dir / task_id / label
            target_snapshot_dir.mkdir(parents=True, exist_ok=True)
            for fname in [".env", "cortex_memory.sqlite", "cortex_memory.sqlite-wal", "cortex_memory.sqlite-shm"]:
                src = self.workspace_dir / fname
                if src.exists():
                    shutil.copy2(src, target_snapshot_dir / fname)

            return commit_sha
        finally:
            if os.path.exists(tmp_index_path):
                os.remove(tmp_index_path)

    def restore_checkpoint(self, task_id: str, label: str = "pre") -> bool:
        """Restores working tree deterministically to refs/checkpoints/$task_id/$label."""
        ref = f"refs/checkpoints/{task_id}/{label}"
        code, commit_sha, _ = self._run_git(["rev-parse", "--verify", "--quiet", ref])
        if code != 0:
            raise FileNotFoundError(f"Checkpoint not found for task '{task_id}' at {ref}")

        # Undo must be undoable: snapshot current dirty state before rollback
        timestamp = int(time.time())
        self.create_checkpoint(task_id, f"before-restore-{timestamp}")

        # Stage untracked files so git restore removes them cleanly
        self._run_git(["add", "-A"])
        
        # Restore both staged and working tree files from checkpoint ref
        code, out, err = self._run_git(["restore", f"--source={ref}", "--staged", "--worktree", "--", "."])
        if code != 0:
            raise RuntimeError(f"Git restore failed: {err}")

        # Unstage files so workspace is clean
        self._run_git(["reset", "-q"])

        # Restore local SQLite DBs and stateful files
        src_snapshot_dir = self.snapshots_dir / task_id / label
        if src_snapshot_dir.exists():
            for item in src_snapshot_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, self.workspace_dir / item.name)

        return True

    def create_failure_report(self, task_id: str) -> Optional[str]:
        """Generates unified diff between pre checkpoint and failed checkpoint."""
        pre_ref = f"refs/checkpoints/{task_id}/pre"
        failed_ref = f"refs/checkpoints/{task_id}/failed"
        code, diff_out, _ = self._run_git(["diff", pre_ref, failed_ref])
        if code == 0:
            report_file = self.reports_dir / f"{task_id}.failed.diff"
            report_file.write_text(diff_out, encoding="utf-8")
            return str(report_file)
        return None
