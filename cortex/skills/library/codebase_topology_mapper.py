"""
Integrity Hash: 4e81b2a9701d
Description: Maps codebase directory topology, measures lines of code, and indexes classes and functions.
"""
import ast
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def analyze_python_file(path: Path):
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(content)
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        lines = len(content.splitlines())
        return lines, classes, functions
    except Exception:
        return 0, [], []

def main():
    root = Path(__file__).resolve().parent.parent.parent.parent
    print(f"=== CORTEX-OS CODEBASE TOPOLOGY MAPPER ===")
    print(f"Target Root: {root}\n")

    py_files = sorted(list(root.rglob("*.py")))
    # Filter out .venv
    project_files = [f for f in py_files if ".venv" not in f.parts and "__pycache__" not in f.parts]
    
    total_loc = 0
    total_classes = 0
    total_functions = 0
    modules_report = []

    for f in project_files:
        rel = f.relative_to(root)
        loc, cls_list, fn_list = analyze_python_file(f)
        total_loc += loc
        total_classes += len(cls_list)
        total_functions += len(fn_list)
        modules_report.append((str(rel), loc, len(cls_list), len(fn_list)))

    modules_report.sort(key=lambda x: x[1], reverse=True)

    print(f"Indexed {len(project_files)} active Python modules:")
    print(f"Total Lines of Code: {total_loc:,} | Classes: {total_classes} | Functions/Methods: {total_functions}\n")
    print("Top Architectural Modules by Size:")
    for mod, loc, c_count, f_count in modules_report[:12]:
        print(f"  * {mod:<45} | {loc:>5} LOC | {c_count:>2} Classes | {f_count:>3} Functions")

    return 0

if __name__ == "__main__":
    sys.exit(main())
