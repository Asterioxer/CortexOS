"""
Integrity Hash: 8b1c4e9023fa
Description: Audits the current repository branch, staging area, uncommitted changes, and checkpoint status.
"""
import sys
import subprocess
from pathlib import Path

def run_git(args):
    res = subprocess.run(["git"] + args, capture_output=True, text=True)
    return res.stdout.strip()

def main():
    print("=== GIT WORKING-TREE & GOVERNANCE AUDIT ===")
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    head_sha = run_git(["rev-parse", "--short", "HEAD"])
    status = run_git(["status", "--short"])
    
    print(f"Active Branch: {branch} (HEAD: {head_sha})")
    
    if not status:
        print("Working Tree: CLEAN (No uncommitted modifications)")
    else:
        lines = status.splitlines()
        print(f"Working Tree: DIRTY ({len(lines)} modified/untracked files)")
        for l in lines[:10]:
            print(f"  {l}")
        if len(lines) > 10:
            print(f"  ... and {len(lines) - 10} more files")

    # Check shadow checkpoints
    checkpoints = run_git(["for-each-ref", "--count=3", "--format=%(refname:short) (Commit: %(objectname:short))", "refs/checkpoints/"])
    if checkpoints:
        print("\nRecent Shadow Checkpoints:")
        for cp in checkpoints.splitlines():
            print(f"  * {cp}")
            
    return 0

if __name__ == "__main__":
    sys.exit(main())
