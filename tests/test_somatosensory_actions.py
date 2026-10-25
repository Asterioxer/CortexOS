import pytest
from cortex.embodiment.system_somatosensory import SystemSomatosensory
from cortex.inference.client import LocalInferenceClient

def test_active_window_detection():
    somato = SystemSomatosensory()
    win = somato.get_active_window()
    assert "title" in win
    assert "process" in win
    assert "status" in win
    assert win["status"] == "SUCCESS"

def test_clipboard_operations():
    somato = SystemSomatosensory()
    # Write to clipboard
    test_str = "CORTEX-OS-CLIPBOARD-TEST-99"
    set_res = somato.set_clipboard_text(test_str)
    assert set_res["status"] == "SUCCESS"

    # Read from clipboard
    get_res = somato.get_clipboard_text()
    assert get_res["status"] == "SUCCESS"
    assert test_str in get_res["text"]

@pytest.mark.asyncio
async def test_system1_new_action_routing():
    llm = LocalInferenceClient()
    
    # 1. Active window
    res_win = await llm.evaluate_system1_fastpath("<current_perception>what is my active window</current_perception>")
    assert res_win["confidence"] >= 0.9
    assert res_win["action"]["action"] == "get_active_window"

    # 2. Clipboard
    res_clip = await llm.evaluate_system1_fastpath("<current_perception>what did i copy in my clipboard</current_perception>")
    assert res_clip["confidence"] >= 0.9
    assert res_clip["action"]["action"] == "get_clipboard"

    # 3. Media control
    res_pause = await llm.evaluate_system1_fastpath("<current_perception>pause the song</current_perception>")
    assert res_pause["confidence"] >= 0.9
    assert res_pause["action"]["action"] == "media_control"
    assert res_pause["action"]["command"] == "pause"

    res_skip = await llm.evaluate_system1_fastpath("<current_perception>skip to next track</current_perception>")
    assert res_skip["confidence"] >= 0.9
    assert res_skip["action"]["action"] == "media_control"
    assert res_skip["action"]["command"] == "next"
