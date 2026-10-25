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

    # 4. Stop Brave song / stop song
    res_stop_brave = await llm.evaluate_system1_fastpath("<current_perception>stop the brave song</current_perception>")
    assert res_stop_brave["confidence"] >= 0.9
    assert res_stop_brave["action"]["action"] == "media_control"
    assert res_stop_brave["action"]["command"] == "pause"

    res_stop_song = await llm.evaluate_system1_fastpath("<current_perception>stop the song</current_perception>")
    assert res_stop_song["confidence"] >= 0.9
    assert res_stop_song["action"]["action"] == "media_control"
    assert res_stop_song["action"]["command"] == "pause"

    # 5. Open new terminal
    res_term = await llm.evaluate_system1_fastpath("<current_perception>open a new terminal</current_perception>")
    assert res_term["confidence"] >= 0.9
    assert res_term["action"]["action"] == "launch_terminal"

    # 6. List desktop directory
    res_ls_desk = await llm.evaluate_system1_fastpath("<current_perception>yes run ls on the /desktop directory of mine and fetch everything you see</current_perception>")
    assert res_ls_desk["confidence"] >= 0.9
    assert res_ls_desk["action"]["action"] == "directory_list"

    res_check_path = await llm.evaluate_system1_fastpath(r"<current_perception>C:\Users\soham\Desktop check it here</current_perception>")
    assert res_check_path["confidence"] >= 0.9
    assert res_check_path["action"]["action"] == "directory_list"

def test_somatosensory_path_resolution_and_listing():
    somato = SystemSomatosensory()
    resolved_desk = somato.resolve_path("/desktop")
    assert resolved_desk == somato.desktop_dir
    assert resolved_desk.exists()

    items = somato.list_directory("/desktop")
    assert isinstance(items, list)
    assert len(items) > 0
    assert any(it["name"] for it in items)
