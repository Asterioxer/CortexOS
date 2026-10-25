import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sentiment_analyzer import CognitiveIntentAnalyzer
from voice_engine import UnifiedVoiceEngine

a = CognitiveIntentAnalyzer()
engine = UnifiedVoiceEngine()

test_cases = [
    ("switch to jenny", "jenny", "en-US-JennyNeural"),
    ("switch voice to christopher", "christopher", "en-US-ChristopherNeural"),
    ("switch persona to aria", "aria", "en-US-AriaNeural"),
    ("use guy voice", "guy", "en-US-GuyNeural"),
    ("set voice to neerja", "neerja", "en-IN-NeerjaNeural"),
    ("can you switch to prabhat please", "prabhat", "en-IN-PrabhatNeural"),
    ("use jenny's voice", "jenny", "en-US-JennyNeural")
]

print("Testing Natural Voice Persona Switching (0ms LLM Overhead):")
for phrase, expected_p, expected_v in test_cases:
    res = a.analyze(phrase)
    assert res["intent"] == "PERSONA_SWITCH", f"Failed intent for '{phrase}', got {res['intent']}"
    assert res["target_persona"] == expected_p, f"Failed persona for '{phrase}', got {res['target_persona']}"
    engine.set_persona(res["target_persona"])
    assert engine.active_voice == expected_v, f"Failed voice switch for '{phrase}'"
    print(f"  [✓] \"{phrase}\" -> Switched to {engine.persona_name} ({engine.active_voice})")

print("\n🎉 ALL PERSONA VOICE SWITCHING TESTS PASSED!")
