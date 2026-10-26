# Local LLM Streaming (Qwen 3.6 / Llama.cpp) Workspace

- **Location**: `C:\Users\soham\Desktop\qwen3.6-setup-streaming`
- **Domain**: Quantized Local LLM Inference, Low-Latency Streaming, CUDA GPU Offloading
- **Primary Toolchains**: `llama.cpp` (`llama-server`, `llama-cli`), PowerShell/Batch automation scripts, HuggingFace GGUF models
- **Hardware Target**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM) + 24 GB Host RAM

## Key Artifacts & Automation Scripts
- `check_system.bat` / `check_system.ps1`: Probes host GPU VRAM availability, CUDA driver status, and thermal headroom prior to model loading.
- `llama-server.bat`: Spawns a local OpenAI-compatible inference server running on `http://127.0.0.1:8080` with continuous batching and flash attention enabled.
- `llama-cli.bat` / `llama-cli.ps1`: Interactive terminal streaming shell for direct CLI conversation with the quantized Qwen model.

## Operational Parameters for 4GB RTX 3050
Because the laptop GPU possesses 4,096 MB VRAM, optimal inference configurations utilize:
- **Quantization**: Q4_K_M or Q5_K_M 4-bit/5-bit quantization to fit the model weights (~2.2 GB - 3.1 GB) directly into VRAM.
- **Offload Layers (`-ngl`)**: 24 to 28 layers offloaded to CUDA, leaving remaining layers to CPU with AVX2 acceleration.
- **Context Window (`-c`)**: 4096 tokens with KV cache quantization (`-ctk q8_0`, `-ctv q8_0`) to preserve VRAM during extended multi-turn prompts.

## Integration with CortexOS
CortexOS's cognitive reasoning pipeline can consume this local streaming server as an unmetered, zero-cloud offline fallback for the Analytical perspective in the Global Workspace.

---
## Related Notes
- [[Hardware_Topology]]
- [[Global_Workspace_Theory]]
- [[Filesystem_and_Workspaces]]
