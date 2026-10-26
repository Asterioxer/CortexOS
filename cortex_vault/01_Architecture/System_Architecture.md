---
title: "System Architecture & Cognitive Pipeline"
type: "architecture"
tags:
  - cortex/architecture
  - cortex/pipeline
  - cortex/gwa
last_updated: "2026-10-26"
---

# 🏗️ CortexOS System Architecture & Cognitive Pipeline

CortexOS is an autonomous, self-learning cognitive operating system embodied on the local laptop. It implements a synchronized **Global Workspace Architecture (GWA)** governed by deterministic policies and continuous self-reflection.

## 🔄 The 9-Stage Cognitive Pipeline

The runtime processes thought and action across 9 sequential stages:

```
[01 PERCEIVE] ──> [02 EMBODIMENT] ──> [03 RETRIEVE] ──> [04 SYSTEM 1]
                                                            │
    ┌───────────────────────────────────────────────────────┘
    ▼
[05 GENERATE] ──> [06 CRITIQUE] ──> [07 ARBITRATE] ──> [08 GOVERN] ──> [09 EXECUTE]
```

1. **Stage 1: Cognitive Perception (`PERCEIVE`)**:
   - Ingests operator textual queries, keyboard shortcuts, or ambient background wakeups.
   - Computes Shannon entropy of working memory to monitor reasoning state.

2. **Stage 2: Hardware Somatosensory (`EMBODIMENT`)**:
   - Updates hardware posture: CPU %, RAM GB, GPU utilization, active media playback (Spotify/Chrome), focused desktop window, battery level.
   - Employs [[01_Architecture/Embodiment_Somatosensory|SystemSomatosensory]] for physical OS perception.

3. **Stage 3: Hybrid Memory & Vault Retrieval (`RETRIEVE`)**:
   - Dual retrieval: [[01_Architecture/Memory_Substrate_4Tier|4-Tier Memory Substrate]] (Episodic WAL, Vector LoRA, Bi-Temporal Kùzu) PLUS `VaultRAG` semantic hybrid retrieval over `cortex_vault`.
   - Prevents hallucinations by surfacing canonical architectural facts and playbooks.

4. **Stage 4: System 1 Reflexive Fast-Path (`SYSTEM 1`)**:
   - Evaluates whether the operator request is a routine reflex (e.g., getting telemetry, opening an application, pausing audio).
   - If confidence exceeds 85%, executes reflex in sub-50ms bypass mode without full deliberation.

5. **Stage 5: Divergent Generator (`GENERATE`)**:
   - System 2 multi-perspective divergent generator producing 3 distinct candidate thoughts:
     - `Analytic`: Rigorous, detail-oriented, long-term stability.
     - `Pragmatic`: Action-oriented, fast execution, pragmatic outcome.
     - `Cautious`: Boundary-checked, policy-verified, restraint-focused.

6. **Stage 6: HASSUM & Convergent Critic Swarm (`CRITIQUE`)**:
   - Evaluates sample covariance matrix eigenvectors to measure semantic density and semantic entropy.
   - If uncertainty is high, flags metacognitive doubt.

7. **Stage 7: Metacognitive Executive Arbitration (`ARBITRATE`)**:
   - Evaluates candidate critiques and selects the optimal winning thought.
   - Emits transition tags: `[RESPONSE]`, `[THINK_MORE]`, or `[NO_OP]`.

8. **Stage 8: Cedar Policy & Sandboxed Governance (`GOVERN`)**:
   - Compares proposed action against Cedar safety policies in `config/policies.cedar`.
   - Actions classified as `ALLOW`, `ESCALATE` (human hold card), or `DENY`.
   - Shadow checkpoints created via [[01_Architecture/Governance_Cedar|GitShadowCheckpointManager]].

9. **Stage 9: Somatosensory & Shell Execution (`EXECUTE`)**:
   - Concrete execution of allowed actions: launching apps, modifying files, crystallizing skills, synthesis, or speech generation.
   - Audio synthesized via [[03_Decisions_ADR/ADR-002-Neural-Voice-Engine|Neural Voice Engine]] with monotonic epoch mutex to prevent voice collision.
