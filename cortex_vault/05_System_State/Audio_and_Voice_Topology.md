---
title: "Host Audio Architecture & Neural Voice Topology"
type: "audio_topology"
tags:
  - cortex/system_state
  - cortex/audio
  - cortex/voice
last_updated: "2026-10-26"
status: "verified"
---

# 🎙️ Host Audio Architecture & Neural Voice Topology

Authoritative ground-truth topology for the somatosensory audio perception pipeline, neural TTS engines, and sub-10ms barge-in buffers.

## 🔊 Hardware Endpoints & Audio Interfaces
- **Output Endpoints**: Realtek High Definition Audio & NVIDIA High Definition Audio (DisplayPort/HDMI).
- **Microphone Input**: Realtek HD Audio Array (Internal beamforming microphone array, 48,000 Hz, 24-bit stereo).
- **Default Sample Rate**: `48,000 Hz` / 16-bit PCM for WebSockets; `24,000 Hz` MP3 MPEG for streamed neural TTS.

## 🗣️ Neural Voice Engine Personas
CortexOS maps distinct cognitive perspectives to verified Microsoft Edge neural voice models with single-flight mutex serialization to prevent overlapping audio:

| Persona | Voice Model Identifier | Frequency & Tone | Cognitive Perspective |
|---|---|---|---|
| **`JARVIS`** | `en-GB-RyanNeural` | Baritone, authoritative, precise | Executive & Primary Greeting / Goodbye |
| **`EDITH`** | `en-GB-SoniaNeural` | Crisp, rapid, analytical | `Analytic` Specialist Agent |
| **`GUY`** | `en-US-GuyNeural` | Conversational, direct, pragmatic | `Pragmatic` Specialist Agent |
| **`FRIDAY`** | `en-US-JennyNeural` | Measured, cautious, warm | `Cautious` Specialist Agent |

## 🛑 Sub-10ms Barge-In Mechanism
When the operator speaks or presses the microphone:
1. `bargeInStopVoice()` immediately sends an abort signal to the browser `Audio` element.
2. The server-side synthesis buffer flushes pending chunk streams.
3. Audio mutex unlocks to prevent audio collision and echo artifacts.
