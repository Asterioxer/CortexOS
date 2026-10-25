"""
Integrity Hash: 3d5f1c990a2b
Description: Audits workspace cache directories, build artifacts, and dangling temporary files for safe reclamation.
"""
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def get_dir_size(path: Path) -> int:
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except Exception:
                    pass
    except Exception:
        pass
    return total

def main():
    root = Path(__file__).resolve().parent.parent.parent.parent
    print("=== CORTEX-OS DISK SPACE & CACHE AUDITOR ===")
    print(f"Target Directory: {root}\n")

    CACHE_TARGETS = [
        "__pycache__",
        ".pytest_cache",
        ".coverage",
        "*.pyc",
        "*.pyo"
    ]

    total_reclaimable = 0
    found_items = []

    # Search for cache dirs
    for cache_name in ["__pycache__", ".pytest_cache"]:
        for d in root.rglob(cache_name):
            if ".venv" not in d.parts:
                sz = get_dir_size(d)
                total_reclaimable += sz
                found_items.append((str(d.relative_to(root)), sz, "Directory"))

    print(f"Discovered {len(found_items)} cache directories eligible for reclamation:")
    for path_str, sz, item_type in found_items:
        sz_kb = round(sz / 1024, 1)
        print(f"  * {path_str:<50} ({sz_kb:>6.1f} KB)")

    total_mb = round(total_reclaimable / (1024 * 1024), 2)
    print(f"\nTotal Recoverable Non-Destructive Space: {total_mb} MB")
    print("[STATUS]: Non-destructive inspection complete. No working tree files were deleted.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
