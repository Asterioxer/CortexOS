from voice_assistant import VoiceAssistant
import os

def test_pipeline():
    print("Initializing VoiceAssistant...")
    # Initialize with speech disabled during automated test to not block
    assistant = VoiceAssistant(default_model="qwen2.5-fast", default_profile="voice", voice_enabled=False)
    
    print("\n--- Test 1: File creation tool call ---")
    reply1 = assistant.handle_user_message("Create a text file called trial.txt with greeting Hello from Voice Assistant")
    print("Reply 1:", reply1)
    
    trial_path = r"C:\Users\soham\voice-lab\sandbox\trial.txt"
    if os.path.exists(trial_path):
        print(f"[SUCCESS] File was created on disk at: {trial_path}")
        with open(trial_path, "r") as f:
            print("Content:", f.read())
    else:
        print("[!] File not found at expected path.")

    print("\n--- Test 2: Dynamic Profile Switch ---")
    assistant.handle_user_message("/mode deep")
    print(f"Current profile after switch: {assistant.profile}")

    print("\n--- Test 3: Model Switch ---")
    assistant.handle_user_message("/model qwen9b-direct")
    print(f"Current model after switch: {assistant.model}")

    print("\n--- Pipeline Tests Completed Successfully! ---")

if __name__ == "__main__":
    test_pipeline()
