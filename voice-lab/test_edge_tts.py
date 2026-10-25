import asyncio
import edge_tts
import io
import soundfile as sf
import sounddevice as sd
import time

async def test_neural_voice():
    voice = "en-US-JennyNeural"
    text = "Hello Soham! This is my new natural neural voice. It sounds just like a real person talking to you, with natural rhythm and breathing."
    print(f"Synthesizing with {voice}...")
    t0 = time.time()
    communicate = edge_tts.Communicate(text, voice)
    audio_bytes = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes.extend(chunk["data"])
    dt = time.time() - t0
    print(f"Synthesized {len(audio_bytes)} bytes in {dt:.2f}s!")

    # Read audio into numpy via soundfile
    data, samplerate = sf.read(io.BytesIO(audio_bytes))
    print(f"Playing audio through speakers (Duration: {len(data)/samplerate:.2f}s)...")
    sd.play(data, samplerate)
    sd.wait()
    print("Done playing!")

if __name__ == "__main__":
    asyncio.run(test_neural_voice())
