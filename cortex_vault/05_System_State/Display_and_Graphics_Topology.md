---
title: "Display Substrate & Dual-GPU Graphics Topology"
type: "display_topology"
tags:
  - cortex/system_state
  - cortex/gpu
  - cortex/display
last_updated: "2026-10-26"
status: "verified"
---

# 🖥️ Display Substrate & Dual-GPU Graphics Topology

Hardware acceleration profiles, display resolution pipes, and GPU compute capabilities on host `SOHAM`.

## 🖥️ Active Display Output
- **Resolution**: `1920 x 1080` (Full HD, 32-bit RGBA color depth, 60Hz/144Hz refresh).
- **Display Pipe**: Driven by Intel Iris Xe Graphics integrated controller via eDP internal display bus.
- **Window Management**: Windows DWM (Desktop Window Manager) with somatosensory active window tracking.

## 🎮 GPU Compute Acceleration Substrate
1. **Discrete GPU**: `NVIDIA GeForce RTX 3050 Laptop GPU`
   - **VRAM**: `4.0 GB GDDR6` dedicated high-speed video memory.
   - **Driver**: NVIDIA Game Ready / Studio Driver `32.0.16.1687`.
   - **CUDA Compute Capability**: `8.6` (Ampere Architecture).
   - **Role**: Heavy local LLM inference (Ollama, Qwen GGUF streaming), PyTorch tensor workloads, CUDA matrix kernels.

2. **Integrated GPU**: `Intel(R) Iris(R) Xe Graphics`
   - **VRAM**: `2.0 GB` dynamically allocated system memory.
   - **Driver**: Intel Graphics Driver `32.0.101.7088`.
   - **Role**: OS desktop rendering, hardware video decoding (H.264/HEVC/AV1), lightweight 3D Three.js canvas in Web UI.
