# 🤖 Autonomous Windows Voice & System Assistant

A fully local, zero-cloud desktop voice assistant and computer control system running on your **NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM)**, **Intel Core i5-12500H**, and **24GB RAM**.

---

## ✨ Features & Architecture

### 1. ⚡ Dual-Engine Parallel Architecture (100% GPU VRAM)
- **`qwen2.5:3b`** (~1.9 GB) -> **Primary Computer Control & Tool Calling** (Runs at **38.7 tokens/sec**, 0.24s prompt eval, 100% in GPU VRAM).
- **`dolphinlabs/llama3.2-3b-uncensored:latest`** (~3.4 GB) -> **Sentiment & Conversational Brain** (Runs at **22.9 tokens/sec**, completely abliterated/unfiltered).
- **`nandhank/qwen3.5-abliterated-truthful:9b`** (6.6 GB) -> **Heavyweight Deep Reasoning** fallback.

### 2. 🎙️ Autonomous Hands-Free Voice Listener (No `Win + H` Needed)
- Built-in continuous microphone listener using `sounddevice` and **`faster-whisper` (`tiny.en`)**.
- Uses Voice Activity Detection (VAD) to detect when you start and stop speaking.
- Automatically pauses the microphone while speaking to prevent audio feedback/echo loops.

### 3. 🧠 Sentiment & Emotion Awareness
- Real-time emotional tone analyzer detects user states: **Frustrated**, **Urgent**, **Excited**, **Confused**, **Grateful**, or **Neutral**.
- Dynamically steers the assistant persona:
  - *Frustrated / Stressed*: Speaks with direct empathy, cuts out pleasantries, fixes the problem immediately.
  - *Urgent*: Executes tasks with zero preamble and 1-sentence confirmation.
  - *Excited*: Matches high energy.

### 4. 🛡️ Almost Full System Control with Security Guardrails
- **Full Capabilities**:
  - Open & Close apps (`open_application`, `close_application`).
  - System Health: CPU %, RAM %, Disk space, and Battery status (`get_system_stats`).
  - Audio Volume & Mute control (`set_volume`).
  - File Explorer navigation & safe file creation (`create_text_file`, `open_folder`, `list_files`).
  - PowerShell execution (`run_powershell`).
- **Security Guardrails (Strictly Protected)**:
  - Automatically blocks attempts to read or export browser passwords (`Login Data`, `Cookies`).
  - Blocks SSH private keys (`.ssh/id_rsa`, `id_ed25519`).
  - Blocks secrets and `.env` files containing `API_KEY`, `PASSWORD`, `TOKEN`.
  - Blocks Windows Credential Manager (`cmdkey`, `vaultcmd`) and registry SAM hives.

### 5. 🚀 Auto-Start on Windows Boot
- Starts silently in the background or minimized every time your laptop boots up:
  - Enabled at: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\StartAutonomousAssistant.vbs`
  - Toggle anytime via:
    ```powershell
    python setup_autostart.py --enable
    python setup_autostart.py --disable
    python setup_autostart.py --status
    ```

### 6. 🗣️ Studio-Grade Natural Human Voices (v3.5)
- Replaced legacy robotic SAPI voices with **Azure Studio Neural Human Voices** with real breathing, intonation, and warmth.
- **Multiple Switchable Personas**:
  - `christopher`: Confident, friendly male human (Default)
  - `jenny`: Warm, conversational female human
  - `guy`: Casual, energetic male human
  - `aria`: Crisp, intelligent female assistant
  - `neerja` / `prabhat`: Natural Indian English voices
- **Fish Audio SDK Compatibility**: Ready for custom Fish Audio voice clones when `FISH_AUDIO_API_KEY` is provided.
- **Instant Sub-10ms Barge-In**: Hardware audio buffer instantly purges via `sounddevice.stop()` when interrupted.
- **Seamless Offline Resilience**: Automatically falls back to local Windows SAPI if offline without errors.

---

## 🎮 How to Run

### Option 1: One-Click Launch
Double-click:
```
C:\Users\soham\voice-lab\start_assistant.bat
```

### Option 2: From Terminal
```powershell
cd C:\Users\soham\voice-lab
.\oi_env\Scripts\python.exe voice_assistant.py
```

---

## 🗣️ Voice Commands to Try Out Loud

Just speak naturally into your microphone:
- *"Check my battery level and CPU usage"*
- *"Open Notepad and write down my grocery list"*
- *"Close Notepad"*
- *"I am really stressed and frustrated with work right now"*
- *"Set system volume to 60 percent"*
- *"Search the web for the latest NASA news"*
- *"List files in my downloads folder"*
- *"Open Notepad and write a program to reverse string in Python"*
- *`/persona jenny` (switches to Jenny's female neural voice)*
- *`/persona christopher` (switches to Christopher's male neural voice)*
- *"Stop"* (instantly interrupts audio playback in <10ms)
- *"Exit the program"* (shuts down back to terminal)
