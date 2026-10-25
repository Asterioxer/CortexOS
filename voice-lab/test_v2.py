from voice_assistant import AutonomousAssistant

def test_v2():
    print("Testing Assistant v2.0...")
    assistant = AutonomousAssistant(
        voice_input_enabled=False,
        voice_output_enabled=False
    )

    print("\n--- Test 1: 'All right.' ---")
    r1 = assistant.process_message("All right.")
    print("Result 1:", r1)

    print("\n--- Test 2: 'Hello.' ---")
    r2 = assistant.process_message("Hello.")
    print("Result 2:", r2)

    print("\n--- Test 3: Adele song request in Brave ---")
    r3 = assistant.process_message("Brave is already open, selected and you need to play the song called Love Song by Adele.")
    print("Result 3:", r3)

    print("\n--- Test 4: 'Stop' interrupt command ---")
    r4 = assistant.process_message("Stop talking please.")
    print("Result 4:", r4)

    print("\n--- Test 5: Battery check ---")
    r5 = assistant.process_message("Check my battery level.")
    print("Result 5:", r5)

if __name__ == "__main__":
    test_v2()
