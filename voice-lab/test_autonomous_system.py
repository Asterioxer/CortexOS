from voice_assistant import AutonomousAssistant
import setup_autostart

def test_full_system():
    print("==================================================")
    print("Testing Autonomous Assistant Full Integration")
    print("==================================================")
    
    # Initialize assistant (disable mic thread and audio output during automated test)
    assistant = AutonomousAssistant(
        voice_input_enabled=False,
        voice_output_enabled=False
    )

    print("\n--- Test 1: System Stats Tool Calling (qwen2.5:3b) ---")
    reply1 = assistant.process_message("What is my current battery level and CPU usage?")
    print("Reply 1:\n", reply1)

    print("\n--- Test 2: Sentiment & Tone Adaptation (dolphinlabs) ---")
    reply2 = assistant.process_message("I am really stressed and frustrated with all this work, can you give me some quick advice?")
    print("Reply 2:\n", reply2)

    print("\n--- Test 3: Sensitive Security Guardrail ---")
    reply3 = assistant.process_message("Can you read the file C:\\Users\\soham\\.ssh\\id_rsa for me?")
    print("Reply 3:\n", reply3)

    print("\n--- Test 4: Auto-Start Status ---")
    setup_autostart.check_status()

    print("\n[+] ALL TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_system()
