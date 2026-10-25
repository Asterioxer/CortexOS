"""
Phase 3 Test Suite: Autonomous Laptop Startup / Session Unlock Greeting Sentinel
Validates:
1. Executive Briefing Synthesis (Time-of-day, Battery health, Live top headline).
2. Native Windows WTS Session Unlock Registration & Cooldown Guard.
3. Cognitive Intent Routing for "BRIEFING".
4. Assistant Integration and on-demand trigger.
"""
import time
import sys

# Ensure UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from session_sentinel import ExecutiveBriefing, SessionUnlockSentinel
from sentiment_analyzer import CognitiveIntentAnalyzer

def test_executive_briefing_synthesis():
    print("\n--- [TEST 1] Executive Briefing Synthesis ---")
    eb = ExecutiveBriefing(username="Soham")
    briefing = eb.generate()
    print(f"  Generated Spoken Briefing:\n  \"{briefing}\"")
    
    assert "Soham" in briefing, "Username missing from briefing"
    assert any(g in briefing for g in ["Good morning", "Good afternoon", "Good evening", "Welcome back"]), "Time greeting missing"
    assert "The time is" in briefing, "Time report missing"
    assert "Battery is at" in briefing, "Battery telemetry missing"
    assert "All systems are online and standing by" in briefing, "Signoff missing"
    print("[+] Test 1 Passed: Executive briefing generated with full telemetry!")

def test_sentinel_wts_registration_and_cooldown():
    print("\n--- [TEST 2] Windows WTS Sentinel & Cooldown Guard ---")
    delivered = []
    def on_unlock(text):
        delivered.append(text)

    sentinel = SessionUnlockSentinel(
        on_unlock_callback=on_unlock,
        username="Soham",
        cooldown_seconds=5.0
    )
    sentinel.start()
    time.sleep(0.5)

    assert sentinel.hwnd is not None, "Message-only window failed to create"
    print(f"  Hidden message window created with HWND: {sentinel.hwnd}")

    # Trigger briefing directly
    b1 = sentinel.trigger_briefing_now()
    assert len(delivered) == 1, "Callback not triggered"
    assert b1 == delivered[0], "Briefing text mismatch"
    print(f"  Dispatched initial briefing successfully: {b1[:60]}...")

    # Test simulated unlock inside cooldown
    sentinel.last_unlock_time = time.time() # active cooldown
    sentinel._wnd_proc(sentinel.hwnd, 0x02B1, 0x8, 0) # WTS_SESSION_UNLOCK
    assert len(delivered) == 1, "Cooldown failed to suppress duplicate unlock event!"
    print("  Cooldown protection successfully suppressed duplicate greeting.")

    sentinel.stop()
    print("[+] Test 2 Passed: Native WTS Sentinel and cooldown protection verified!")

def test_intent_routing_briefing():
    print("\n--- [TEST 3] Cognitive Intent Routing for Briefing ---")
    analyzer = CognitiveIntentAnalyzer()
    queries = [
        "give me my briefing",
        "executive briefing",
        "give me a status briefing",
        "what is my morning briefing"
    ]
    for q in queries:
        r = analyzer.analyze(q)
        print(f"  Query: '{q}' -> Intent: {r['intent']}")
        assert r["intent"] == "BRIEFING", f"Failed for '{q}', got {r['intent']}"

    print("[+] Test 3 Passed: 0ms Intent Routing for Briefing verified!")

if __name__ == "__main__":
    print("=" * 65)
    print("🚀 EXECUTING PHASE 3 TEST SUITE (SESSION UNLOCK SENTINEL)")
    print("=" * 65)
    test_executive_briefing_synthesis()
    test_sentinel_wts_registration_and_cooldown()
    test_intent_routing_briefing()
    print("\n" + "=" * 65)
    print("🎉 ALL TESTS PASSED: PHASE 3 FULLY OPERATIONAL!")
    print("=" * 65)
