---
title: "Ollama Testing, LoRA Fine-Tuning & Custom LLM Workspace"
type: "workspace_catalog"
tags:
  - cortex/workspaces
  - cortex/ollama
  - cortex/lora
  - cortex/finetuning
  - cortex/rag
last_updated: "2026-10-27"
status: "verified"
---

# 🦙 Ollama Testing, LoRA Fine-Tuning & Custom LLM Workspace

- **Location**: `C:\Users\soham\Desktop\ollama_testing`
- **Domain**: Parameter-Efficient Fine-Tuning (PEFT / LoRA), Local RAG Pipelines, Tool-Calling Agents, Ollama Model Packaging
- **Primary Toolchains**: Python 3.12, PyTorch, HuggingFace Transformers, PEFT, TRL (SFTTrainer), ChromaDB, FastAPI, Vite / React

## 📂 Project Architecture

```
ollama_testing/
├── test.py                            # Basic Ollama API connectivity & latency test
└── custom_llm/
    ├── finetune.py                    # PEFT QLoRA fine-tuning script using HuggingFace TRL
    ├── Modelfile                      # Ollama model definition file importing base model & system prompt
    ├── training_data.jsonl            # Domain instruction-tuning dataset for Soham-style reasoning
    ├── soham-lora-adapter/            # Trained LoRA adapter checkpoint
    │   ├── adapter_config.json        # LoRA rank (r=8), alpha (16), target modules (q_proj, v_proj)
    │   ├── adapter_model.safetensors  # Saved low-rank tensor weights
    │   ├── chat_template.jinja        # Jinja2 chat template for conversation formatting
    │   └── tokenizer.json             # Full tokenizer vocabulary and merges
    ├── rag_chatbot.py                 # RAG chatbot leveraging ChromaDB vector store
    ├── tool_chatbot.py                # Autonomous function-calling chatbot with JSON schema parsing
    ├── router.py                      # Multi-agent model router (direct vs RAG vs tool invocation)
    ├── chroma_db/                     # Persistent ChromaDB SQLite vector store (`chroma.sqlite3`)
    ├── api/
    │   ├── server.py                  # FastAPI server exposing endpoints for chat, RAG, and tools
    │   └── tools.py                   # Local tool definitions (math, file inspection, weather/time)
    └── web/                           # Vite + React web interface for custom LLM interaction
```

---

## 🧬 Fine-Tuning Pipeline (`custom_llm/finetune.py`)

The fine-tuning pipeline implements Parameter-Efficient Fine-Tuning (PEFT) using Low-Rank Adaptation (LoRA):
- **Base Architecture**: Causal Language Model with 4-bit/8-bit quantization support.
- **LoRA Hyperparameters**:
  - Rank ($r$): `8` (low memory footprint, fast training).
  - Alpha ($\alpha$): `16` (scaling factor $\alpha/r = 2.0$).
  - Target Modules: `["q_proj", "v_proj"]` (query and value projection matrices in self-attention layers).
  - Dropout: `0.05`.
  - Task Type: `CAUSAL_LM`.
- **Training Harness**: Supervised Fine-Tuning (`SFTTrainer` from HuggingFace TRL) on structured instruction pairs formatted via `format_instruction(sample)`.

---

## 🔍 Retrieval & Function Calling Subsystems

1. **Vector RAG (`custom_llm/rag_chatbot.py`)**:
   - Embeds sample knowledge documents (`sample_data.txt`) into a local persistent ChromaDB instance (`chroma_db/chroma.sqlite3`).
   - Retrieves top-$k$ nearest context passages via cosine similarity to augment user prompts without cloud dependencies.
2. **Tool-Calling Agent (`custom_llm/tool_chatbot.py`)**:
   - Implements structured JSON tool calling, extracting parameters to invoke local functions in `api/tools.py` and synthesizing final replies.
3. **Model Router (`custom_llm/router.py`)**:
   - Classifies incoming queries based on semantic intent to decide whether direct generation, vector retrieval, or tool execution is needed.

---

## ⚡ Integration with CortexOS
CortexOS's local inference bridge ([`cortex/inference/ollama_bridge.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/inference/ollama_bridge.py)) leverages the exact models tested and benchmarked here (`qwen2.5:3b`, `qwen2.5:7b`, `llama3.2:3b`). The PEFT LoRA architecture also provides the structural template for CortexOS's planned autonomous self-tuning adapters.

---
## Related Notes
- [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]]
- [[01_Architecture/Local_Ollama_Inference_Substrate|Local Ollama Inference Substrate]]
- [[05_System_State/Local_Inference_Topology|Local Inference Topology]]
- [[07_Workspace_Index/Local_LLM_Streaming_Qwen|Local LLM Streaming Qwen]]
- [[06_Self_Evolution/Autonomous_Evolution_Architecture|Autonomous Evolution Architecture]]
