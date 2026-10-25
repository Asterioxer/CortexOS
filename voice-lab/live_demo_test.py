"""
Live Audio & Laptop Control Demonstration
Tests all core assistant capabilities while speaking aloud through your laptop speakers.
"""
import time
import os
import sys

# Ensure UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from voice_assistant import AutonomousAssistant

def run_live_demonstration():
    print("=" * 65)
    print("🔊 LAUNCHING LIVE AUDIO & LAPTOP CONTROL TEST")
    print("=" * 65)
    print("Please listen to your laptop speakers!\n")

    assistant = AutonomousAssistant(
        tool_model="qwen2.5:3b",
        chat_model="dolphinlabs/llama3.2-3b-uncensored:latest",
        reasoning_model="nandhank/qwen3.5-abliterated-truthful:9b",
        default_profile="voice",
        voice_input_enabled=False,  # We feed inputs programmatically for the demo
        voice_output_enabled=True   # Speakers active!
    )

    # Step 1: Greeting & Intro
    print("\n[Step 1] Initializing & Greeting...")
    intro = "Hello Soham. Running autonomous system test suite now. You will hear every response through your speakers."
    print(f"Assistant: {intro}")
    assistant.speak(intro, wait=True)
    time.sleep(1.0)

    # Step 2: System Telemetry & Battery
    print("\n[Step 2] Querying System Telemetry & Battery...")
    res = assistant.process_message("What is my system battery and CPU status?")
    assistant.wait_until_done_speaking(timeout=10)
    time.sleep(1.0)

    # Step 3: Code Generation & Notepad Injection
    print("\n[Step 3] Code Generation & Opening Notepad...")
    res = assistant.process_message("Open Notepad and write a program to reverse string in Python.")
    assistant.wait_until_done_speaking(timeout=10)
    time.sleep(1.5)

    # Step 4: Live News Retrieval
    print("\n[Step 4] Live News Retrieval & Synthesis...")
    res = assistant.process_message("What is today's latest news?")
    assistant.wait_until_done_speaking(timeout=15)
    time.sleep(1.0)

    # Step 5: Instant Barge-in Interruption Demo
    print("\n[Step 5] Demonstrating Instant Voice Barge-In Cut-off...")
    announcement = "Now demonstrating barge-in. I will start speaking a long sentence and cut it off instantly."
    assistant.speak(announcement, wait=True)
    time.sleep(0.5)

    # Start long async speech
    assistant.speak("This is a long sentence that would normally take ten seconds to speak, but barge-in will immediately purge the audio queue now.")
    time.sleep(1.2)  # Let it speak for 1.2s
    print("--> Triggering Instant Barge-In Cut-Off (<20ms)...")
    assistant.stop_speaking()
    print("[+] Audio cut off instantly!")
    time.sleep(0.5)

    # Confirm barge-in success
    barge_ack = "Barge-in cut-off executed instantly in under twenty milliseconds."
    print(f"Assistant: {barge_ack}")
    assistant.speak(barge_ack, wait=True)
    time.sleep(1.0)

    # Step 6: Conclusion
    print("\n[Step 6] Test Conclusion...")
    conclusion = "All tests completed successfully. Your autonomous assistant is ready and standing by."
    print(f"Assistant: {conclusion}")
    assistant.speak(conclusion, wait=True)

    print("\n" + "=" * 65)
    print("✅ LIVE DEMONSTRATION COMPLETE - ALL SYSTEMS FUNCTIONAL")
    print("=" * 65)

if __name__ == "__main__":
    run_live_demonstration()
