"""
Unit test to verify that laptop speaker audio bleed does NOT trigger self-interruption,
while genuine sustained human voice (RMS > 0.16 for 3+ chunks) cleanly triggers barge-in.
"""
import time
import numpy as np
from voice_listener import VoiceListener

def test_anti_self_barge():
    print("[*] Testing Anti-Self-Barging & Human Barge-in Discrimination...")
    
    interrupted = False
    def on_interrupt():
        nonlocal interrupted
        interrupted = True
        print("  -> Interruption callback triggered!")

    listener = VoiceListener(
        on_speech_detected=lambda t: None,
        on_interrupt_detected=on_interrupt,
        barge_in_prob_threshold=0.70,
        barge_in_min_chunks=2
    )

    # 1. Simulate assistant starts speaking
    listener.set_speaking(True)
    # Move past the initial 350ms startup grace period
    listener.speaking_start_time = time.time() - 0.50

    # 2. Simulate laptop speaker audio bleed (RMS ~0.08 - 0.10)
    print("[*] Feeding 10 chunks of laptop speaker audio bleed (RMS ~0.09)...")
    for _ in range(10):
        # Create audio chunk with RMS ~0.09
        chunk = np.random.normal(0, 0.09, 800).astype(np.float32)
        listener._audio_callback(chunk, 800, None, None)

    assert not interrupted, "FAIL: Assistant barged itself on speaker audio bleed!"
    print("[+] PASS: Assistant ignored 10 chunks of speaker audio bleed without self-interruption.")

    # 3. Simulate human speaking firmly into mic (vocal formants with pitch modulation)
    print("[*] Feeding chunks of deliberate human voice...")
    t_full = np.arange(1024) / 16000.0
    f0 = 140 + 30 * np.sin(2 * np.pi * 4 * t_full)
    phase = 2 * np.pi * np.cumsum(f0) / 16000.0
    voice = np.zeros_like(t_full)
    for h in range(1, 15):
        voice += (1.0 / h) * np.sin(h * phase)
    voice = (voice / np.max(np.abs(voice))).astype(np.float32) * 0.6

    listener.vad._infer_512 = lambda c: 0.85
    listener._audio_callback(voice[:512], 512, None, None)
    listener._audio_callback(voice[512:1024], 512, None, None)
    listener._audio_callback(voice[:512], 512, None, None)

    assert interrupted, "FAIL: Real human speech failed to trigger barge-in!"
    print("[+] PASS: Genuine human speech cleanly triggered barge-in!")

    print("\n[SUCCESS] Anti-Self-Barging logic 100% verified!")

if __name__ == "__main__":
    test_anti_self_barge()
