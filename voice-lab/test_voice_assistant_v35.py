import time
from voice_assistant import AutonomousAssistant

def test_v35():
    print("Testing Assistant v3.5 (Studio Human Neural Voice + Offline Resilience)...")
    assistant = AutonomousAssistant(
        voice_input_enabled=False,
        voice_output_enabled=True
    )

    print(f"Active Voice Persona: {assistant.voice_engine.persona_name}")
    assert assistant.voice_engine.persona_name == "christopher"

    # Test Persona switch
    res_persona = assistant.process_message("/persona jenny")
    print("Persona switch reply:", res_persona)
    assert assistant.voice_engine.persona_name == "jenny"

    # Test Greeting message
    print("\nTesting greeting speech with Jenny Neural...")
    reply = assistant.process_message("Hello there!")
    print("Greeting reply:", reply)
    assistant.wait_until_done_speaking(timeout=8)

    # Test System Stats with speech
    print("\nTesting system stats with speech...")
    reply_stats = assistant.process_message("What is my CPU and battery status?")
    print("Stats reply:", reply_stats)
    assistant.wait_until_done_speaking(timeout=8)

    print("\n[+] V3.5 INTEGRATION TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_v35()
