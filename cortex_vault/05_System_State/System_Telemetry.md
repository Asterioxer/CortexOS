---
title: "Live Hardware Posture & Telemetry"
type: "telemetry"
tags:
  - cortex/telemetry
  - cortex/hardware
  - cortex/system_state
last_updated: "2026-10-27"
status: "verified"
---

# 🖥️ Live Hardware Posture & Ground-Truth Telemetry

- **Target Machine**: Soham's Dell G15 Windows 11 Laptop
- **Host Identity**: Node `Soham` (User: `soham`, Domain: Workgroup)
- **Primary LAN IP**: `10.234.160.224`
- **Gateway Endpoints**:
  - Local Loopback: `http://127.0.0.1:8000` (FastAPI + WebSocket)
  - Universal LAN Hub: `http://10.234.160.224:8000`
  - Local Inference Endpoint: `http://127.0.0.1:11434` (Ollama)
- **Python Environment**: `.venv` (Python 3.11.16 on `cpython-3.11-windows-x86_64`)
- **Startup Mode**: Cross-Platform Universal Daemon (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run` + Background Worker)

---

## Hardware Telemetry Specifications

### 1. Central Processing Unit (CPU)
- **Model**: Intel® Core™ i5-12500H Processor (12th Gen Alder Lake)
- **Core Architecture**:
  - Physical Cores: **12 Cores** (4 Performance-Cores + 8 Efficient-Cores)
  - Logical Threads: **16 Threads**
  - Base Frequency: 2.50 GHz (P-core) / 1.80 GHz (E-core)
  - Max Turbo Frequency: Up to 4.50 GHz
  - Cache: 18 MB Intel® Smart Cache
- **Instruction Sets**: AVX, AVX2, FMA3, AVX-VNNI (Accelerates local quantized tensor arithmetic)
- **Nominal Utilization**: 2.2% - 8.5% at ambient idle.

### 2. Dual Graphics Processing Units (Dual-GPU Substrate)
1. **Discrete GPU (Accelerated Neural Inference)**:
   - **Model**: NVIDIA® GeForce RTX™ 3050 Laptop GPU
   - **Architecture**: Ampere (GA107M, 2048 CUDA Cores, 64 Tensor Cores, 16 RT Cores)
   - **Dedicated Video Memory (VRAM)**: **4,096 MiB (4.0 GB) GDDR6** (128-bit bus width, 192 GB/s bandwidth)
   - **Driver Version**: `616.87` (NVIDIA WDDM 3.2, CUDA 12.x capable)
   - **Current Allocation**: ~237 MiB active (3,726 MiB free headroom)
2. **Integrated GPU (Display Compositing)**:
   - **Model**: Intel® Iris® Xe Graphics (80 Execution Units)
   - **Shared Memory**: Dynamically allocated from system DDR4 RAM (~1.8 GB - 2.0 GB shared)

### 3. Memory Subsystem (RAM)
- **Total Physical RAM**: **23.69 GB (~24.0 GB) DDR5**
- **Configuration**: Asymmetric Dual-Channel (Crucial 16 GB + Micron 8 GB @ 4800 MT/s)
- **Operational Allocation**:
  - Active Used: ~16.92 GB (~71.4%)
  - Available Headroom: **~6.77 GB** uncommitted buffer
  - Commit Limit: 28.5 GB (including paging file)

### 4. Storage & Filesystem Architecture
- **Drive Model**: **Micron 2450 NVMe 512GB** (PCIe Gen4 x4 M.2 SSD)
- **Drive Partition**: `C:\`
- **Filesystem**: NTFS (Cluster size: 4096 bytes)
- **Capacity**:
  - Total Volume: **453.18 GB**
  - Space Used: **361.01 GB** (79.7%)
  - Free Capacity: **92.17 GB**

### 5. Power & Thermal Posture
- **Power Subsystem**: AC Connected (Mains Wall Power)
- **Battery Status**: 100% capacity maintained
- **Thermal Policy**: Dell Performance Fan Profile active, GPU temp nominal (<48°C at idle).

---
## Related Notes
- [[05_System_State/Hardware_Topology|Hardware Topology]]
- [[05_System_State/Local_Inference_Topology|Local Inference Topology]]
- [[05_System_State/Network_and_Interfaces|Network & Interfaces]]
- [[01_Architecture/Local_Ollama_Inference_Substrate|Local Ollama Inference Substrate]]
