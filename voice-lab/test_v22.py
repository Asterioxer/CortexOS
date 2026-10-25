from voice_assistant import AutonomousAssistant

def test_v22():
    print("Testing Assistant v2.2...")
    assistant = AutonomousAssistant(
        voice_input_enabled=False,
        voice_output_enabled=False
    )

    print("\n--- Test 1: Real Live News Retrieval ---")
    reply1 = assistant.process_message("What is the latest news regarding Rahul Gandhi, Marco Rubio, and S. Jaishankar?")
    print("Report summary:")
    print(reply1[:300] + "...")

    print("\n--- Test 2: Voice Exit Trigger Check ---")
    analysis = assistant.analyzer.analyze("No, stop the program, exit out of this shell, you can go home now.")
    print("Exit command analysis:", analysis["intent"])
    assert analysis["intent"] == "EXIT", "Failed to detect voice exit intent"

    print("\n[+] V2.2 TESTS PASSED!")

if __name__ == "__main__":
    test_v22()
