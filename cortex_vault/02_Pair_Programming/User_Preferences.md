---
title: "Operator Profile & Behavioral Preferences"
type: "pair_programming"
tags:
  - cortex/operator
  - cortex/preferences
  - cortex/autonomy
  - cortex/profile
last_updated: "2026-10-27"
status: "verified"
---

# 👤 Operator Profile & Behavioral Preferences

- **Lead Operator & Architect**: Soham
- **Primary Workstation**: Dell G15 Windows 11 Laptop (`Node: Soham`)
- **Core Engineering Domains**:
  1. *Artificial Intelligence & Cognitive Agents*: GWA architectures, Letta tiered memory, local LLM quantization (Qwen/LLaMA on Ollama & llama.cpp), AI alignment and human-agent approval boundaries research.
  2. *Web3 & Smart Contracts*: Solidity EVM contracts (ERC-20, ERC-721, ERC-1155), Bitcoin cryptographic algorithms (SHA-256 miners, secp256k1 curves), Remix IDE.
  3. *Quantitative Finance & Machine Learning*: Algorithmic backtesting (`backtest.py`), technical indicator feature engineering, time-series forecasting.
  4. *Full-Stack Web & Mobile*: Next.js, Flask, SpringBoot, Flutter, Docker containerization.

---

## Autonomy Boundaries & Operational Directives

### 1. Direct Execution Autonomy
- **Full System Autonomy Mandate**: Soham expects CortexOS to possess direct, hands-on control over his operating system. When an action is expected (e.g. opening VS Code, switching projects, probing network sockets, running tests, adjusting audio volume, auditing git trees), CortexOS must execute it autonomously without passive hand-wringing.
- **System 1 Fast-Path**: Routine queries and actions must execute reflexively (<10ms) via deterministic trigger routing and `SystemSomatosensory` rather than waiting for multi-second speculative LLM deliberation.
- **Cedar Containment Guardrails**: File modifications outside the project root and dangerous system-level shutdowns require explicit human confirmation.

### 2. UI / UX Design Directives
- **Zero-Lag Static Architecture**: Disallow heavy full-screen WebGL 3D render loops, particle clouds, and 3D card tilt physics that consume CPU/GPU cycles, blur low-DPI text, or cause mouse click displacement.
- **Fast 2D HUD Layout**: Clean static dark cyberpunk theme (`#080c16`), high-contrast badges, and 1-click Quick-Action chips for high-frequency operations.
- **Header Controls**: Instant access to `[ 👋 Greet ]` (session status welcome) and `[ 🛑 STAND DOWN ]` (memory consolidation + vault git commit + standby mode).
- **Responsive Navigation**: All 7 tabs (`Stage`, `Memory`, `Graph`, `Skills`, `Governance`, `Execution`, `Vault`) must maintain instant tab-switching responsiveness with proper scrolling padding.

### 3. Audio & Voice Synthesizer Directives
- **Single-Speaker Mutex**: Never allow multiple speech synthesizers (e.g. SAPI5, Kokoro, Piper, browser Web Audio) to speak concurrently. Switching personas must instantly halt any active audio buffer.
- **Echo & Feedback Elimination**: Audio playback must not re-trigger microphone speech recognition or create feedback loops.
- **Default Personas**:
  - `JARVIS`: Formal baritone for session greetings, hardware alerts, and shutdown announcements.
  - `Guy`: Direct, energetic conversational companion for pair programming and code discussion.
  - `Edith`: Tactical assistant for cartography, security, and hardware telemetry scans.

### 4. Local Inference & Anti-Hallucination Directives
- **Local-First Zero Cloud**: All neural cognition must run locally via Ollama on the host **NVIDIA GeForce RTX 3050 Laptop GPU** (`qwen2.5:3b`, `llama3.2-3b`, `qwen3.5:9b`, `gemma3:4b`).
- **Strict Grounding**: The model must never hallucinate imaginary files or invent non-existent capabilities. Answers must cite and align with the ground truth stored in this **Obsidian Knowledge Vault**.

---
## Related Notes
- [[00_Index|CortexOS Master Knowledge Vault]]
- [[02_Pair_Programming/Active_Context|Active Living Context]]
- [[02_Pair_Programming/Execution_Playbooks|Execution Playbooks]]
- [[04_Skills_Catalog/Trigger_Registry|Deterministic Trigger Registry]]
- [[05_System_State/Operator_Profile_and_Habits|Operator Profile & Tool Ergonomics]]
