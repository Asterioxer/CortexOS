import os
import subprocess
import shutil
import time
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List


class VaultSync:
    """Manages dedicated private repository backup & Git synchronization for the Obsidian Vault.
    
    Uses an isolated git directory (--git-dir=.cortex/vault_backup.git) so that the vault's
    backup sync operates independently of the main CortexOS project repository.
    """

    def __init__(self, workspace_root: Optional[Path] = None, vault_dir: Optional[Path] = None):
        self.workspace_root = workspace_root or Path(__file__).resolve().parent.parent.parent
        self.vault_dir = vault_dir or (self.workspace_root / "cortex_vault").resolve()
        self.git_dir = (self.workspace_root / ".cortex" / "vault_backup.git").resolve()
        self.backup_dir = (self.workspace_root / ".cortex" / "backups").resolve()
        self.last_sync_file = self.workspace_root / ".cortex" / "vault_last_sync.txt"

        self.git_dir.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _run_git(self, args: List[str]) -> Tuple[int, str, str]:
        """Runs a git command targeting the isolated vault git directory."""
        cmd = [
            "git",
            f"--git-dir={self.git_dir}",
            f"--work-tree={self.vault_dir}"
        ] + args
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.vault_dir),
                check=False
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as e:
            return 1, "", str(e)

    def is_initialized(self) -> bool:
        """Returns True if the vault backup Git database is initialized."""
        head_file = self.git_dir / "HEAD"
        return head_file.exists()

    def init_repo(self, remote_url: Optional[str] = None) -> Dict[str, Any]:
        """Initializes the isolated backup git repository and creates the initial commit."""
        self.git_dir.parent.mkdir(parents=True, exist_ok=True)
        self.vault_dir.mkdir(parents=True, exist_ok=True)

        # 1. git init
        rc, out, err = self._run_git(["init"])
        if rc != 0:
            return {"status": "ERROR", "error": f"Failed to init git: {err}"}

        # 2. Set default branch to main
        self._run_git(["branch", "-M", "main"])

        # 3. If remote provided, set origin
        if remote_url:
            self.set_remote(remote_url)

        # 4. Stage and commit initial vault
        self.commit("chore: initial cortex obsidian vault backup")

        return {
            "status": "SUCCESS",
            "message": "Vault backup repository initialized.",
            "git_dir": str(self.git_dir),
            "remote": remote_url
        }

    def set_remote(self, remote_url: str) -> Dict[str, Any]:
        """Configures or updates the private backup remote URL."""
        if not self.is_initialized():
            self.init_repo()

        # Check existing remote
        rc, out, _ = self._run_git(["remote", "get-url", "origin"])
        if rc == 0:
            self._run_git(["remote", "set-url", "origin", remote_url])
        else:
            self._run_git(["remote", "add", "origin", remote_url])

        return {"status": "SUCCESS", "remote_url": remote_url}

    def get_remote(self) -> Optional[str]:
        """Retrieves configured remote URL if present."""
        if not self.is_initialized():
            return None
        rc, out, _ = self._run_git(["remote", "get-url", "origin"])
        return out if rc == 0 and out else None

    def commit(self, message: Optional[str] = None) -> Dict[str, Any]:
        """Stages all notes in cortex_vault and commits them."""
        if not self.is_initialized():
            self.init_repo()

        msg = message or f"chore(vault): auto-sync backup ({time.strftime('%Y-%m-%d %H:%M:%S')})"
        self._run_git(["add", "-A"])
        rc, out, err = self._run_git(["commit", "-m", msg])

        has_changes = rc == 0
        return {
            "status": "COMMITTED" if has_changes else "NO_CHANGES",
            "message": out if has_changes else "Working tree clean, no new vault changes.",
            "raw_output": out or err
        }

    def sync(self, remote_url: Optional[str] = None) -> Dict[str, Any]:
        """Commits local vault changes and syncs with the private remote repository."""
        if not self.is_initialized():
            self.init_repo(remote_url=remote_url)

        if remote_url:
            self.set_remote(remote_url)

        target_remote = self.get_remote()

        # 1. Local commit first
        commit_res = self.commit()

        if not target_remote:
            # No remote configured: record local backup timestamp
            self._record_sync_timestamp()
            return {
                "status": "LOCAL_BACKUP_ONLY",
                "message": "Vault changes committed to local isolated backup. Configure a private remote URL to enable cloud push.",
                "commit_status": commit_res["status"],
                "last_sync": self.get_last_sync_time()
            }

        # 2. Remote pull & push
        pull_rc, pull_out, pull_err = self._run_git(["pull", "origin", "main", "--rebase"])
        push_rc, push_out, push_err = self._run_git(["push", "-u", "origin", "main"])

        if push_rc == 0:
            self._record_sync_timestamp()
            return {
                "status": "SYNCED",
                "message": f"Successfully backed up and synchronized vault with private remote {target_remote}.",
                "remote": target_remote,
                "last_sync": self.get_last_sync_time()
            }
        else:
            return {
                "status": "PUSH_FAILED",
                "error": f"Failed to push to remote: {push_err or push_out}",
                "message": "Vault was saved locally, but remote push failed. Check network or remote permissions.",
                "remote": target_remote
            }

    def export_backup_zip(self, dest_path: Optional[Path] = None) -> Path:
        """Creates a standalone .zip archive of the entire Obsidian Vault for offline backup."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        target_zip = dest_path or (self.backup_dir / f"cortex_vault_backup_{timestamp}.zip")
        target_zip.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(self.vault_dir):
                for f in files:
                    full_p = Path(root) / f
                    arcname = full_p.relative_to(self.vault_dir.parent).as_posix()
                    zf.write(full_p, arcname=arcname)

        return target_zip

    def _record_sync_timestamp(self) -> None:
        try:
            self.last_sync_file.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
        except Exception:
            pass

    def get_last_sync_time(self) -> Optional[str]:
        if self.last_sync_file.exists():
            try:
                return self.last_sync_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass
        return None

    def status(self) -> Dict[str, Any]:
        """Returns comprehensive status of vault git backup and remote synchronization."""
        initialized = self.is_initialized()
        remote = self.get_remote()
        last_sync = self.get_last_sync_time()

        uncommitted = 0
        last_commit = "None"
        branch = "None"

        if initialized:
            # Check git status --porcelain
            rc, out, _ = self._run_git(["status", "--porcelain"])
            if rc == 0 and out:
                uncommitted = len(out.splitlines())

            # Check branch
            rc, out, _ = self._run_git(["branch", "--show-current"])
            if rc == 0 and out:
                branch = out

            # Check last commit
            rc, out, _ = self._run_git(["log", "-1", "--format=%h - %s (%cr)"])
            if rc == 0 and out:
                last_commit = out

        return {
            "initialized": initialized,
            "git_dir": str(self.git_dir),
            "vault_dir": str(self.vault_dir),
            "remote_url": remote,
            "branch": branch,
            "uncommitted_files": uncommitted,
            "last_commit": last_commit,
            "last_sync": last_sync,
            "status_label": "SYNCED" if uncommitted == 0 and last_commit != "None" else "PENDING_CHANGES"
        }


_GLOBAL_VAULT_SYNC: Optional[VaultSync] = None


def get_vault_sync() -> VaultSync:
    global _GLOBAL_VAULT_SYNC
    if _GLOBAL_VAULT_SYNC is None:
        _GLOBAL_VAULT_SYNC = VaultSync()
    return _GLOBAL_VAULT_SYNC
