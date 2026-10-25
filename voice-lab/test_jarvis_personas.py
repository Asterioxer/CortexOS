from sentiment_analyzer import CognitiveIntentAnalyzer
from voice_engine import UnifiedVoiceEngine

def test_jarvis():
    analyzer = CognitiveIntentAnalyzer()
    engine = UnifiedVoiceEngine()

    test_cases = [
        ("switch to jarvis", "jarvis"),
        ("talk like jarvis", "jarvis"),
        ("switch voice to friday", "friday"),
        ("activate edith", "edith"),
        ("use christopher voice", "christopher"),
        ("switch to neerja", "neerja")
    ]

    for phrase, expected in test_cases:
        res = analyzer.analyze(phrase)
        print(f"Phrase: '{phrase}' -> Target: {res.get('target_persona')}")
        assert res.get("intent") == "PERSONA_SWITCH", f"Failed intent for {phrase}"
        assert res.get("target_persona") == expected, f"Expected {expected}, got {res.get('target_persona')}"
        ack = engine.set_persona(expected)
        print(f"  -> Voice Engine Ack: {ack} (Active: {engine.active_voice})")
        assert engine.persona_name == expected

    print("\n[SUCCESS] All JARVIS, Friday, Edith, and Natural Personas 100% verified!")

if __name__ == "__main__":
    test_jarvis()
