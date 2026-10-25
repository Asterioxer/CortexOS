import pytest
from fastapi.testclient import TestClient
from cortex.server import app

client = TestClient(app)

def test_dashboard_html():
    res = client.get("/")
    assert res.status_code == 200
    assert "CORTEX-OS // COGNITIVE RUNTIME" in res.text
    assert "tab-memory" in res.text
    assert "tab-graph" in res.text
    assert "tab-skills" in res.text
    assert "tab-governance" in res.text

def test_working_memory_api():
    # 1. Get all blocks
    res = client.get("/api/blocks")
    assert res.status_code == 200
    data = res.json()
    assert "persona_self" in data
    assert "human_profile" in data
    assert "workspace_state" in data
    assert "scratchpad_stm" in data

    # 2. Update a block
    res_update = client.post("/api/blocks/scratchpad_stm", json={"value": "Testing pane update from pytest."})
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["status"] == "SUCCESS"
    assert "Testing pane update from pytest." in updated_data["value"]

def test_media_api():
    res = client.get("/api/media")
    assert res.status_code == 200
    m = res.json()
    assert "active" in m

    res_ctrl = client.post("/api/media/control", json={"command": "toggle"})
    assert res_ctrl.status_code == 200
    ctrl_data = res_ctrl.json()
    assert "status" in ctrl_data

def test_graph_and_engrams_api():
    # 1. Assert a fact
    res_assert = client.post("/api/graph/assert", json={
        "source": "pytest_agent",
        "target": "cortex_ui",
        "relation": "validates",
        "layer": "semantic",
        "provenance": "unit_test"
    })
    assert res_assert.status_code == 200
    assert res_assert.json()["status"] == "SUCCESS"

    # 2. Query graph
    res_graph = client.get("/api/graph")
    assert res_graph.status_code == 200
    g_data = res_graph.json()
    assert "edges" in g_data
    assert "engrams" in g_data
    assert any(e["source_id"] == "pytest_agent" and e["target_id"] == "cortex_ui" for e in g_data["edges"])

def test_skills_api():
    res_skills = client.get("/api/skills")
    assert res_skills.status_code == 200
    s_data = res_skills.json()
    assert "skills" in s_data
    assert "curriculum_challenge" in s_data
    assert len(s_data["skills"]) >= 2

    # Test running git_working_tree_auditor
    res_run = client.post("/api/skills/run", json={"name": "git_working_tree_auditor"})
    assert res_run.status_code == 200
    run_data = res_run.json()
    assert run_data["status"] == "SUCCESS"
    assert "GIT WORKING-TREE & GOVERNANCE AUDIT" in run_data["stdout"]

def test_governance_api():
    # 1. Get governance state
    res_gov = client.get("/api/governance")
    assert res_gov.status_code == 200
    g_data = res_gov.json()
    assert "policy_code" in g_data
    assert "checkpoints" in g_data
    assert "working_tree_diff" in g_data

    # 2. Test PDP evaluation on safe read action
    res_test_allow = client.post("/api/governance/test", json={
        "action": "file_read",
        "resource": "cortex/server.py"
    })
    assert res_test_allow.status_code == 200
    assert res_test_allow.json()["verdict"] == "ALLOW"
    assert res_test_allow.json()["evaluation_time_ms"] < 2.0  # sub-millisecond class

    # 3. Test PDP evaluation on dangerous action -> ESCALATE
    res_test_esc = client.post("/api/governance/test", json={
        "action": "git_push_remote",
        "resource": "origin master"
    })
    assert res_test_esc.status_code == 200
    assert res_test_esc.json()["verdict"] == "ESCALATE"

    # 4. Create manual shadow checkpoint
    res_cp = client.post("/api/governance/checkpoint", json={"label": "pytest_check"})
    assert res_cp.status_code == 200
    assert res_cp.json()["status"] == "SUCCESS"
    assert "sha" in res_cp.json()

def test_panic_killswitch_api():
    # 1. Trigger panic
    res_trig = client.post("/api/governance/panic")
    assert res_trig.status_code == 200
    assert res_trig.json()["status"] == "PANIC_TRIGGERED"

    # 2. Check panic status
    res_st = client.get("/api/governance/panic")
    assert res_st.status_code == 200
    assert res_st.json()["panic_active"] is True

    # 3. Reset panic
    res_reset = client.post("/api/governance/reset_panic")
    assert res_reset.status_code == 200
    assert res_reset.json()["status"] == "PANIC_RESET"

    # 4. Verify clean status
    res_st2 = client.get("/api/governance/panic")
    assert res_st2.status_code == 200
    assert res_st2.json()["panic_active"] is False
