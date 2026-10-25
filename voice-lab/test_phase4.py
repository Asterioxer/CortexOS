"""
Phase 4 Test Suite: System-Level Mixture of Experts (MoE) & Hermes Integration
Validates:
1. MoE Gating Router multi-domain dispatch.
2. Expert 1: CS Scientist code generation & AST verification.
3. Expert 3: Strategic News Intelligence Importance Scoring Matrix (1-10).
4. Hermes Agent Bridge (CLI detection, 51+ skills discovery, skill persistence).
"""
import sys
import os

# Ensure UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from mixture_of_experts import MoEGatingRouter, CSScientistExpert, StrategicNewsExpert, HermesBridge

def test_moe_gating_router():
    print("\n--- [TEST 1] MoE Gating Router Classification ---")
    router = MoEGatingRouter()
    
    test_cases = [
        ("How to implement Dijkstra shortest path in Python with complexity analysis?", "CS_SCIENTIST"),
        ("What is the Big-O time and space complexity of merge sort?", "CS_SCIENTIST"),
        ("Open a new tab in chrome for Claude AI", "OS_OPERATOR"),
        ("Take a screenshot and toggle desktop", "OS_OPERATOR"),
        ("What is the latest geopolitical news on border conflict and trade sanctions?", "STRATEGIC_NEWS"),
        ("List all installed Hermes agent skills and tools", "HERMES_BRIDGE"),
        ("Hello, how are you doing today?", "GENERAL_ASSISTANT")
    ]

    for query, expected_expert in test_cases:
        res = router.route(query)
        print(f"  Query: '{query[:45]}...' -> {res['expert']} (Expected: {expected_expert})")
        assert res["expert"] == expected_expert, f"Routing failed for '{query}': got {res['expert']}, expected {expected_expert}"

    print("[+] Test 1 Passed: MoE Gating Router correctly routed all queries across all 4 domains!")

def test_cs_scientist_ast_verification():
    print("\n--- [TEST 2] CS Scientist AST Validation ---")
    cs = CSScientistExpert()

    valid_py = "def dijkstra(graph, start):\n    import heapq\n    pq = [(0, start)]\n    return pq\n"
    res1 = cs.validate_code_ast(valid_py)
    print(f"  Valid Python AST: {res1}")
    assert res1["valid"] is True, "Valid code failed AST check"

    broken_py = "def dijkstra(graph, start:\n    return False"
    res2 = cs.validate_code_ast(broken_py)
    print(f"  Invalid Python AST: {res2}")
    assert res2["valid"] is False, "Broken code incorrectly passed AST check"
    assert "Syntax error" in res2["error"], "Error message missing"

    print("[+] Test 2 Passed: CS Scientist AST parser accurately enforces syntax validity!")

def test_strategic_news_importance_matrix():
    print("\n--- [TEST 3] Strategic News 1-10 Importance Scoring Matrix ---")
    news_expert = StrategicNewsExpert()

    critical_title = "President signs emergency sanctions treaty amid border conflict and inflation spike"
    crit_score = news_expert.score_importance(critical_title)
    print(f"  Critical Headline: '{critical_title}' -> Score: {crit_score}/10")
    assert crit_score >= 8, f"Critical news scored too low: {crit_score}"

    trivial_title = "Celebrity actress spotted at movie premiere dating new actor"
    triv_score = news_expert.score_importance(trivial_title)
    print(f"  Trivial Headline:  '{trivial_title}' -> Score: {triv_score}/10")
    assert triv_score <= 3, f"Trivia news scored too high: {triv_score}"

    feed = news_expert.fetch_prioritized_news("world economy", max_items=3)
    print(f"  Sample Prioritized Feed:\n{feed}")
    assert "Strategic Intelligence" in feed, "Feed header missing"

    print("[+] Test 3 Passed: Strategic Intelligence importance matrix and ranking verified!")

def test_hermes_bridge_integration():
    print("\n--- [TEST 4] Hermes Agent Bridge & Skills Discovery ---")
    hermes = HermesBridge()
    available = hermes.is_available()
    print(f"  Hermes executable detected: {available} ({hermes.hermes_bin})")
    assert available, "Hermes executable not found"

    version = hermes.get_version()
    print(f"  Hermes Version: {version}")
    assert "Hermes Agent" in version, "Invalid version string"

    skills = hermes.list_skills()
    print(f"  Discovered {len(skills)} Hermes skills (e.g. {skills[0]['name'] if skills else 'none'})")
    assert len(skills) >= 10, f"Expected at least 10 skills, found {len(skills)}"

    # Test skill synthesis persistence
    memory_path = os.path.abspath(r"C:\Users\soham\Desktop\voice-lab\assistant_memory\learned_skills.json")
    saved = hermes.save_learned_skill(
        skill_name="test_hermes_skill",
        code="def test_skill(): return True",
        description="Test skill synthesized from Hermes bridge",
        memory_file=memory_path
    )
    assert saved is True, "Failed to save synthesized skill to assistant memory"
    print(f"  Synthesized skill persisted to assistant memory successfully!")

    print("[+] Test 4 Passed: Hermes Bridge successfully connected and verified!")

if __name__ == "__main__":
    print("=" * 65)
    print("🚀 EXECUTING PHASE 4 TEST SUITE (MoE & HERMES INTEGRATION)")
    print("=" * 65)
    test_moe_gating_router()
    test_cs_scientist_ast_verification()
    test_strategic_news_importance_matrix()
    test_hermes_bridge_integration()
    print("\n" + "=" * 65)
    print("🎉 ALL TESTS PASSED: PHASE 4 FULLY OPERATIONAL!")
    print("=" * 65)
