---
title: "Voice and Speech Lab Workspace"
type: "workspace_catalog"
tags:
  - cortex/workspaces
  - cortex/voice_lab
  - cortex/tts
  - cortex/audio_dsp
last_updated: "2026-10-27"
status: "verified"
---

# 🎙️ Voice and Speech Lab Workspace

- **Location**: `C:\Users\soham\Desktop\voice-lab`
- **Domain**: Neural Audio Synthesis, Text-to-Speech (TTS), Speech-to-Text (STT)
- **Primary Toolchains**: Python 3.11/3.12, PyAudio, sounddevice, Kokoro-82M ONNX, pyttsx3, Piper TTS
- **Hardware Target**: NVIDIA GeForce RTX 3050 Laptop GPU (CUDA/DirectML) + Realtek High Definition Audio

## Purpose and Scope
`voice-lab` is the designated experimental sandbox for Soham's audio and voice research. Work here informs and enhances the neural voice pipeline of CortexOS:
1. **Multi-Engine Evaluation**: Benchmarking Kokoro-82M ONNX vs. Piper TTS vs. SAPI5 `pyttsx3` for latency, natural inflection, and compute overhead.
2. **Audio Echo & Overlap Prevention**: Developing queue-based mutual exclusion mechanisms so multiple voice engines or concurrent threads do not speak simultaneously or trigger sound card feedback loops.
3. **Phonetic Grounding**: Tuning pronunciation dictionaries and phonetic mappings for technical terms (e.g., GWA, Cedar, Letta, Autopoiesis, CUDA).

## Integration with CortexOS
CortexOS's internal module [`cortex/voice_assistant.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/voice_assistant.py) and [`cortex/vault/trigger_router.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/vault/trigger_router.py) interface directly with voice models:
- **Default System Voice**: JARVIS persona (pyttsx3 David / SAPI5) for low-latency system status announcements.
- **Secondary Voices**: Guy (conversational developer companion), Edith (tactical), Friday, Christopher.
- **Voice Trigger**: Invoking `open project voice-lab` instantly opens this workspace in VS Code and switches the pair programming context.

---
## Related Notes
- [[05_System_State/Audio_and_Voice_Topology|Audio and Voice Topology]]
- [[03_Decisions_ADR/ADR-002-Neural-Voice-Engine|ADR-002 Neural Voice Engine]]
- [[04_Skills_Catalog/Trigger_Registry|Deterministic Trigger Registry]]
- [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]]
