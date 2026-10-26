"""Unit & Integration Tests for CortexOS Deterministic Trigger Router."""

import pytest
from starlette.testclient import TestClient

from cortex.vault.trigger_router import get_trigger_router, TriggerRouter
from cortex.server import app

client = TestClient(app)


def test_trigger_router_match_greeting():
    router = get_trigger_router()
    for phrase in ["hello", "greetings", "hey cortex", "greet", "wake up"]:
        match = router.match(phrase)
        assert match is not None, f"Failed to match greeting phrase: {phrase}"
        assert match.trigger_type == "SESSION_GREETING"
        assert match.action_name == "execute_greeting"


def test_trigger_router_match_shutdown():
    router = get_trigger_router()
    for phrase in ["shutdown", "power off", "goodbye", "stand down", "exit cortex", "shut down"]:
        match = router.match(phrase)
        assert match is not None, f"Failed to match shutdown phrase: {phrase}"
        assert match.trigger_type == "SYSTEM_SHUTDOWN"
        assert match.action_name == "execute_shutdown"


def test_trigger_router_match_telemetry():
    router = get_trigger_router()
    match = router.match("telemetry")
    assert match is not None
    assert match.trigger_type == "HARDWARE_TELEMETRY"


def test_trigger_router_match_project_switch():
    router = get_trigger_router()
    match = router.match("open project voice-lab")
    assert match is not None
    assert match.trigger_type == "PROJECT_SWITCH"
    assert match.parameters["project_name"] == "voice-lab"


def test_trigger_router_match_app_launch():
    router = get_trigger_router()
    match = router.match("open code")
    assert match is not None
    assert match.trigger_type == "APPLICATION_LAUNCH"
    assert match.parameters["target"] == "code"


@pytest.mark.asyncio
async def test_trigger_router_execute_greeting():
    router = get_trigger_router()
    res = router.get_greeting()
    assert res["status"] == "SUCCESS"
    assert "Soham" in res["response"]
    assert "RAM" in res["response"]
    assert res["speak"] is True
    assert res["persona"] == "jarvis"


@pytest.mark.asyncio
async def test_trigger_router_execute_shutdown():
    router = get_trigger_router()
    res = router.get_shutdown()
    assert res["status"] == "SHUTDOWN_READY"
    assert "Goodbye Soham" in res["response"]
    assert "Vault backup" in res["response"] or "vault backup" in res["response"].lower()
    assert res["speak"] is True


def test_api_system_greet_endpoint():
    res = client.post("/api/system/greet")
    assert res.status_code == 200
    data = res.json()
    assert "Soham" in data["response"]
    assert data["persona"] == "jarvis"


def test_api_system_shutdown_endpoint():
    res = client.post("/api/system/shutdown")
    assert res.status_code == 200
    data = res.json()
    assert "Goodbye Soham" in data["response"]
    assert data["status"] == "SHUTDOWN_READY"


def test_api_system_trigger_endpoint():
    res = client.post("/api/system/trigger", json={"prompt": "telemetry"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "Hardware Posture" in data["response"]
