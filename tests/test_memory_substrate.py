import pytest
import time
import numpy as np
from cortex.memory.blocks import WorkingMemoryManager, MemoryBlock
from cortex.memory.substrate import MemorySubstrate
from cortex.embodiment.mcp_bridge import MCPDesktopBridge, PerceptualCircuitBreaker

def test_working_memory_blocks():
    mgr = WorkingMemoryManager()
    
    # 1. Verify 4 pinned blocks exist
    assert "persona_self" in mgr.blocks
    assert "human_profile" in mgr.blocks
    assert "workspace_state" in mgr.blocks
    assert "scratchpad_stm" in mgr.blocks
    
    # 2. Append and replace operations
    mgr.core_memory_append("scratchpad_stm", "Investigating issue #42.")
    assert "Investigating issue #42." in mgr.get_block("scratchpad_stm").value
    
    mgr.core_memory_replace("scratchpad_stm", "issue #42", "feature #99")
    assert "feature #99" in mgr.get_block("scratchpad_stm").value
    
    # 3. Memory rethink
    mgr.memory_rethink("scratchpad_stm", "Distilled single goal: ship v1.0.")
    assert mgr.get_block("scratchpad_stm").value == "Distilled single goal: ship v1.0."
    
    # 4. Jinja compile
    compiled = mgr.compile()
    assert "<memory_block label=\"persona_self\"" in compiled
    assert "Distilled single goal: ship v1.0." in compiled

def test_working_memory_char_limit():
    block = MemoryBlock(label="test_block", description="test", value="hello", char_limit=20)
    with pytest.raises(ValueError, match="exceeded limit"):
        block.append("this string is much too long to fit inside the twenty character limit")

@pytest.mark.asyncio
async def test_memory_substrate_tier1_to_tier4(tmp_path):
    db_file = str(tmp_path / "test_cortex.sqlite")
    substrate = MemorySubstrate(db_file)
    
    # Tier 1: Raw episode
    ep_id = substrate.record_raw_episode(
        event_type="test_perceive",
        tick_id=1,
        input_payload="User opened terminal",
        thought_trace="System 1 check",
        action_taken="read_status",
        outcome="nominal"
    )
    assert ep_id > 0
    
    # Tier 2: Bi-temporal graph edge with validity
    now = time.time()
    edge_id = substrate.add_graph_edge(
        source="repo_core",
        target="python_311",
        relation="uses_runtime",
        layer="semantic",
        provenance="pyproject.toml"
    )
    assert edge_id.startswith("edge_")
    
    # Query graph at current time
    facts = substrate.query_graph_at_time(now)
    assert len(facts) >= 1
    assert facts[0]["source_id"] == "repo_core"
    assert facts[0]["relation"] == "uses_runtime"
    
    # Tier 3: Vector storage & search
    v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    await substrate.index_vector("item_1", "Authentication module", v1)
    await substrate.index_vector("item_2", "Database migrations", v2)
    
    # Search with query close to v1
    query_vec = np.array([0.9, 0.1, 0.0], dtype=np.float32)
    results = await substrate.search_vectors(query_vec, top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == "item_1"
    assert results[0]["similarity"] > 0.8
    
    # Tier 4: Procedural skills
    await substrate.index_new_skill(
        tool_name="git_branch_cleaner",
        docstring="Removes merged local branches cleanly.",
        file_path="/skills/cleaner.py",
        score=9,
        atlas_pamphlet="# Clean branches checklist"
    )
    skills = await substrate.search_skills("clean local branches")
    assert len(skills) >= 1
    assert skills[0]["name"] == "git_branch_cleaner"

@pytest.mark.asyncio
async def test_mcp_desktop_bridge():
    bridge = MCPDesktopBridge(simulation_mode=True)
    tree_res = await bridge.query_accessibility_tree(root_id="desktop_root")
    assert tree_res["circuit_breaker_passed"] is True
    assert "desktop_root" in tree_res["uri"]
    assert len(tree_res["nodes"]) > 0
    
    # Test circuit breaker with empty nodes
    bad_payload = {"type": "a11y_tree", "nodes": []}
    passed, reason = PerceptualCircuitBreaker.inspect(bad_payload)
    assert not passed
    assert "empty" in reason
