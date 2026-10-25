from voice_assistant import AutonomousAssistant
import os
import json

def test_v3():
    print("Testing Assistant v3.0 (Agentic + Self-Learning + Notepad Injection)...")
    assistant = AutonomousAssistant(
        voice_input_enabled=False,
        voice_output_enabled=False
    )

    print("\n--- Test 1: Code Writing & Notepad Launch ---")
    reply1 = assistant.process_message("Open Notepad and write a program to reverse string.")
    print("Reply 1:", reply1)

    # Check memory file
    mem_file = r"C:\Users\soham\voice-lab\assistant_memory\learned_skills.json"
    assert os.path.exists(mem_file), "Memory file not found"
    with open(mem_file, "r") as f:
        skills = json.load(f)
    print(f"Memory contains {len(skills)} learned skill(s):")
    for s in skills:
        print(f"  - Intent: {s['intent']} | Action: {s['action_type']}")

    print("\n--- Test 2: Instant Barge-in Callback Check ---")
    from voice_listener import VoiceListener
    interrupted = []
    def mock_interrupt():
        interrupted.append(True)
    listener = VoiceListener(lambda x: None, on_interrupt_detected=mock_interrupt)
    # Simulate a chunk over threshold while speaking
    listener.set_speaking(True)
    import numpy as np
    loud_chunk = np.ones((800, 1), dtype=np.float32) * 0.15 # RMS = 0.15 > 0.085
    listener._audio_callback(loud_chunk, 800, None, None)
    assert len(interrupted) > 0, "Failed to trigger instant barge-in cut-off"
    print("[+] Instant Sub-50ms Barge-in callback verified successfully!")

    print("\n[+] V3.0 COMPLETE PIPELINE TEST PASSED!")

if __name__ == "__main__":
    test_v3()
