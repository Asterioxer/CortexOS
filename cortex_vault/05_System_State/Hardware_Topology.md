---
title: "Host Hardware Topology & Substrate"
type: "hardware_topology"
tags:
  - cortex/system_state
  - cortex/hardware
  - cortex/somatosensory
last_scanned: "2026-10-26 20:04:00"
status: "verified"
---

# 🖥️ Host Hardware Topology & Substrate

Authoritative ground-truth hardware profile probed by [[01_Architecture/Embodiment_Somatosensory|System Cartographer]] on `2026-10-26 20:04:00`.

## 🎛️ Central Processing Unit (CPU)
- **Model**: `12th Gen Intel(R) Core(TM) i5-12500H`
- **Architecture**: `AMD64`
- **Physical Cores**: `12` physical execution cores
- **Logical Threads**: `16` concurrent hardware threads
- **Live Utilization**: `43.3%`

## 🎮 Graphical Processing Units (GPUs)
- **NVIDIA GeForce RTX 3050 Laptop GPU**: Driver `32.0.16.1687`, VRAM: `4.0 GB`
- **Intel(R) Iris(R) Xe Graphics**: Driver `32.0.101.7088`, VRAM: `2.0 GB`

## 🧠 Physical Memory (RAM) & Swap
- **Total Physical RAM**: `23.69 GB`
- **Available RAM**: `3.76 GB`
- **RAM In Use**: `19.94 GB` (84.1%)
- **Swap / Pagefile**: `24.0 GB` (0.2% utilized)

## 💽 Storage & Partitions
| Mount | Filesystem | Used | Free | Total | Utilization |
|---|---|---|---|---|---|
| `C:\` | `NTFS` | 366.12 GB | 87.07 GB | 453.18 GB | 80.8% |

---
> [!NOTE] Self-Autonomy Relevance
> CortexOS uses this hardware topology to dynamically scale its thread pools, throttle background cognitive consolidation when RAM headroom is tight, and assign local LLM inference tasks based on available VRAM.
