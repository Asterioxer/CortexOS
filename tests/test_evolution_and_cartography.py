"""Unit and Integration Tests for CortexOS System Cartographer & Self-Evolution Engine."""

import pytest
import os
import shutil
from pathlib import Path

from cortex.vault.system_cartographer import SystemCartographer
from cortex.vault.evolution_engine import SelfEvolutionEngine
from cortex.vault.vault_manager import ObsidianVault


@pytest.fixture
def temp_vault(tmp_path):
    vault_dir = tmp_path / "test_cortex_vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    (vault_dir / ".obsidian").mkdir()
    (vault_dir / "00_Index.md").write_text("# Test Index\n[[05_System_State/Hardware_Topology]]\n", encoding="utf-8")
    return vault_dir


def test_system_cartographer_probe_hardware(temp_vault):
    cart = SystemCartographer(vault_path=temp_vault)
    hw = cart.probe_hardware()
    assert "cpu" in hw
    assert "memory" in hw
    assert "disks" in hw
    assert hw["cpu"]["physical_cores"] > 0
    assert hw["memory"]["total_gb"] > 0.0


def test_system_cartographer_probe_os(temp_vault):
    cart = SystemCartographer(vault_path=temp_vault)
    os_env = cart.probe_os_environment()
    assert "caption" in os_env
    assert "user" in os_env
    assert "hostname" in os_env
    assert len(os_env["shells"]) > 0


def test_system_cartographer_probe_toolchains(temp_vault):
    cart = SystemCartographer(vault_path=temp_vault)
    tools = cart.probe_toolchains()
    assert isinstance(tools, dict)
    assert "python" in tools
    assert tools["python"]["path"] != ""


def test_system_cartographer_scan_and_diff(temp_vault):
    cart = SystemCartographer(vault_path=temp_vault)
    res = cart.run_full_cartography_scan()
    assert "snapshot" in res
    assert "diffs" in res
    assert res["latency_ms"] > 0.0

    # Verify generated markdown files in 05_System_State
    state_dir = temp_vault / "05_System_State"
    assert (state_dir / "Hardware_Topology.md").exists()
    assert (state_dir / "OS_and_Kernel_Environment.md").exists()
    assert (state_dir / "Toolchains_and_Compilers.md").exists()
    assert (state_dir / "Network_and_Interfaces.md").exists()
    assert (state_dir / "Filesystem_and_Workspaces.md").exists()


def test_evolution_engine_health_introspection(temp_vault):
    evo = SelfEvolutionEngine(vault_path=temp_vault)
    health = evo.introspect_system_health()
    assert "health_score" in health
    assert 0.0 <= health["health_score"] <= 100.0
    assert health["status_label"] in ["NOMINAL", "MODERATE", "CONSTRAINED"]
    assert "cpu_percent" in health["metrics"]
    assert "ram_percent" in health["metrics"]


def test_evolution_engine_record_introspection(temp_vault):
    evo = SelfEvolutionEngine(vault_path=temp_vault)
    res = evo.record_introspection(
        event_type="Test Anomaly Reconciliation",
        description="Verified test self-reflection logging.",
        metrics={"test_metric": 42},
        perspective_used="Analytic"
    )
    assert res["status"] == "recorded"
    ledger_path = temp_vault / "06_Self_Evolution" / "Introspection_Ledger.md"
    assert ledger_path.exists()
    content = ledger_path.read_text(encoding="utf-8")
    assert "Test Anomaly Reconciliation" in content
    assert "`Analytic`" in content


def test_evolution_engine_adapt_heuristics(temp_vault):
    evo = SelfEvolutionEngine(vault_path=temp_vault)
    weights = evo.adapt_heuristics(feedback_score=0.9, recent_perspective="Pragmatic", health_score=85.0)
    assert "analytic" in weights
    assert "pragmatic" in weights
    assert "cautious" in weights
    total = sum(weights.values())
    assert abs(total - 1.0) < 0.01


def test_evolution_engine_synthesize_skill(temp_vault):
    evo = SelfEvolutionEngine(vault_path=temp_vault)
    res = evo.synthesize_skill(
        name="AutoBuildDockerCluster",
        trigger_phrases=["build docker cluster", "spin up docker containers"],
        steps=[
            "Inspect Docker daemon in 05_System_State/Toolchains_and_Compilers.md",
            "Run docker-compose up -d in sandbox"
        ],
        category="DevOps Automation"
    )
    assert res["status"] == "synthesized"
    skill_file = temp_vault / "04_Skills_Catalog" / "Skill_AutoBuildDockerCluster.md"
    assert skill_file.exists()
    content = skill_file.read_text(encoding="utf-8")
    assert "AutoBuildDockerCluster" in content
    assert "build docker cluster" in content


def test_evolution_engine_run_evolution_cycle(temp_vault):
    evo = SelfEvolutionEngine(vault_path=temp_vault)
    res = evo.run_evolution_cycle(trigger_source="unit_test")
    assert "latency_ms" in res
    assert "health" in res
    assert "weights" in res
    assert "rag_chunks" in res
    assert "diffs" in res
