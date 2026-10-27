---
title: "Host Hardware Topology & Substrate"
type: "hardware_topology"
tags:
  - cortex/system_state
  - cortex/hardware
  - cortex/somatosensory
last_scanned: "2026-10-27 08:57:00"
status: "verified"
---

# 🖥️ Host Hardware Topology & Substrate

Authoritative ground-truth hardware profile probed by [[01_Architecture/Embodiment_Somatosensory|System Cartographer]] on host node `SOHAM`.

---

## 🎛️ Motherboard & System Baseboard
- **Manufacturer**: Dell Inc.
- **Product Model**: `053JTT` (Version `A05`) — Dell G15 5520 Gaming Chassis
- **Chassis Architecture**: Mobile Performance Workstation
- **PCIe Subsystem**: PCIe Gen4 x4 NVMe lanes + PCIe Gen4 x8 dGPU interconnect

---

## ⚙️ Central Processing Unit (CPU)
- **Model**: Intel® Core™ i5-12500H Processor (12th Gen Alder Lake-H)
- **Architecture**: `AMD64` (Intel 7 lithography, 45W Base TDP / 95W Max Turbo)
- **Execution Units**:
  - Physical Cores: **12 Cores** (4 Performance-Cores Golden Cove + 8 Efficient-Cores Gracemont)
  - Logical Threads: **16 Threads**
- **Clocks & Cache**:
  - P-Core Max Turbo: **4.50 GHz** (Base: 2.50 GHz)
  - E-Core Max Turbo: **3.30 GHz** (Base: 1.80 GHz)
  - Total Cache: **18 MB Intel® Smart Cache** (L3) + 1.25 MB L2 per P-core
- **Instruction Capabilities**: AVX2, FMA3, AVX-VNNI (Accelerates local 4-bit/8-bit quantized tensor arithmetic in Ollama and llama.cpp)

---

## 🧠 High-Speed Memory Subsystem (DDR5 RAM)
- **Total Physical Memory**: **`23.69 GB` (~24.0 GB)**
- **Memory Standard**: **DDR5 SDRAM @ 4800 MT/s**
- **Physical Module Topology**:
  - **Slot 1 (Bank 0)**: `Crucial CT16G48C40S5.C8A1` — **16 GB DDR5-4800 SO-DIMM**
  - **Slot 2 (Bank 0)**: `Micron MTC4C10163S1SC48BA1` — **8 GB DDR5-4800 SO-DIMM**
- **Current Operational Metrics**:
  - In Use: ~16.92 GB (~71.4%)
  - Available Headroom: **~6.77 GB** uncommitted buffer
  - Paging File: 24.0 GB system-managed commit limit

---

## 🎮 Dual Graphical Processing Units (Dual-GPU Substrate)

### 1. Discrete GPU (CUDA & Tensor Acceleration)
- **Model**: NVIDIA® GeForce RTX™ 3050 Laptop GPU (Ampere GA107M)
- **CUDA Cores**: 2,048
- **Tensor Cores**: 64 (3rd Gen) | **RT Cores**: 16 (2nd Gen)
- **Dedicated VRAM**: **`4,096 MiB` (4.0 GB) GDDR6** (128-bit bus width, 192 GB/s)
- **Driver Version**: `32.0.16.1687` (NVIDIA WDDM 3.2, DirectML & CUDA 12.x)
- **Live Memory Footprint**: ~237 MiB active / **3,726 MiB free headroom**
- **Primary Role**: Local LLM neural inference (`qwen2.5:3b`, `llama3.2-3b`, `qwen3.5:9b`), ONNX speech embeddings.

### 2. Integrated GPU (Display & Media Compositing)
- **Model**: Intel® Iris® Xe Graphics Family (Alder Lake-H GT2, 80 Execution Units)
- **Shared Memory**: Dynamically allocated system DDR5 RAM pool (~2.0 GB)
- **Driver Version**: `32.0.101.7088` (Intel WDDM 3.1)
- **Primary Role**: 120 Hz display compositing, QuickSync hardware media decoding.

---

## 💽 High-Speed NVMe Storage Subsystem
- **Physical Drive Model**: **Micron 2450 NVMe 512GB** (`Micron_2450_MTFDKCD512TFK`)
- **Interface**: PCIe Gen4 x4 NVMe 1.4 M.2 2280
- **Partition Allocation**:
  | Mount | Partition Type | Capacity | Space Used | Available Free | Utilization |
  |---|---|---|---|---|---|
  | `C:\` | OS & Workspaces (NTFS) | **453.18 GB** | **361.01 GB** | **92.17 GB** | **79.7%** |

---

## 🔌 Thermal, Power & Acoustic Management
- **Power Delivery**: AC Mains Connected (Dell 180W / 240W Barrel Adapter)
- **Battery Status**: 100% capacity maintained
- **Acoustic / Fan Profile**: Dell Alienware Command Center Thermal Mode: Balanced / Performance

---
## Related Notes
- [[05_System_State/System_Telemetry|Live System Telemetry]]
- [[05_System_State/Display_and_Graphics_Topology|Display & Graphics Topology]]
- [[05_System_State/Local_Inference_Topology|Local Inference Topology]]
- [[01_Architecture/Local_Ollama_Inference_Substrate|Local Ollama Inference Substrate]]
