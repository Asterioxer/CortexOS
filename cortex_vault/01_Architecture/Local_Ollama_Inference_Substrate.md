# Local Ollama Inference Substrate

- **Service Endpoint**: `http://127.0.0.1:11434`
- **Component File**: [`cortex/inference/ollama_bridge.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/inference/ollama_bridge.py)
- **Status**: Live / Integrated / Zero-Cloud

## Purpose and Architectural Guarantees
The Local Ollama Inference Substrate provides CortexOS with an unmetered, privacy-preserving, 100% offline cognitive engine. It eliminates dependencies on external third-party APIs while providing deep technical ownership over the host operating system.

## Multi-Model Tier & Specialization
CortexOS dynamically interfaces with 4 local quantized models installed on Soham's machine:

| Model Identifier | Size (VRAM) | Parameter Class | Primary Cognitive Role |
| :--- | :--- | :--- | :--- |
| **`qwen2.5:3b`** | 1.80 GB | 3 Billion | **Default Fast Path**: Low-latency reactive reasoning, application launching, shell control, system state queries. |
| **`dolphinlabs/llama3.2-3b-uncensored:latest`** | 3.19 GB | 3.2 Billion | **Conversational & Empathic**: Unfiltered dialogue, psychological introspection, affective state reflection. |
| **`nandhank/qwen3.5-abliterated-truthful:9b`** | 6.14 GB | 9 Billion | **Heavyweight Deep Reasoning**: Algorithmic proofs, multi-file code synthesis, structural AST inspection. |
| **`gemma3:4b`** | 3.11 GB | 4 Billion | **Analytical & Structured**: Strict JSON schemas, mathematical validation, and data formatting. |

## Autonomous Action & Function Calling Protocol
Rather than acting as a passive chatbot, the local model operates as an active agent with real autonomy over Soham's laptop:
1. **Grounded Ingestion**: The system prompt injects live telemetry (Intel i5-12500H, RTX 3050, 24GB RAM, active window, active music, open apps) and retrieved RAG context from the Obsidian Vault.
2. **Action Intent Generation**: When an action is necessary, the model emits a structured JSON action block:
   ```json
   {
     "action": "launch_application",
     "parameters": {"target": "code"},
     "thought": "Opening VS Code on Soham's desktop."
   }
   ```
3. **Cedar Governance & Execution**: The action is routed to [[01_Architecture/Cedar_Security_Governance|Cedar Policy Engine]] and executed through [[cortex/embodiment/system_somatosensory.py|SystemSomatosensory]].
4. **Grounded Articulation**: The model receives real OS stdout/stderr/return values to formulate its final response to Soham.

---
## Related Notes
- [[05_System_State/Local_Inference_Topology]]
- [[01_Architecture/Global_Workspace_Theory]]
- [[04_Skills_Catalog/Trigger_Registry]]
- [[06_Self_Evolution/Autonomous_Evolution_Architecture]]
