---
title: "Network Adapters & LAN Interfaces"
type: "network_interfaces"
tags:
  - cortex/system_state
  - cortex/network
  - cortex/lan
last_scanned: "2026-10-27 08:55:00"
status: "verified"
---

# 🌐 Network Adapters & LAN Interfaces

Ground-truth network topology, physical wireless adapters, virtual bridges, and socket routing for universal multi-device access across Soham's local network.

---

## 📡 Live Universal Gateways & Sockets

- **Active Host IPv4 Address**: `10.234.160.224`
- **Universal LAN Gateway**: `http://10.234.160.224:8000` *(Accessible from smartphones, tablets, and secondary machines on the same local subnet)*
- **Local Loopback**: `http://127.0.0.1:8000`
- **Full-Duplex Cognitive WebSocket**: `ws://10.234.160.224:8000/ws`
- **Local Neural Inference API**: `http://127.0.0.1:11434` (Ollama Server)

---

## 🔌 Hardware Network Adapters & Topology

### 1. Primary Wireless Interface (`Wi-Fi`)
- **Adapter Hardware**: Intel® Wi-Fi 6 AX201 160MHz (Gig+ 802.11ax, 2x2 MIMO)
- **Physical MAC Address**: `68-7A-64-ED-5E-4F`
- **Current Link Speed**: 144.4 Mbps (Dynamic rate adaptation)
- **IPv4 Address**: `10.234.160.224 / 24`
- **Operational Status**: `Up` (Default Route for all internet and LAN traffic)

### 2. VirtualBox Host-Only Virtual Adapter (`Ethernet 4`)
- **Virtual Adapter**: Oracle VirtualBox Host-Only Ethernet Adapter
- **Physical MAC Address**: `0A-00-27-00-00-08`
- **Link Speed**: 1 Gbps
- **IPv4 Address**: `192.168.56.1 / 24`
- **Role**: Host-to-guest networking for localized containerized VMs and security sandboxes.

### 3. Ancillary Interfaces
- **`Bluetooth Network Connection`**: PAN Adapter (`169.254.181.105` APIPA / Unpaired)
- **`Ethernet`**: Realtek Gigabit Ethernet Controller (`169.254.26.41` / Cable unplugged)
- **`Local Area Connection* 1 & 2`**: Microsoft Wi-Fi Direct Virtual Adapters for Miracast / Hotspot

---

## 🔒 Port Allocation Matrix

| Port | Protocol | Binding Address | Subsystem / Service |
| :--- | :--- | :--- | :--- |
| **`8000`** | TCP (HTTP/WS) | `0.0.0.0:8000` | **CortexOS Master Daemon & HUD Dashboard** (FastAPI / Uvicorn) |
| **`11434`** | TCP (HTTP) | `127.0.0.1:11434` | **Local Ollama Inference Engine** (CUDA Acceleration) |
| **`8080`** | TCP (HTTP) | `127.0.0.1:8080` | *Optional* `llama-server` (Qwen local streaming) |

---
## Related Notes
- [[05_System_State/System_Telemetry|Live Hardware Telemetry]]
- [[05_System_State/Hardware_Topology|Hardware Topology]]
- [[01_Architecture/Startup_Service_Daemon|Startup Service Daemon]]
