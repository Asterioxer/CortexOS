---
title: "Host Hardware Topology & Substrate"
type: "hardware_topology"
tags:
  - cortex/system_state
  - cortex/hardware
  - cortex/somatosensory
last_scanned: "2026-10-26 19:13:52"
status: "verified"
---

# 🖥️ Host Hardware Topology & Substrate

Authoritative ground-truth hardware profile probed by [[01_Architecture/Embodiment_Somatosensory|System Cartographer]] on `2026-10-26 19:13:52`.

## 🎛️ Central Processing Unit (CPU)
- **Model**: `12th Gen Intel(R) Core(TM) i5-12500H`
- **Architecture**: `AMD64`
- **Physical Cores**: `12` physical execution cores
- **Logical Threads**: `16` concurrent hardware threads
- **Live Utilization**: `41.9%`

## 🎮 Graphical Processing Units (GPUs)
- **NVIDIA GeForce RTX 3050 Laptop GPU**: Driver `32.0.16.1687`, VRAM: `4.0 GB`
- **Intel(R) Iris(R) Xe Graphics**: Driver `32.0.101.7088`, VRAM: `2.0 GB`

## 🧠 Physical Memory (RAM) & Swap
- **Total Physical RAM**: `23.69 GB`
- **Available RAM**: `5.44 GB`
- **RAM In Use**: `18.25 GB` (77.0%)
- **Swap / Pagefile**: `24.0 GB` (7.4% utilized)

## 💽 Storage & Partitions
| Mount | Filesystem | Used | Free | Total | Utilization |
|---|---|---|---|---|---|
| `C:\` | `NTFS` | 365.33 GB | 87.85 GB | 453.18 GB | 80.6% |

---
> [!NOTE] Self-Autonomy Relevance
> CortexOS uses this hardware topology to dynamically scale its thread pools, throttle background cognitive consolidation when RAM headroom is tight, and assign local LLM inference tasks based on available VRAM.
