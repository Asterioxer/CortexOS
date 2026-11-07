# LiveVoice integration notes

This change adds the missing microphone capture and token-to-speech building blocks.
It intentionally does not replace the existing assistant orchestration automatically:
the assistant currently assumes completed text responses and needs a follow-up wiring
change to preserve its memory/governance/tool-routing behavior.

## Components

- `cortex.embodiment.live_audio.CortexVoiceListener`: 16 kHz microphone capture,
  bounded frame queue, VAD segmentation, Faster-Whisper transcription, phantom
  phrase filtering, optional wake-word filtering, and asynchronous callbacks.
- `cortex.inference.streaming.OllamaChatStreamer`: reads NDJSON token deltas from
  the same `LocalInferenceClient.base_url` and `.model` configuration.
- `cortex.embodiment.streaming_tts.EdgeSentenceStreamer`: synthesizes completed
  sentences using the existing `CortexVoiceEngine.PERSONAS` data and plays them
  while later tokens continue to arrive.

## Wiring example

```python
from cortex.embodiment.live_audio import CortexVoiceListener
from cortex.embodiment.streaming_tts import EdgeSentenceStreamer
from cortex.inference.streaming import OllamaChatStreamer
from cortex.embodiment.voice import CortexVoiceEngine
from cortex.inference.client import LocalInferenceClient

llm = LocalInferenceClient()
streamer = OllamaChatStreamer(llm)
voice = CortexVoiceEngine()
speech = EdgeSentenceStreamer(voice.PERSONAS, persona=voice.active_persona)

def respond(text: str):
    messages = [{"role": "user", "content": text}]
    speech.speak_stream(streamer.stream_chat(messages))

listener = CortexVoiceListener(
    on_speech_detected=respond,
    on_interrupt_detected=speech.stop,
)
listener.start()
```

The example is a minimal smoke path, not a replacement for CortexOS's current
cognitive orchestration. Before production use, route the transcript through the
existing assistant handler and preserve the system prompt, conversation history,
governance checks, and tool approval path. The current generator is cancelled when
the consumer closes it; cancellation may wait for the next network read to return.

## Dependencies and runtime

Existing project modules already depend on `sounddevice`, `soundfile`,
`faster-whisper`, `edge-tts`, `numpy`, and `httpx`. Ensure they are installed
in the active environment. Microphone permissions and a working input/output device
are required.

## Known limitations

- TTS streams by sentence, not raw PCM frames; it waits for a sentence boundary.
- Echo cancellation is not included. Use a full-duplex AEC implementation before
  enabling simultaneous speaker playback and microphone capture.
- The listener currently uses CPU Faster-Whisper `tiny.en`; benchmark other models
  on target hardware before changing defaults.
- No hardware audio test is claimed by this PR.
