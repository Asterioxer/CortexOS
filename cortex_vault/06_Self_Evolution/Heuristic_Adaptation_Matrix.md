---
title: "Heuristic Adaptation Matrix & Dynamic Arbitration Parameters"
type: "heuristic_matrix"
tags:
  - cortex/evolution
  - cortex/heuristics
  - cortex/parameters
last_updated: "2026-10-26"
status: "active"
---

# ⚖️ Heuristic Adaptation Matrix & Dynamic Arbitration Parameters

This matrix governs how CortexOS tunes its tri-perspective cognitive arbitration biases (`Analytic`, `Pragmatic`, `Cautious`), dynamic generation temperature, and autonomous execution confidence thresholds.

## 🎚️ Active Arbitration Bias Weights

| Perspective | Current Weight | Adaptation Vector | Activation Triggers |
|---|---|---|---|
| **`Analytic`** | `0.31` | Increments on structural anomalies, unfamiliar tools, or syntax errors | Complex architectural design, diff reconciliation, debugging |
| **`Pragmatic`** | `0.31` | Increments on high-confidence pairing, repetitive tasks, and tool execution | Direct command execution, note taking, telemetry lookup |
| **`Cautious`** | `0.38` | Increments on resource pressure (>85% RAM/Disk) or external mutations | Destructive file commands, daemon reconfiguration, autostart changes |

$$\sum (W_A, W_P, W_C) = 1.0$$

---

## 🌡️ Dynamic Temperature Regulation
The cognitive generation temperature ($T$) is not hardcoded. It dynamically scales based on measured environmental and semantic entropy:

$$T = \text{clamp}(0.15, 0.75, T_{\text{base}} + \Delta_T \cdot \text{Entropy})$$

- **$T_{\text{base}} = 0.35$**: Grounded baseline for deterministic, unhallucinated responses.
- **$\Delta_T = 0.25$**: Exploration variance.
- When Entropy is low ($0.0 \le E \le 0.3$), $T \approx 0.35$ (precise, structured execution).
- When Entropy is high ($E \ge 0.8$), $T \approx 0.55 - 0.70$ (creative architectural reasoning).

---

## 🎯 Autonomy Execution Confidence Thresholds
- **$\theta_{\text{auto}} = 0.80$**: Threshold required for dispatching Tier-1 autonomous operations without human intervention.
- **$\theta_{\text{escalate}} = 0.40$**: If arbitration score falls below this, the system halts and queries operator Soham for guidance.
- **StallBreaker Watchdog Gate**: Hard-coded hardware deadline of `45.0s`.

---
> [!NOTE] Self-Tuning
> [[06_Self_Evolution/Autonomous_Evolution_Architecture|SelfEvolutionEngine]] automatically adjusts these weights during each evolution cycle based on task success feedback and environmental health.
