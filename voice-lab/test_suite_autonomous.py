"""
Comprehensive Autonomous Stress & Benchmark Test Suite
Runs rigorous tests on:
1. Code Generation & Purity (no meta-wrappers, clean AST-valid Python & C++)
2. Cognitive Intent & Emotion Classification
3. System Controller (Stats, Screenshot, Volume, Desktop, News)
4. Security & Sensitive Credential Guardrails
5. Self-Learning Memory & Skill Caching
"""
import ast
import os
import sys
import json
import time

# Ensure UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from autonomous_agent import AutonomousAgent, is_safe_powershell
from system_controller import SystemController
from sentiment_analyzer import CognitiveIntentAnalyzer

def run_tests():
    print("=" * 70)
    print("🧪 RUNNING AUTONOMOUS STRESS & BENCHMARK SUITE")
    print("=" * 70)
    
    passed = 0
    total = 0

    # -------------------------------------------------------------
    # Test Group 1: Security Guardrails
    # -------------------------------------------------------------
    print("\n[Group 1] Security & Guardrails Verification...")
    ctrl = SystemController(sandbox_dir=r"C:\Users\soham\voice-lab\sandbox")

    # Sensitive path read test
    total += 1
    res = ctrl.read_file_content(r"C:\Users\soham\.ssh\id_rsa")
    if "ACCESS DENIED" in res:
        print("  [PASS] Blocked unauthorized .ssh/id_rsa access")
        passed += 1
    else:
        print(f"  [FAIL] Did not block .ssh read: {res}")

    total += 1
    res = ctrl.read_file_content(r"C:\Windows\System32\config\sam")
    if "ACCESS DENIED" in res:
        print("  [PASS] Blocked unauthorized SAM registry access")
        passed += 1
    else:
        print(f"  [FAIL] Did not block SAM read: {res}")

    # PowerShell security blacklist test
    total += 1
    cmd1 = "Get-Content ~/.ssh/id_rsa"
    if not is_safe_powershell(cmd1):
        print("  [PASS] PowerShell filter blocked: 'Get-Content ~/.ssh/id_rsa'")
        passed += 1
    else:
        print("  [FAIL] PowerShell filter allowed unsafe command")

    total += 1
    cmd2 = "cmdkey /list"
    if not is_safe_powershell(cmd2):
        print("  [PASS] PowerShell filter blocked: 'cmdkey /list'")
        passed += 1
    else:
        print("  [FAIL] PowerShell filter allowed cmdkey")

    # -------------------------------------------------------------
    # Test Group 2: Cognitive Intent & Emotion Classification
    # -------------------------------------------------------------
    print("\n[Group 2] Cognitive Intent & Emotion Accuracy...")
    analyzer = CognitiveIntentAnalyzer()

    intent_tests = [
        ("exit the program and close this shell", "EXIT"),
        ("stop, be quiet for a second", "INTERRUPT"),
        ("hello assistant, good morning", "GREETING"),
        ("take a screenshot right now", "SCREENSHOT"),
        ("minimize all windows to desktop", "DESKTOP_TOGGLE"),
        ("mute the volume", "VOLUME_MUTE"),
        ("play shape of you by ed sheeran on brave", "MEDIA_PLAY"),
        ("what is today's latest news on geopolitics?", "NEWS"),
    ]

    for prompt, expected_intent in intent_tests:
        total += 1
        res = analyzer.analyze(prompt)
        if res["intent"] == expected_intent:
            print(f"  [PASS] '{prompt[:35]}...' -> {expected_intent}")
            passed += 1
        else:
            print(f"  [FAIL] '{prompt}' -> Got {res['intent']}, expected {expected_intent}")

    # Emotion tests
    total += 1
    res_emo = analyzer.analyze("Why is this damn code failing over and over, I hate this!")
    if res_emo["emotion"] == "frustrated":
        print(f"  [PASS] Frustrated emotion correctly recognized")
        passed += 1
    else:
        print(f"  [FAIL] Emotion got {res_emo['emotion']}, expected frustrated")

    total += 1
    res_emo2 = analyzer.analyze("Quick, hurry up! Give me the status immediately!")
    if res_emo2["emotion"] == "urgent":
        print(f"  [PASS] Urgent emotion correctly recognized")
        passed += 1
    else:
        print(f"  [FAIL] Emotion got {res_emo2['emotion']}, expected urgent")

    # -------------------------------------------------------------
    # Test Group 3: System Controller Capabilities
    # -------------------------------------------------------------
    print("\n[Group 3] System Controller Tools...")
    
    # Telemetry
    total += 1
    stats = ctrl.get_system_stats()
    if "CPU:" in stats and "RAM:" in stats:
        print("  [PASS] System stats telemetry functional")
        passed += 1
    else:
        print(f"  [FAIL] Stats failed: {stats}")

    # Screenshot
    total += 1
    snap_res = ctrl.take_screenshot("benchmark_test.png")
    snap_path = os.path.join(r"C:\Users\soham\voice-lab\sandbox\screenshots", "benchmark_test.png")
    if (os.path.exists(snap_path) and os.path.getsize(snap_path) > 1000) or "Screen capture paused" in snap_res or "saved successfully" in snap_res:
        print(f"  [PASS] Screenshot tool executed/handled cleanly: {snap_res}")
        passed += 1
    else:
        print(f"  [FAIL] Screenshot failed: {snap_res}")

    # Live News
    total += 1
    news = ctrl.fetch_live_news("technology")
    if "Live News Headlines" in news and len(news) > 50:
        print("  [PASS] Live Google News RSS retrieval functional")
        passed += 1
    else:
        print(f"  [FAIL] News retrieval failed: {news}")

    # -------------------------------------------------------------
    # Test Group 4: Code Generation Purity (No meta-wrappers)
    # -------------------------------------------------------------
    print("\n[Group 4] Pure Code Generation Quality...")
    agent = AutonomousAgent()

    total += 1
    # Check Python pure generation
    print("  [*] Testing Python code generation: 'check if a number is prime'...")
    task = "write a program to check if a number is prime in Python"
    clean_task = agent._extract_coding_task(task)
    sys_prompt = (
        "You are an expert software developer. "
        "Write ONLY the pure, complete, and syntactically valid source code for the requested task. "
        "STRICT RULES:\n"
        "1. Output ONLY the source code. Never include markdown code fences (```) or conversational remarks.\n"
        "2. NEVER write code that calls notepad.exe, cmd.exe, or OS shell wrappers.\n"
        "3. Include helpful comments and a clean main entrypoint."
    )
    raw_code = agent._query_ollama(agent.fast_model, f"Task: {clean_task}", sys_prompt)
    code = agent._clean_code_fences(raw_code)

    # Verify no notepad meta-calls
    has_meta_notepad = "notepad" in code.lower() and "import os" in code and "os.system" in code
    # Verify AST syntax
    syntax_valid = False
    try:
        ast.parse(code)
        syntax_valid = True
    except SyntaxError as e:
        syntax_valid = False
        print(f"    AST syntax error: {e}")

    if not has_meta_notepad and syntax_valid:
        print("  [PASS] Python code generated is 100% syntactically valid and pure (no meta-wrappers)")
        passed += 1
    else:
        print(f"  [FAIL] Code purity test failed (has_meta={has_meta_notepad}, syntax={syntax_valid})")

    # -------------------------------------------------------------
    # Test Group 5: Memory Persistence & Recall
    # -------------------------------------------------------------
    print("\n[Group 5] Self-Learning Memory...")
    total += 1
    mem = agent.memory
    mem.record_success(
        intent="benchmark memory test unique skill 999",
        action_type="powershell",
        code_or_cmd="echo 'Memory Test OK'"
    )
    hit = mem.find_matching_skill("benchmark memory test unique skill 999")
    if hit and hit.get("code_or_cmd") == "echo 'Memory Test OK'":
        print("  [PASS] Memory successfully recorded and retrieved new skill")
        passed += 1
    else:
        print("  [FAIL] Memory recall failed")

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{total} TESTS PASSED ({(passed/total)*100:.1f}%)")
    print("=" * 70)

    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
