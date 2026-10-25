import pytest
from cortex.embodiment.sentiment import CognitiveSentimentTracker
from cortex.embodiment.voice import CortexVoiceEngine
from cortex.embodiment.system_somatosensory import SystemSomatosensory
from cortex.inference.client import LocalInferenceClient

def test_sentiment_tracker():
    tracker = CognitiveSentimentTracker()

    # 1. Frustrated tone
    prof_frust = tracker.analyze("Why is this stupid code not working it keeps failing!!")
    assert prof_frust.primary_emotion == "frustrated"
    assert prof_frust.urgency_score >= 0.8
    assert prof_frust.recommended_temperature <= 0.2
    assert "frustration_mitigation" in prof_frust.detected_intents

    # 2. Urgent tone
    prof_urg = tracker.analyze("I need this immediately right now asap!")
    assert prof_urg.primary_emotion == "urgent"
    assert prof_urg.urgency_score >= 0.9
    assert prof_urg.recommended_temperature <= 0.15

    # 3. Excited tone
    prof_exc = tracker.analyze("Wow this is awesome and amazing cool work!")
    assert prof_exc.primary_emotion == "excited"
    assert prof_exc.recommended_temperature >= 0.5

    # 4. Speech normalization
    norm_text = tracker.normalize_speech("open braver and launch power shell for cortex os")
    assert "brave" in norm_text
    assert "powershell" in norm_text
    assert "CortexOS" in norm_text

def test_voice_engine_text_cleaning_and_personas():
    engine = CortexVoiceEngine(enabled=False)

    # 1. Clean markdown and code blocks
    raw_markdown = "Here is the code:\n```python\nprint('hello')\n```\nCheck out `file.py` and [link](http://test.com) 🚀!"
    cleaned = engine.clean_text_for_speech(raw_markdown)
    assert "print('hello')" not in cleaned
    assert "http" not in cleaned
    assert "🚀" not in cleaned
    assert "file.py" in cleaned

    # 2. Persona catalogue
    personas = engine.list_personas()
    p_ids = [p["id"] for p in personas]
    assert "jarvis" in p_ids
    assert "friday" in p_ids
    assert "christopher" in p_ids
    assert "edith" in p_ids
    assert "neerja" in p_ids

    # 3. Switch persona
    res = engine.set_persona("friday")
    assert res["status"] == "SUCCESS"
    assert engine.active_persona == "friday"

    # 4. Stop (barge-in)
    engine.stop()
    assert engine.is_speaking is False

def test_somatosensory_voice_lab_extensions():
    somato = SystemSomatosensory()

    # 1. Volume query and set
    vol = somato.get_volume()
    assert "volume" in vol
    assert "muted" in vol

    set_res = somato.set_volume(45)
    assert set_res["status"] == "SUCCESS"

    # 2. Application close (test with dummy non-running app)
    res_close = somato.close_application("non_existent_fake_app_xyz")
    assert res_close["status"] in ("NOT_FOUND", "SUCCESS")

@pytest.mark.asyncio
async def test_system1_voice_lab_routing():
    llm = LocalInferenceClient()

    # 1. Volume setting
    res_vol = await llm.evaluate_system1_fastpath("<current_perception>set volume to 75</current_perception>")
    assert res_vol["confidence"] >= 0.95
    assert res_vol["action"]["action"] == "set_volume"
    assert res_vol["action"]["level"] == 75

    # 2. Mute toggle
    res_mute = await llm.evaluate_system1_fastpath("<current_perception>mute audio</current_perception>")
    assert res_mute["confidence"] >= 0.95
    assert res_mute["action"]["action"] == "toggle_mute"

    # 3. Close application
    res_close = await llm.evaluate_system1_fastpath("<current_perception>close notepad</current_perception>")
    assert res_close["confidence"] >= 0.95
    assert res_close["action"]["action"] == "close_application"
    assert res_close["action"]["application"] == "notepad"

    # 4. Switch voice persona
    res_persona = await llm.evaluate_system1_fastpath("<current_perception>switch voice to jarvis</current_perception>")
    assert res_persona["confidence"] >= 0.95
    assert res_persona["action"]["action"] == "voice_persona"
    assert res_persona["action"]["persona"] == "jarvis"

    # 5. Stop speaking (barge-in)
    res_stop = await llm.evaluate_system1_fastpath("<current_perception>stop speaking</current_perception>")
    assert res_stop["confidence"] >= 0.95
    assert res_stop["action"]["action"] == "voice_stop"
