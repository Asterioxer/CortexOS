from faster_whisper import WhisperModel
import time

print("Testing faster-whisper tiny.en initialization...")
t0 = time.time()
model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
print(f"Loaded tiny.en in {time.time() - t0:.2f}s")
