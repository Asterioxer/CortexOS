import asyncio
import edge_tts
import io
import soundfile as sf
import sounddevice as sd
import time
import threading

class NeuralVoiceEngine:
    VOICES = {
        "jenny": "en-US-JennyNeural",
        "christopher": "en-US-ChristopherNeural",
        "guy": "en-US-GuyNeural",
        "aria": "en-US-AriaNeural",
        "neerja": "en-IN-NeerjaNeural",
        "prabhat": "en-IN-PrabhatNeural"
    }

    def __init__(self, voice_name: str = "christopher"):
        self.voice_name = voice_name
        self.active_voice = self.VOICES.get(voice_name.lower(), "en-US-ChristopherNeural")
        self._is_speaking = False
        self._playback_thread = None

    def is_speaking(self) -> bool:
        return self._is_speaking

    def stop(self):
        """Instant sub-10ms cut-off for barge-in."""
        self._is_speaking = False
        try:
            sd.stop()
        except Exception:
            pass

    async def _synthesize(self, text: str) -> bytes:
        comm = edge_tts.Communicate(text, self.active_voice, rate="+5%", pitch="+0Hz")
        buffer = bytearray()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                buffer.extend(chunk["data"])
        return bytes(buffer)

    def speak(self, text: str, wait: bool = False):
        self.stop()
        self._is_speaking = True

        def _worker():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                raw_bytes = loop.run_until_complete(self._synthesize(text))
                loop.close()

                if not self._is_speaking:
                    return

                # Decode audio via soundfile
                data, samplerate = sf.read(io.BytesIO(raw_bytes), dtype="float32")
                
                if not self._is_speaking:
                    return

                # Play via sounddevice
                sd.play(data, samplerate)
                # Wait until finished or stopped
                duration = len(data) / samplerate
                t0 = time.time()
                while sd.get_stream() and sd.get_stream().active and self._is_speaking:
                    time.sleep(0.05)
                    if time.time() - t0 > duration + 0.5:
                        break
            except Exception as e:
                print(f"[!] Neural voice error: {e}")
            finally:
                self._is_speaking = False

        if wait:
            _worker()
        else:
            self._playback_thread = threading.Thread(target=_worker, daemon=True)
            self._playback_thread.start()

if __name__ == "__main__":
    engine = NeuralVoiceEngine("christopher")
    print("Testing Christopher Neural voice...")
    engine.speak("Hey there Soham! I'm now speaking with Christopher's natural human voice. How does this sound to you?", wait=True)
    print("Done test!")
