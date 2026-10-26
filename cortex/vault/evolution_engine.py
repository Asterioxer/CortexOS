"""CortexOS Autonomous Self-Evolution Engine.

Provides closed-loop autopoietic evolution:
1. Continuous environmental cartography diff tracking.
2. Cognitive introspection and health scoring.
3. Dynamic heuristic adaptation for tri-perspective arbitration.
4. Procedural skill synthesis directly into the Obsidian Vault.
5. Grounded knowledge consolidation and isolated Git backup.
"""

from __future__ import annotations

import os
import sys
import re
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import psutil

from cortex.vault.system_cartographer import SystemCartographer
from cortex.vault.vault_manager import ObsidianVault
from cortex.vault.rag_engine import VaultRAG
from cortex.vault.git_sync import VaultSync


class SelfEvolutionEngine:
    """Manages system introspection, heuristic adaptation, skill synthesis, and autonomous evolution."""

    def __init__(self, vault_path: Optional[str | Path] = None):
        if vault_path is None:
            self.vault_path = Path(__file__).resolve().parent.parent.parent / "cortex_vault"
        else:
            self.vault_path = Path(vault_path)

        self.evolution_dir = self.vault_path / "06_Self_Evolution"
        self.evolution_dir.mkdir(parents=True, exist_ok=True)
        self.skills_dir = self.vault_path / "04_Skills_Catalog"
        self.skills_dir.mkdir(parents=True, exist_ok=True)

        self.cartographer = SystemCartographer(self.vault_path)
        self.vault = ObsidianVault(self.vault_path)
        self.rag = VaultRAG(self.vault)
        self.sync = VaultSync(self.vault_path)

        # Dynamic heuristic weights (Analytic, Pragmatic, Cautious)
        self.weights = {
            "analytic": 0.33,
            "pragmatic": 0.34,
            "cautious": 0.33
        }

    def introspect_system_health(self) -> Dict[str, Any]:
        """Compute host health index (0-100%) and resource headroom."""
        mem = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=0.1)

        disk_pct = 0.0
        try:
            disk_pct = psutil.disk_usage("C:\\" if sys.platform == "win32" else "/").percent
        except Exception:
            pass

        # Calculate health score: 100 - weighted resource pressures
        pressure = (mem.percent * 0.35) + (disk_pct * 0.25) + (cpu_pct * 0.20)
        health_score = max(0.0, min(100.0, 100.0 - pressure))

        alerts: List[str] = []
        if mem.percent > 90.0:
            alerts.append("CRITICAL: Physical RAM utilization exceeded 90%.")
        elif mem.percent > 82.0:
            alerts.append("WARNING: Physical RAM pressure elevated (>82%).")

        if disk_pct > 88.0:
            alerts.append(f"WARNING: Primary disk utilization elevated ({disk_pct}%).")

        status_label = "NOMINAL"
        if health_score < 60.0:
            status_label = "CONSTRAINED"
        elif health_score < 75.0:
            status_label = "MODERATE"

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "health_score": round(health_score, 1),
            "status_label": status_label,
            "metrics": {
                "cpu_percent": cpu_pct,
                "ram_percent": mem.percent,
                "ram_available_gb": round(mem.available / (1024**3), 2),
                "ram_total_gb": round(mem.total / (1024**3), 2),
                "disk_percent": disk_pct
            },
            "alerts": alerts
        }

    def record_introspection(
        self,
        event_type: str,
        description: str,
        metrics: Optional[Dict[str, Any]] = None,
        perspective_used: str = "Pragmatic"
    ) -> Dict[str, Any]:
        """Append a structured reflection record into '06_Self_Evolution/Introspection_Ledger.md'."""
        ledger_path = self.evolution_dir / "Introspection_Ledger.md"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        metrics_summary = ""
        if metrics:
            metrics_summary = ", ".join([f"{k}: `{v}`" for k, v in metrics.items()])

        entry_block = f"""
### [{now_str}] {event_type}
- **Description**: {description}
- **Arbitration Perspective**: `{perspective_used}`
- **System Metrics**: {metrics_summary or 'Nominal telemetry'}
"""
        try:
            if ledger_path.exists():
                content = ledger_path.read_text(encoding="utf-8")
                # Insert below the Milestone History header
                target_header = "## 📊 Evolutionary Milestone History\n"
                if target_header in content:
                    idx = content.find(target_header) + len(target_header)
                    new_content = content[:idx] + entry_block + content[idx:]
                else:
                    new_content = content + "\n" + entry_block
                ledger_path.write_text(new_content, encoding="utf-8")
            else:
                ledger_path.write_text(f"# 📜 Autonomous Introspection Ledger\n\n## 📊 Evolutionary Milestone History\n{entry_block}", encoding="utf-8")
        except Exception as e:
            return {"status": "error", "message": str(e)}

        return {
            "status": "recorded",
            "timestamp": now_str,
            "event_type": event_type
        }

    def adapt_heuristics(
        self,
        feedback_score: float = 1.0,
        recent_perspective: str = "Pragmatic",
        health_score: float = 80.0
    ) -> Dict[str, float]:
        """Dynamically tune tri-perspective arbitration weights based on performance and health."""
        # If system is under resource pressure, increase Cautious weight
        if health_score < 70.0:
            self.weights["cautious"] += 0.05
            self.weights["pragmatic"] -= 0.03
            self.weights["analytic"] -= 0.02
        elif health_score >= 80.0 and feedback_score >= 0.8:
            # Velocity is good; bias slightly towards Pragmatic execution
            self.weights["pragmatic"] += 0.03
            self.weights["cautious"] -= 0.02
            self.weights["analytic"] -= 0.01

        # Keep weights within [0.15, 0.70] and normalize sum to 1.0
        for k in self.weights:
            self.weights[k] = max(0.15, min(0.70, self.weights[k]))

        total = sum(self.weights.values())
        for k in self.weights:
            self.weights[k] = round(self.weights[k] / total, 3)

        # Update Heuristic_Adaptation_Matrix.md
        matrix_path = self.evolution_dir / "Heuristic_Adaptation_Matrix.md"
        try:
            if matrix_path.exists():
                c = matrix_path.read_text(encoding="utf-8")
                c = re.sub(r"\|\s*\*\*`Analytic`\*\*\s*\|\s*`[0-9\.]+`", f"| **`Analytic`** | `{self.weights['analytic']}`", c)
                c = re.sub(r"\|\s*\*\*`Pragmatic`\*\*\s*\|\s*`[0-9\.]+`", f"| **`Pragmatic`** | `{self.weights['pragmatic']}`", c)
                c = re.sub(r"\|\s*\*\*`Cautious`\*\*\s*\|\s*`[0-9\.]+`", f"| **`Cautious`** | `{self.weights['cautious']}`", c)
                matrix_path.write_text(c, encoding="utf-8")
        except Exception:
            pass

        return dict(self.weights)

    def synthesize_skill(
        self,
        name: str,
        trigger_phrases: List[str],
        steps: List[str],
        category: str = "Developer Automation",
        grounded_tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Synthesize a new procedural skill into the Obsidian Vault and Skills Catalog."""
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "", name.replace(" ", "_"))
        skill_file = self.skills_dir / f"Skill_{safe_name}.md"

        tools_list = grounded_tools or ["python", "git"]
        tools_md = "\n".join([f"  - \"{t}\"" for t in tools_list])
        triggers_md = "\n".join([f"  - \"{tp}\"" for tp in trigger_phrases])
        steps_md = "\n".join([f"{i}. {s}" for i, s in enumerate(steps, 1)])

        content = f"""---
title: "Skill: {name}"
type: "skill_definition"
category: "{category}"
triggers:
{triggers_md}
grounded_toolchains:
{tools_md}
governance_tier: 2
created_at: "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
status: "active"
---

# ⚡ Skill: {name}

Autopoietically synthesized by [[06_Self_Evolution/Skill_Synthesis_Engine|Skill Synthesis Engine]].

## 🎯 Trigger Keywords
{triggers_md}

## 🛠️ Required Grounded Toolchains
{tools_md}

## 📋 Execution Steps
{steps_md}

---
> [!NOTE] Copilot Dispatch
> [[02_Pair_Programming/Pair_Programming_Copilot|Pair Copilot]] automatically triggers this playbook upon matching any of the above phrases.
"""
        skill_file.write_text(content, encoding="utf-8")

        # Register in Skills_Registry.md if not already present
        registry_file = self.skills_dir / "Skills_Registry.md"
        try:
            if registry_file.exists():
                reg_content = registry_file.read_text(encoding="utf-8")
                row = f"| **`{name}`** | `{category}` | [[04_Skills_Catalog/Skill_{safe_name}|Skill_{safe_name}]] | Tier 2 |"
                if f"Skill_{safe_name}" not in reg_content:
                    reg_content += f"\n{row}\n"
                    registry_file.write_text(reg_content, encoding="utf-8")
        except Exception:
            pass

        return {
            "status": "synthesized",
            "skill_name": name,
            "path": f"04_Skills_Catalog/Skill_{safe_name}.md",
            "triggers_count": len(trigger_phrases)
        }

    def run_evolution_cycle(self, trigger_source: str = "autonomous") -> Dict[str, Any]:
        """Execute a complete 5-phase autopoietic self-evolution cycle."""
        t0 = time.time()

        # Phase 1: Environmental Cartography
        cart_res = self.cartographer.run_full_cartography_scan()
        diffs = cart_res.get("diffs", [])

        # Phase 2: System Health Introspection
        health = self.introspect_system_health()

        # Phase 3: Heuristic Adaptation
        new_weights = self.adapt_heuristics(
            feedback_score=1.0,
            recent_perspective="Pragmatic",
            health_score=health["health_score"]
        )

        # Phase 4: Re-index RAG Chunks
        self.vault.scan_notes(force=True)
        self.rag = VaultRAG(self.vault)
        total_chunks = len(self.rag._chunks)

        # Phase 5: Versioned Memory Consolidation (Git Auto-Backup)
        sync_res = self.sync.commit(
            message=f"chore(evolution): autopoietic evolution cycle ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        )

        dt = (time.time() - t0) * 1000

        # Record event in Introspection Ledger
        ledger_desc = f"Self-evolution cycle completed in {dt:.1f}ms. Health: {health['health_score']}% ({health['status_label']}). Indexed {total_chunks} RAG knowledge chunks. Diff: {'; '.join(diffs[:2])}"
        self.record_introspection(
            event_type="Autopoietic Self-Evolution Cycle",
            description=ledger_desc,
            metrics={
                "health_score": f"{health['health_score']}%",
                "rag_chunks": total_chunks,
                "weights": f"A:{new_weights['analytic']}, P:{new_weights['pragmatic']}, C:{new_weights['cautious']}"
            },
            perspective_used="Pragmatic"
        )

        # Update Active Context living document
        self.vault.update_active_context(
            active_goal=f"Self-Evolution Cycle Completed ({datetime.now().strftime('%H:%M:%S')})",
            details={
                "Trigger": trigger_source,
                "Action Dispatched": "run_evolution_cycle",
                "Health Score": f"{health['health_score']}% ({health['status_label']})",
                "Grounded Sources": "06_Self_Evolution/Autonomous_Evolution_Architecture.md, 06_Self_Evolution/Introspection_Ledger.md"
            }
        )

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "latency_ms": round(dt, 2),
            "health": health,
            "weights": new_weights,
            "rag_chunks": total_chunks,
            "diffs": diffs,
            "git_backup": sync_res.get("status_label")
        }
