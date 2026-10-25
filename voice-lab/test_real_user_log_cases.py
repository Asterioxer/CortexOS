"""
Validation Suite for Today's Real User Logs & Field Feedback
Tests all edge cases encountered in the real interactive session:
1. Spoken persona switches (including phonetic errors like 'Abia', spoken 'slash persona', etc.)
2. App resolution for 'LinkedIn' (web app) and 'Anti-Gravity' (Start Menu .lnk)
3. Spoken browser tab switching (Ctrl+1, Ctrl+2)
4. Complex conversational news disambiguation and compound greeting parsing
"""
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sentiment_analyzer import CognitiveIntentAnalyzer
from system_controller import SystemController

def test_user_log_cases():
    print("=" * 65)
    print("VALIDATING REAL USER RUNTIME LOG FIXES")
    print("=" * 65)

    analyzer = CognitiveIntentAnalyzer()
    ctrl = SystemController()

    # 1. Spoken Persona Switching Tests
    print("\n--- 1. Testing Spoken Persona Switching ---")
    persona_cases = [
        ("Change your persona to Abia, ARIA.", "aria"),
        ("Good job Aria, you can switch up persona slash persona and put in Jenny in the place.", "jenny"),
        ("slash persona Jenny.", "jenny"),
        ("I want Jenny.", "jenny"),
        ("I want you to change the persona that you are speaking with.  I want Jenny.", "jenny"),
        ("use guy voice", "guy"),
        ("switch to neerja", "neerja"),
        ("can you be christopher please", "christopher")
    ]
    for text, expected in persona_cases:
        res = analyzer.analyze(text)
        print(f"  Query: '{text[:50]:<50}' -> {res['intent']} ({res.get('target_persona')})")
        assert res["intent"] == "PERSONA_SWITCH", f"Expected PERSONA_SWITCH for '{text}', got {res['intent']}"
        assert res.get("target_persona") == expected, f"Expected {expected}, got {res.get('target_persona')}"
    print("[+] All persona switching cases passed!")

    # 2. Browser Tab Switch Tests
    print("\n--- 2. Testing Browser Tab Switch Routing ---")
    tab_cases = [
        ("Click on the first tab that is there, LinkedIn, Post-Fo Social Media Manager.", 1),
        ("go to the second tab in chrome", 2),
        ("switch to the third tab", 3)
    ]
    for text, expected_tab in tab_cases:
        res = analyzer.analyze(text)
        print(f"  Query: '{text[:50]:<50}' -> {res['intent']} (Tab {res.get('tab_number')})")
        assert res["intent"] == "BROWSER_TAB_SWITCH", f"Expected BROWSER_TAB_SWITCH for '{text}'"
        assert res.get("tab_number") == expected_tab, f"Expected tab {expected_tab}, got {res.get('tab_number')}"
    print("[+] All tab switching cases passed!")

    # 3. Intelligent News Disambiguation & Compound Greeting
    print("\n--- 3. Testing News Disambiguation & Compound Greetings ---")
    news_cases = [
        ("Now about your research on today's latest news and give it to me.  Research the news from new tab in Google Chrome and read exactly what it gives you.", "world breaking news"),
        ("I was asking is that you give me the news not about Google Chrome about like what are the latest news happening around the world by searching it on my Google Chrome account which is currently open and you open a new tab in search for the news itself.  It will help you a lot.", "world breaking news"),
        ("Give me the news, give me the news, please.", "world breaking news"),
        ("Hi, how's it going today?  Could you fetch me in the latest news of the day and like what's happening around the world today?", "world breaking news"),
        ("What is the latest news on artificial intelligence in India?", "artificial intelligence in india")
    ]
    for text, expected_topic in news_cases:
        res = analyzer.analyze(text)
        print(f"  Query: '{text[:50]:<50}' -> {res['intent']} | Topic: '{res.get('news_topic')}'")
        assert res["intent"] == "NEWS", f"Expected NEWS for '{text}', got {res['intent']}"
        assert res.get("news_topic") == expected_topic, f"Expected topic '{expected_topic}', got '{res.get('news_topic')}'"
    print("[+] All news disambiguation cases passed!")

    # 4. App & Web App Resolution Verification
    print("\n--- 4. Testing App & Web App Resolution ---")
    # LinkedIn
    res_li = ctrl.open_application("LinkedIn")
    print(f"  LinkedIn resolution: {res_li}")
    assert "browser" in res_li or "successfully" in res_li, f"Unexpected LinkedIn output: {res_li}"

    # Anti-Gravity / Antigravity
    res_ag1 = ctrl.open_application("Anti-Gravity")
    print(f"  Anti-Gravity resolution: {res_ag1}")
    assert "successfully" in res_ag1, f"Failed to resolve Anti-Gravity: {res_ag1}"

    res_ag2 = ctrl.open_application("Antigravity")
    print(f"  Antigravity resolution: {res_ag2}")
    assert "successfully" in res_ag2, f"Failed to resolve Antigravity: {res_ag2}"

    print("[+] All app resolution cases passed!")

    print("\n" + "=" * 65)
    print("ALL RUNTIME LOG VERIFICATION TESTS PASSED (100% HEALTHY)")
    print("=" * 65)

if __name__ == "__main__":
    test_user_log_cases()
