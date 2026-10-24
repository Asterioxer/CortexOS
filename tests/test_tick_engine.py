import pytest
import numpy as np
from cortex.workspace.tick_engine import (
    GWACognitiveTickEngine,
    IntrinsicDriveMonitor,
    HASSUMUncertaintyGate,
    GlobalWorkspaceState
)
from cortex.inference.client import LocalInferenceClient
from cortex.memory.blocks import WorkingMemoryManager
from cortex.memory.substrate import MemorySubstrate
from cortex.governance.policy_engine import PolicyEngine

def test_intrinsic_drive_entropy():
    monitor = IntrinsicDriveMonitor(num_clusters=4)
    state = GlobalWorkspaceState()
    
    # Generate 4 distinct vectors
    v1 = np.array([1.0, 0.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0, 0.0])
    v3 = np.array([0.0, 0.0, 1.0, 0.0])
    v4 = np.array([0.0, 0.0, 0.0, 1.0])
    
    # Initialize clusters
    monitor.compute_entropy_and_regulate(v1, state)
    monitor.compute_entropy_and_regulate(v2, state)
    monitor.compute_entropy_and_regulate(v3, state)
    monitor.compute_entropy_and_regulate(v4, state)
    
    # Test entropy on balanced thought
    balanced_v = np.array([0.5, 0.5, 0.5, 0.5])
    ent = monitor.compute_entropy_and_regulate(balanced_v, state)
    assert ent > 0.5
    assert state.current_temperature == state.base_temperature

    # Test entropy stagnation: submit identical vector repeatedly
    stagnant_v = np.array([1.0, 0.0, 0.0, 0.0])
    for _ in range(5):
        stagnant_ent = monitor.compute_entropy_and_regulate(stagnant_v, state)
    
    # Stagnation boosts temperature
    if stagnant_ent < 0.35:
        assert state.current_temperature > state.base_temperature

def test_hassum_uncertainty_gate():
    # 1. Coherent, tightly clustered vectors -> Should PASS
    coherent = [
        np.array([1.0, 0.05, 0.0], dtype=np.float32),
        np.array([0.98, 0.08, 0.0], dtype=np.float32),
        np.array([0.99, 0.02, 0.0], dtype=np.float32)
    ]
    res_pass = HASSUMUncertaintyGate.evaluate_samples(coherent)
    assert res_pass["semantic_density"] >= 0.68
    assert res_pass["pass"] is True

    # 2. Conflicting, orthogonal vectors -> Should FAIL
    divergent = [
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.0, 0.0], dtype=np.float32),
        np.array([0.0, 0.0, 1.0], dtype=np.float32)
    ]
    res_fail = HASSUMUncertaintyGate.evaluate_samples(divergent)
    assert res_fail["semantic_density"] < 0.68 or res_fail["semantic_entropy"] > 0.42
    assert res_fail["pass"] is False

@pytest.mark.asyncio
async def test_gwa_cognitive_tick(tmp_path):
    db_path = str(tmp_path / "tick_test.sqlite")
    memory = MemorySubstrate(db_path)
    wm = WorkingMemoryManager()
    policy = PolicyEngine()
    llm = LocalInferenceClient()
    
    engine = GWACognitiveTickEngine(
        llm_client=llm,
        memory_substrate=memory,
        working_memory=wm,
        skill_engine=None,
        policy_gate=policy
    )
    
    # Tick 1: Routine heartbeat
    tag1 = await engine.run_cognitive_tick(external_input=None)
    assert engine.state.tick_id == 1
    assert tag1 in ["[RESPONSE]", "[NO_OP]", "[THINK_MORE]"]
    
    # Verify first-person framing in trace
    assert "I " in engine.state.stm_buffer[-1]
    
    # Tick 2: Input perception requiring System 2 Swarm deliberation
    tag2 = await engine.run_cognitive_tick(external_input="Complex novel requirement requiring analysis.")
    assert engine.state.tick_id == 2
    assert len(engine.state.stm_buffer) >= 2
    assert "I thought:" in engine.state.stm_buffer[-1]
