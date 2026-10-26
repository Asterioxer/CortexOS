import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from cortex.inference.ollama_bridge import OllamaBridge, get_ollama_bridge

@pytest.mark.asyncio
async def test_ollama_bridge_initialization():
    bridge = OllamaBridge()
    assert bridge.active_model == "qwen2.5:3b"
    assert bridge.base_url == "http://127.0.0.1:11434"

@pytest.mark.asyncio
async def test_ollama_bridge_check_health():
    bridge = get_ollama_bridge()
    is_online = await bridge.check_health()
    # It should detect Ollama running on Soham's machine
    assert is_online is True

@pytest.mark.asyncio
async def test_ollama_bridge_list_models():
    bridge = get_ollama_bridge()
    models = await bridge.list_models(force_refresh=True)
    assert len(models) >= 1
    names = [m.name for m in models]
    assert any("qwen2.5:3b" in n for n in names)

@pytest.mark.asyncio
async def test_ollama_bridge_set_active_model():
    bridge = get_ollama_bridge()
    bridge.set_active_model("dolphinlabs/llama3.2-3b-uncensored:latest")
    assert "llama3.2" in bridge.active_model
    bridge.set_active_model("qwen2.5:3b")
    assert "qwen" in bridge.active_model

@pytest.mark.asyncio
async def test_ollama_bridge_get_status_payload():
    bridge = get_ollama_bridge()
    await bridge.list_models()
    payload = bridge.get_status_payload()
    assert payload["online"] is True
    assert "active_model" in payload
    assert "available_models" in payload
    assert len(payload["available_models"]) >= 1

@pytest.mark.asyncio
async def test_ollama_bridge_build_system_prompt():
    bridge = get_ollama_bridge()
    prompt = bridge.build_system_prompt(
        somato_snapshot="CPU: 12% | RAM: 8GB",
        vault_context="Note: 05_System_State/Hardware_Topology.md"
    )
    assert "Soham" in prompt
    assert "RTX 3050" in prompt
    assert "CPU: 12%" in prompt
    assert "Hardware_Topology.md" in prompt
    assert "```action" in prompt

@pytest.mark.asyncio
async def test_ollama_bridge_autonomous_action_parsing():
    bridge = get_ollama_bridge()
    mock_somato = MagicMock()
    mock_somato.get_summary_snapshot.return_value = "All systems nominal."
    mock_somato.execute_action.return_value = {"status": "SUCCESS", "message": "VS Code opened."}

    mock_llm_reply = (
        "I am switching your workspace to the Voice Lab project now, Soham.\n\n"
        "```action\n"
        "{\n"
        '  "action": "switch_project",\n'
        '  "parameters": {"project_name": "voice-lab"},\n'
        '  "thought": "Open Voice Lab workspace on Desktop."\n'
        "}\n"
        "```"
    )

    with patch.object(bridge, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_reply
        res = await bridge.autonomous_think_and_act(
            user_prompt="open voice lab",
            somato_cortex=mock_somato,
            vault_rag=None,
            trigger_router=None
        )
        assert res["status"] == "ACTION_EXECUTED"
        assert res["action_executed"]["action"] == "switch_project"
        assert "switching your workspace" in res["response"]
