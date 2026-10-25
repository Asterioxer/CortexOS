"""
Tests for Full Integration of Voice Lab into CortexOS.
Verifies Audio DSP, Silero VAD, Noise Suppressor, Session Sentinel,
Executive Briefing, Somatosensory Browser Operators, MoE Routing,
CS Algorithm AST Validation, and Strategic News Scoring.
"""

import os
import pytest
import numpy as np

from cortex.embodiment.audio_dsp import SileroVAD, RealTimeNoiseSuppressor, PHANTOM_PHRASES
from cortex.embodiment.voice import CortexVoiceEngine, CortexVoiceListener
from cortex.embodiment.session_sentinel import ExecutiveBriefing, SessionUnlockSentinel
from cortex.embodiment.system_somatosensory import SystemSomatosensory
from cortex.inference.moe_router import (
    MoEGatingRouter,
    CSScientistExpert,
    StrategicNewsExpert,
    HermesBridge
)
from cortex.voice_assistant import CortexVoiceAssistant


def test_silero_vad_and_noise_suppression():
    """Tests Silero VAD processing and real-time noise suppression."""
    vad = SileroVAD()
    assert vad.CHUNK_SAMPLES == 512
    assert vad.SAMPLE_RATE == 16000

    # 1. Test silent chunk
    silent_chunk = np.zeros(512, dtype=np.float32)
    prob_silent, is_speech_silent = vad.process_chunk(silent_chunk)
    assert isinstance(prob_silent, float)
    assert prob_silent < 0.50
    assert is_speech_silent is False

    # 2. Test synthetic speech tone (sine wave 400Hz)
    t = np.linspace(0, 512 / 16000, 512, endpoint=False)
    speech_chunk = (0.5 * np.sin(2 * np.pi * 400 * t)).astype(np.float32)
    prob_tone, _ = vad.process_chunk(speech_chunk)
    assert isinstance(prob_tone, float)

    # 3. Test noise suppressor
    suppressor = RealTimeNoiseSuppressor(sample_rate=16000)
    cleaned = suppressor.filter_chunk(speech_chunk, is_speech=True)
    assert cleaned.shape == (512,)
    assert cleaned.dtype == np.float32


def test_phantom_phrases_and_hallucination_filter():
    """Tests phantom phrase blacklist and hallucination rejection."""
    listener = CortexVoiceListener()
    assert listener.is_phantom_phrase("Thank you.") is True
    assert listener.is_phantom_phrase("thanks for watching!") is True
    assert listener.is_phantom_phrase("subtitles by") is True
    assert listener.is_phantom_phrase("ok") is True
    assert listener.is_phantom_phrase("x") is True

    # Real human command should NOT be filtered
    assert listener.is_phantom_phrase("Open a new terminal for me") is False
    assert listener.is_phantom_phrase("What is the CPU usage?") is False


def test_executive_briefing_and_session_sentinel():
    """Tests Executive Briefing text generation and Session Sentinel."""
    briefing = ExecutiveBriefing(username="Soham")
    time_greeting = briefing.get_time_greeting()
    assert "Soham" in time_greeting

    full_brief = briefing.generate()
    assert "Soham" in full_brief
    assert "The time is" in full_brief
    assert "All CortexOS neural substrates are online" in full_brief

    # Sentinel instantiation
    sentinel = SessionUnlockSentinel(username="Soham", cooldown_seconds=60.0)
    assert sentinel.cooldown_seconds == 60.0
    direct_brief = sentinel.trigger_briefing_now()
    assert "Soham" in direct_brief


def test_somatosensory_browser_and_security_guardrails():
    """Tests web apps, Chrome tab formatting, code sandbox, and sensitive path guardrails."""
    somato = SystemSomatosensory()

    # 1. Web app directory
    res_yt = somato.open_web_app("youtube")
    assert res_yt["status"] == "SUCCESS"
    assert res_yt["url"] == "https://www.youtube.com"

    res_gh = somato.open_web_app("github")
    assert res_gh["status"] == "SUCCESS"
    assert res_gh["url"] == "https://github.com"

    # 2. Sensitive path guardrails
    assert somato.is_sensitive_path(r"C:\Users\soham\.ssh\id_rsa") is True
    assert somato.is_sensitive_path(r"C:\Users\soham\AppData\Local\Google\Chrome\User Data\Default\Login Data") is True
    assert somato.is_sensitive_path(r"C:\Windows\System32\config\SAM") is True
    assert somato.is_sensitive_path(r"C:\Users\soham\Desktop\self-conscious\README.md") is False


def test_moe_router_and_domain_experts():
    """Tests Mixture-of-Experts routing logic and specialized expert capabilities."""
    router = MoEGatingRouter()

    # 1. Algorithm & CS query -> CS_SCIENTIST
    r_cs = router.route("Explain the time complexity of Dijkstra algorithm with priority queue")
    assert r_cs["expert"] == "CS_SCIENTIST"
    assert "qwen3.5" in r_cs["model"]

    # 2. OS & Desktop control -> OS_OPERATOR
    r_os = router.route("Open a new tab in Chrome for GitHub and take a screenshot")
    assert r_os["expert"] == "OS_OPERATOR"
    assert "qwen2.5:3b" in r_os["model"]

    # 3. Geopolitical news -> STRATEGIC_NEWS
    r_news = router.route("Give me the latest headlines on economy, inflation and international sanctions")
    assert r_news["expert"] == "STRATEGIC_NEWS"
    assert "llama3.2" in r_news["model"]

    # 4. Hermes Bridge query
    r_hermes = router.route("List all installed hermes agent skills")
    assert r_hermes["expert"] == "HERMES_BRIDGE"


def test_cs_scientist_ast_validation():
    """Tests Python AST syntax validation by CSScientistExpert."""
    cs_expert = CSScientistExpert()

    # Valid Python
    valid_code = "def fib(n):\n    return n if n <= 1 else fib(n-1) + fib(n-2)\n"
    res_valid = cs_expert.validate_code_ast(valid_code)
    assert res_valid["valid"] is True
    assert res_valid["error"] is None
    assert res_valid["ast_nodes"] == 1

    # Invalid Python (Syntax error)
    invalid_code = "def broken(\n    return 42"
    res_invalid = cs_expert.validate_code_ast(invalid_code)
    assert res_invalid["valid"] is False
    assert "Syntax error" in res_invalid["error"]


def test_strategic_news_importance_scoring():
    """Tests 1-10 geopolitical & economic importance matrix."""
    news_expert = StrategicNewsExpert()

    # High-impact critical news
    score_critical = news_expert.score_importance("Breaking: UN Security Council signs nuclear treaty amid border conflict")
    assert score_critical >= 8

    # Economic impact news
    score_econ = news_expert.score_importance("Central Bank raises interest rate as inflation impacts GDP")
    assert score_econ >= 7

    # Celebrity / trivia news (penalized)
    score_trivia = news_expert.score_importance("Celebrity actor spotted at wedding dating co-star")
    assert score_trivia <= 3


def test_voice_assistant_reflex_integration():
    """Tests that CortexVoiceAssistant orchestrates components cleanly."""
    assistant = CortexVoiceAssistant(voice_enabled=False)
    assert assistant.active_persona == "friday"

    # Test persona change via input
    assistant.handle_input("/persona jarvis")
    assert assistant.active_persona == "jarvis"

    # Test briefing trigger
    assistant.handle_input("give me a briefing")
