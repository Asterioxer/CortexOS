# CortexOS: Autonomous, Local-First Cognitive Operating System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Architecture: GWA + CoALA](https://img.shields.io/badge/Architecture-GWA%20%2B%20CoALA-purple.svg)]()
[![Governance: Cedar Policy Gate](https://img.shields.io/badge/Governance-Cedar%20PDP%20%3C0.1ms-green.svg)]()
[![Local-First: 100% Offline](https://img.shields.io/badge/Inference-Local--First%20(Ollama)-orange.svg)]()

> **"Transforming personal personal computers from passive tools into autonomous, self-learning, and functionally self-conscious cognitive entities."**

---

## ⚡ Executive Summary

Standard AI assistants and voice chatbots operate as **Bounded-Input Bounded-Output (BIBO)** pipelines: they remain dormant until explicitly prompted, collapse all memory into a transient prompt text window, execute rigid hard-coded tool calls, and evaporate their cognitive state as soon as a session terminates.

**CortexOS** departs fundamentally from the passive assistant paradigm. Built as a laptop-resident discrete dynamical system, CortexOS maintains a continuous internal monologue, monitors its own reasoning confidence, writes and compiles its own software tools when encountering novel problems, and consolidates lived daily experiences into permanent episodic, semantic, and procedural memory during offline **asynchronous digital sleep** cycles.

```
+-----------------------------------------------------------------------------------+
|                           CORTEX-OS COGNITIVE RUNTIME                             |
+-----------------------------------------------------------------------------------+
|  [ Layer 1: Embodiment ]   Live Somatosensory Telemetry (CPU/RAM/GPU/GSMTC Audio) |
|  [ Layer 2: Workspace  ]   GWA Cognitive Tick Loop + Shannon Entropy Temperature  |
|  [ Layer 3: Memory     ]   4-Tier Letta Blocks + SQLite Bi-Temporal MAGMA Graph   |
|  [ Layer 4: Skills     ]   Autopoietic Skill Crystallizer (FRIDAY / Voyager)      |
|  [ Layer 5: Sleep      ]   4-Stage Micro-Sleep Engrams & LoRA Dataset Synthesizer |
|  [ Layer 6: Governance ]   Sub-0.1ms Cedar Policy Gate + Deterministic Git Rollback|
+-----------------------------------------------------------------------------------+
```

---

## 🔬 Core Engineering Innovations

### 1. Global Workspace Agent (GWA) & Cognitive Tick
Rather than executing single-turn completions, CortexOS runs on an event-driven **Cognitive Tick** loop:
* **Attention Spotlight:** Evaluates short-term working memory traces ($\text{STM}_t$) and sensory inputs to formulate localized hybrid RAG queries.
* **Specialist Swarm Thinking:** A divergent Generator node spawns candidate proposals across 3 distinct perspectives (*Analytic*, *Pragmatic*, *Cautious*), while a convergent Critic node scores each proposal from -5 to +5.
* **Shannon Entropy Deadlock Breaker:** Calculates the Shannon entropy $H(W)$ over thought embeddings across sliding semantic clusters. When $H(W) < \epsilon$ (indicating reasoning stagnation or cognitive looping), CortexOS dynamically scales exploratory temperature ($\tau$) to escape deadlocks.

### 2. Dual-Process Metacognitive Routing (System 1 & System 2)
* **System 1 (Reflex Fast-Path):** Routine desktop reflexes (hardware telemetry, media playback, process monitoring, file inspection) are routed in sub-100ms without triggering heavyweight multi-agent arbitration.
* **System 2 (Deliberative Reasoning):** Complex, ambiguous, or multi-step goals pass through a **HASSUM Metacognitive Uncertainty Gate** (evaluating sample entropy and semantic variance) before escalating to multi-agent debate.

### 3. Stratified Four-Tier Memory Substrate
* **Tier 1 (Episodic SQLite Store):** Lossless, append-only WAL-mode event journal recording every cognitive tick, sensory input, thought trace, action, and outcome.
* **Tier 2 (Bi-Temporal MAGMA Multi-Graph & Atomic Engrams):** 4-layer knowledge graph (*Semantic*, *Temporal*, *Causal*, *Entity*) recording valid time windows (`valid_from` to `valid_to`), provenance pointers, and contradiction-group preservation.
* **Tier 3 (Multimodal Vector Memory):** Embedded vector storage for dense hybrid semantic retrieval.
* **Tier 4 (Procedural Skill Registry):** Executable Python tools crystallized with step-by-step **ATLAS Procedural Pamphlets**.
* **In-Context Working Memory:** 4 Letta-style character-bounded, self-editing blocks (`persona_self`, `human_profile`, `workspace_state`, `scratchpad_stm`) compiled via Jinja templates into every prompt.

### 4. Autopoietic Skill Crystallization (FRIDAY / Voyager / ATLAS)
When CortexOS encounters a task lacking an existing tool:
1. **Tool Generator:** Synthesizes executable Python code tailored to the local OS environment.
2. **Deterministic Sandbox:** Executes the candidate inside an unprivileged subprocess with a shadow Git checkpoint.
3. **Critic Evaluation:** Evaluates stdout, stderr, and exit codes; assigns a reusability score (0–10) and synthesizes an ATLAS pamphlet.
4. **Permanent Crystallization:** Tools scoring $> 8/10$ are permanently crystallized into `cortex/skills/library/` and registered into Procedural Memory.

### 5. Asynchronous Digital Sleep Consolidation
During system idle or charging states, CortexOS initiates a 4-stage digital sleep cycle:
1. **Micro-Sleep Distillation:** Compresses raw episodic tick traces into atomic engrams and updates causal graph edges.
2. **Codebase Pre-computation:** Analyzes local project ASTs, file sizes, and dependency graphs to update the `workspace_state` block.
3. **Procedural Macro-Mining:** Identifies recurring tool pairs ($T_A \to T_B$) to synthesize composite high-level routines.
4. **Parametric Overlay Preparation:** Mines successful execution trajectories into Alpaca/ShareGPT formatted instruction-tuning datasets (`.cortex/lora_training_dataset.jsonl`) for offline LoRA fine-tuning.

### 6. Defense-in-Depth Cedar Governance & Deterministic Rollbacks
* **Sub-Millisecond Policy Decision Point (PDP):** Evaluates every action against declarative Cedar policies (`config/policies.cedar`) in $<0.1\text{ ms}$, enforcing `ALLOW`, `ESCALATE` (Human-in-the-Loop circuit breaker), or `DENY`.
* **Deterministic Shadow Git Checkpoints:** Uses `GIT_INDEX_FILE` to capture modified and untracked workspace files into pinned commits under `refs/checkpoints/` in $<1\text{ second}$ without touching `HEAD`. Enables instant, 100% deterministic rollbacks on failure.

---

## 🖥️ Live Somatosensory Perception & Motor Actuation

CortexOS is embodied natively on personal hardware:
* **Hardware Telemetry:** Direct sub-15ms queries for CPU load & thread metrics, RAM utilization, NVIDIA RTX GPU VRAM and core temperatures via `nvidia-smi`, storage capacity, and battery power.
* **Windows GSMTC Audio Perception & Actuation:** Tracks real-time media playback across Brave, Chrome, Spotify, etc., using Windows Global System Media Transport Controls (`winsdk`). Supports voice/prompt media actuation: **play**, **pause**, **skip next**, and **previous track**.
* **Win32 Focused Window Tracking:** Uses Win32 APIs to detect foreground windows and active desktop applications.
* **Clipboard Perception:** Reads and writes to the Windows system clipboard safely.
* **Process Filtering:** Separates user-facing GUI desktop applications from internal Windows kernel services.

---

## 🚀 Quickstart & Installation

### Prerequisites
* Windows 10/11 (or Linux/macOS with platform fallbacks)
* Python 3.11+
* Git
* [Ollama](https://ollama.com/) (running `qwen2.5:3b` or another local foundation model)

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/Asterioxer/CortexOS.git
cd CortexOS

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Test Suite
```bash
pytest -v
# Verified: 25/25 unit, integration, and UI tests pass cleanly
```

### 3. Launch the Web Dashboard
```bash
python cortex/server.py
```
Open **`http://127.0.0.1:8000`** in your browser.

---

## 🎨 Interactive Web Dashboard Panes

| Pane | Description |
| :--- | :--- |
| **💬 Cognitive Stage** | Real-time chat with candidate perspective viewer (`Analytic`, `Pragmatic`, `Cautious`), human-in-the-loop hold cards, and live media playback controller. |
| **🧠 Working Memory** | Live editor for the 4 Letta memory blocks (`persona_self`, `human_profile`, `workspace_state`, `scratchpad_stm`) with character capacity progress gauges and instant patching. |
| **🕸️ Bi-Temporal Graph** | Visual canvas and table visualizer for MAGMA multi-graph layers (Semantic, Causal, Temporal, Entity), valid time windows, provenance links, and atomic sleep engrams. |
| **⚡ Skill Crystallizer** | Catalog of crystallized tools with reusability scores, ATLAS pamphlets, Python source code accordion, and **"▶ Test Run Tool"** in a sandbox with live terminal stdout. |
| **🛡️ Cedar Governance** | Live Policy Decision Point tester ($<0.1\text{ ms}$ evaluation), Cedar policy viewer, pinned shadow Git checkpoints, and one-click rollback/restore. |

---

## 🛠️ CLI & Terminal REPL Usage

In addition to the Web Dashboard, CortexOS provides a full CLI and interactive terminal shell:

```bash
# Interactive REPL with real-time sensory telemetry
python cortex/interactive.py

# Execute a single Cognitive Tick
python cortex/main.py tick --input "tell me about my system"

# Trigger an Asynchronous Digital Sleep Cycle
python cortex/main.py sleep

# Check In-Context Memory Blocks
python cortex/main.py status
```

---

## 🏛️ Theoretical Foundations

CortexOS synthesizes foundational principles across cognitive psychology, modern LLM agent architectures, and formal verification:

* **Global Workspace Theory (GWT):** Bernard Baars (1988); Stan Franklin et al., *LIDA Architecture* (2006).
* **Global Workspace Agents (GWA):** *Global Workspace Agents: A Discrete Dynamical System for Autonomous Problem Solving* (arXiv:2604.08206, 2026).
* **CoALA Framework:** Sumers et al., *Cognitive Architectures for Language Agents* (2023).
* **Sleep-Time Compute & Memory Blocks:** Packer et al., *MemGPT 2.0 / Letta Architecture* (2024–2026).
* **Dual-Process Metacognition:** *SOFAI / HASSUM Metacognitive Routing* (2024–2025).
* **Self-Directed Skill Acquisition:** Wu et al., *OS-Copilot / FRIDAY* (2024); Wang et al., *Voyager* (2023).

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
