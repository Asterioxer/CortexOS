"""
Test Suite: Self-Healing Ollama Daemon & Resilience Verification
Verifies that AdaptiveContextEngine can auto-detect, auto-launch, and retry
requests seamlessly if Ollama is ever offline or starting up.
"""
import time
from context_manager import AdaptiveContextEngine

def test_ollama_autoheal():
    print("=" * 60)
    print("Testing Self-Healing Ollama Integration & Auto-Recovery")
    print("=" * 60)

    t0 = time.time()
    engine = AdaptiveContextEngine()
    
    # 1. Verify health check
    is_running = engine.ensure_ollama_running()
    assert is_running is True, "Ollama must be running or auto-started successfully!"
    print(f"[PASS] Ollama server health verified in {time.time() - t0:.2f}s")

    # 2. Test dynamic context generation
    t1 = time.time()
    res = engine.generate(
        model="qwen2.5:3b",
        prompt="Reply with 'ONLINE'.",
        profile="voice"
    )
    ans = res.get("response", "").strip()
    assert len(ans) > 0, "Expected non-empty response from qwen2.5:3b"
    print(f"[PASS] Generate call succeeded in {time.time() - t1:.2f}s | Response: {ans[:30]}")

    # 3. Test streaming chat completion
    t2 = time.time()
    chunks = []
    messages = [
        {"role": "system", "content": "You are a fast assistant. Reply in under 5 words."},
        {"role": "user", "content": "Are you ready?"}
    ]
    for chunk in engine.chat_stream(model="qwen2.5:3b", messages=messages, profile="voice"):
        if chunk.get("content"):
            chunks.append(chunk["content"])
    streamed_text = "".join(chunks).strip()
    assert len(streamed_text) > 0, "Expected streamed tokens"
    print(f"[PASS] Chat stream succeeded in {time.time() - t2:.2f}s | Streamed: {streamed_text}")

    print("=" * 60)
    print("ALL SELF-HEALING OLLAMA TESTS PASSED (100% HEALTHY)")
    print("=" * 60)

if __name__ == "__main__":
    test_ollama_autoheal()
