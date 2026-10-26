"""CLI interface for CortexOS Obsidian Knowledge Vault, RAG & Pair Copilot.

Usage:
  python -m cortex.vault status
  python -m cortex.vault search <query>
  python -m cortex.vault list [--category CAT] [--tag TAG]
  python -m cortex.vault view <path>
  python -m cortex.vault sync [--remote URL]
  python -m cortex.vault pair <task>
  python -m cortex.vault add --title TITLE --content CONTENT [--path PATH]
"""

import sys
import argparse
import json
import asyncio

if sys.platform == "win32":
    try:
        if sys.stdout is not None:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr is not None:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from cortex.vault.vault_manager import get_vault
from cortex.vault.rag_engine import get_vault_rag
from cortex.vault.git_sync import get_vault_sync
from cortex.vault.copilot_pair import get_pair_copilot
from cortex.vault.system_cartographer import SystemCartographer
from cortex.vault.evolution_engine import SelfEvolutionEngine


def main():
    parser = argparse.ArgumentParser(
        prog="python -m cortex.vault",
        description="CortexOS Obsidian Knowledge Vault, Semantic RAG & Autonomous Pair Copilot"
    )
    parser.add_argument(
        "action",
        choices=["status", "search", "list", "view", "sync", "backup", "pair", "add", "cartography", "evolve", "ledger", "synthesize"],
        help="Action to perform"
    )
    parser.add_argument("query", nargs="?", default="", help="Search query, note path, or pair command")
    parser.add_argument("--remote", help="Private git backup remote URL")
    parser.add_argument("--title", help="Note title for add action")
    parser.add_argument("--content", help="Note content for add action")
    parser.add_argument("--path", help="Relative path for note")
    parser.add_argument("--category", help="Category filter")
    parser.add_argument("--tag", help="Tag filter")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    vault = get_vault()
    rag = get_vault_rag()
    sync = get_vault_sync()
    copilot = get_pair_copilot()

    if args.action == "status":
        v_stats = vault.get_stats()
        s_stats = sync.status()
        combined = {
            "vault": v_stats,
            "backup_git": s_stats
        }
        if args.json:
            print(json.dumps(combined, indent=2))
        else:
            print("=" * 68)
            print("📚 CORTEX-OS // OBSIDIAN KNOWLEDGE VAULT & BACKUP STATUS")
            print("=" * 68)
            print(f"  Vault Path:        {v_stats['vault_path']}")
            print(f"  Total Notes:       {v_stats['total_notes']}")
            print(f"  Total Word Count:  {v_stats['total_words']:,} words")
            print(f"  Categories:        {', '.join(v_stats['categories'])}")
            print(f"  Tags:              {', '.join(v_stats['tags'])}")
            print("-" * 68)
            print(f"  Isolated Git Dir:  {s_stats['git_dir']}")
            print(f"  Backup Status:     {s_stats['status_label']}")
            print(f"  Private Remote:    {s_stats['remote_url'] or 'Not configured (Local isolated only)'}")
            print(f"  Last Commit:       {s_stats['last_commit']}")
            print(f"  Last Sync Time:    {s_stats['last_sync'] or 'Never'}")
            print("=" * 68)

    elif args.action == "search":
        q = args.query.strip()
        if not q:
            print("Error: query string required for search.")
            sys.exit(1)
        results = rag.search(q, top_k=5, category=args.category)
        if args.json:
            print(json.dumps([r.to_dict() for r in results], indent=2))
        else:
            print("=" * 68)
            print(f"🔍 VAULT RAG SEARCH: '{q}' ({len(results)} matches)")
            print("=" * 68)
            for i, r in enumerate(results, 1):
                print(f"[{i}] {r.note_title} ({r.rel_path}#{r.header}) - Score: {r.score:.3f}")
                print(f"    Tags: {', '.join(r.tags) or 'None'}")
                print(f"    Matched: {', '.join(r.matched_terms)}")
                print(f"    Snippet: {r.snippet.replace(chr(10), ' ')[:180]}...")
                print("-" * 68)

    elif args.action == "list":
        notes = vault.list_notes(category=args.category, tag=args.tag)
        if args.json:
            print(json.dumps(notes, indent=2))
        else:
            print(f"Obsidian Vault Notes ({len(notes)}):")
            for n in notes:
                print(f"  - {n['rel_path']} ({n['word_count']} words) [{', '.join(n['tags'])}]")

    elif args.action == "view":
        p = args.query.strip()
        note = vault.get_note(p)
        if not note:
            print(f"Error: Note '{p}' not found.")
            sys.exit(1)
        print(note.raw_text)

    elif args.action in ["sync", "backup"]:
        print(f"[*] Synchronizing Obsidian Vault to backup repository...")
        res = sync.sync(remote_url=args.remote)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"[✓] {res.get('message')}")
            print(f"    Status:    {res.get('status')}")
            print(f"    Remote:    {res.get('remote', 'Local only')}")
            print(f"    Last Sync: {res.get('last_sync')}")

    elif args.action == "pair":
        task = args.query.strip()
        if not task:
            print("Error: Task description required for pair copilot.")
            sys.exit(1)
        print(f"[*] Running Pair Copilot for: '{task}'...")
        res = asyncio.run(copilot.execute_pair_request(task))
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("=" * 68)
            print("👥 CORTEX-OS // PAIR COPILOT EXECUTION")
            print("=" * 68)
            print(f"Prompt:          {res['prompt']}")
            print(f"Grounded Source: {', '.join(res['grounded_sources']) or 'Vault Baseline'}")
            print(f"Action Executed: {res['action_executed']}")
            print("-" * 68)
            print(f"Response:\n{res['user_response']}")
            print("=" * 68)

    elif args.action == "add":
        title = args.title or "Untitled Note"
        content = args.content or ""
        path = args.path or f"02_Pair_Programming/{title.replace(' ', '_')}.md"
        note = vault.save_note(path, content, title=title)
        rag._build_index()
        print(f"[✓] Note saved to {note.rel_path} ({note.word_count} words).")

    elif args.action == "cartography":
        print("[*] Running System Cartographer scan across host environment...")
        cart = SystemCartographer(vault.vault_path)
        res = cart.run_full_cartography_scan()
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("=" * 68)
            print("🛰️ CORTEX-OS // SYSTEM CARTOGRAPHY GROUND-TRUTH SCAN")
            print("=" * 68)
            print(f"  Scan Latency:       {res['latency_ms']:.1f}ms")
            print(f"  Toolchains Found:   {len(res['snapshot']['toolchains'])}")
            print(f"  Desktop Workspaces: {res['snapshot']['workspaces']['total_projects']}")
            print(f"  Primary LAN IP:     {res['snapshot']['network']['primary_lan_ip']}")
            print(f"  Detected Diffs:     {'; '.join(res['diffs'])}")
            print("=" * 68)

    elif args.action == "evolve":
        print("[*] Executing 5-phase autopoietic self-evolution cycle...")
        evo = SelfEvolutionEngine(vault.vault_path)
        res = evo.run_evolution_cycle(trigger_source="cli")
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("=" * 68)
            print("🧬 CORTEX-OS // AUTOPOIETIC SELF-EVOLUTION CYCLE")
            print("=" * 68)
            print(f"  Latency:            {res['latency_ms']:.1f}ms")
            print(f"  Health Index:       {res['health']['health_score']}% ({res['health']['status_label']})")
            print(f"  RAG Chunks Indexed: {res['rag_chunks']}")
            print(f"  Adapted Weights:    A:{res['weights']['analytic']} P:{res['weights']['pragmatic']} C:{res['weights']['cautious']}")
            print(f"  Git Backup Status:  {res['git_backup']}")
            print(f"  Diffs Reconciled:   {'; '.join(res['diffs'])}")
            print("=" * 68)

    elif args.action == "ledger":
        evo = SelfEvolutionEngine(vault.vault_path)
        health = evo.introspect_system_health()
        print("=" * 68)
        print("📜 CORTEX-OS // INTROSPECTION & HEALTH AUDIT")
        print("=" * 68)
        print(f"  Health Score:  {health['health_score']}% [{health['status_label']}]")
        print(f"  CPU Load:      {health['metrics']['cpu_percent']}%")
        print(f"  RAM Usage:     {health['metrics']['ram_percent']}% ({health['metrics']['ram_available_gb']} GB available)")
        print(f"  Disk Usage:    {health['metrics']['disk_percent']}%")
        if health["alerts"]:
            for a in health["alerts"]:
                print(f"  ! {a}")
        else:
            print("  Alerts:        None (Nominal)")
        print("=" * 68)

    elif args.action == "synthesize":
        name = args.title or args.query.strip() or "CustomDevWorkflow"
        evo = SelfEvolutionEngine(vault.vault_path)
        res = evo.synthesize_skill(
            name=name,
            trigger_phrases=[f"run {name.lower()}", f"execute {name.lower()}"],
            steps=[
                "Verify required toolchains in 05_System_State/Toolchains_and_Compilers.md",
                "Check workspace directory in 05_System_State/Filesystem_and_Workspaces.md",
                "Execute governed command sequence and log receipt to Active_Context.md"
            ]
        )
        print(f"[✓] Synthesized new skill: {res['skill_name']} -> {res['path']}")


if __name__ == "__main__":
    main()
