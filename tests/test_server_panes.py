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
    assert "tab-execution" in res.text
    assert "btn-side-toggle" in res.text
    assert "ticker-voice" in res.text

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

def test_execution_api():
    # 1. Pipeline status
    res_pipe = client.get("/api/execution/pipeline")
    assert res_pipe.status_code == 200
    pipe_data = res_pipe.json()
    assert "stages" in pipe_data
    assert len(pipe_data["stages"]) == 9
    assert "tick_id" in pipe_data
    assert "temperature" in pipe_data

    # 2. Daemons inspector
    res_daemons = client.get("/api/execution/daemons")
    assert res_daemons.status_code == 200
    daemons_data = res_daemons.json()
    assert isinstance(daemons_data, dict)
    assert "uvicorn_server" in daemons_data
    assert "ambient_worker" in daemons_data
    assert "stall_breaker" in daemons_data
    assert "sleep_daemon" in daemons_data

    # 3. Processes inspector
    res_proc = client.get("/api/execution/processes")
    assert res_proc.status_code == 200
    proc_data = res_proc.json()
    assert "cortex_pid" in proc_data
    assert "total_system_processes" in proc_data
    assert proc_data["total_system_processes"] > 0
    assert "cortex_children" in proc_data
    assert "desktop_applications" in proc_data

    # 4. Terminal sandbox execution (safe command)
    res_term = client.post("/api/execution/terminal", json={"command": "dir"})
    assert res_term.status_code == 200
    term_data = res_term.json()
    assert term_data["status"] == "SUCCESS"
    assert term_data["exit_code"] == 0
    assert "execution_time_ms" in term_data

    # 5. Terminal sandbox execution with blocked command (policy deny)
    res_deny = client.post("/api/execution/terminal", json={"command": "cat .ssh/id_rsa"})
    assert res_deny.status_code == 200
    deny_data = res_deny.json()
    assert deny_data["status"] == "DENIED"

    # 6. Terminal sandbox execution with failing command triggering automatic rollback
    res_fail = client.post("/api/execution/terminal", json={"command": "dir non_existent_folder_xyz_12345"})
    assert res_fail.status_code == 200
    fail_data = res_fail.json()
    assert fail_data["status"] == "FAILED_ROLLED_BACK"

def test_voice_api():
    # 1. Voice status
    res_status = client.get("/api/voice/status")
    assert res_status.status_code == 200
    v_data = res_status.json()
    assert "enabled" in v_data
    assert "active_persona" in v_data
    assert "personas" in v_data
    assert len(v_data["personas"]) >= 5

    # 2. Switch persona
    res_persona = client.post("/api/voice/persona", json={"persona": "jarvis"})
    assert res_persona.status_code == 200
    assert res_persona.json()["status"] == "SUCCESS"
    assert res_persona.json()["active_persona"] == "jarvis"

    # 3. Toggle voice
    res_toggle = client.post("/api/voice/toggle", json={"enabled": False})
    assert res_toggle.status_code == 200
    assert res_toggle.json()["enabled"] is False

    res_toggle_back = client.post("/api/voice/toggle", json={"enabled": True})
    assert res_toggle_back.status_code == 200
    assert res_toggle_back.json()["enabled"] is True

    # 4. Stop voice (barge-in)
    res_stop = client.post("/api/voice/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] == "SUCCESS"

