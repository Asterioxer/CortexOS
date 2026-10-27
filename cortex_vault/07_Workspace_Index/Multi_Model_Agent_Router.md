---
title: "Multi-Model Agent Router Workspace"
type: "workspace_catalog"
tags:
  - cortex/workspaces
  - cortex/agents
  - cortex/model_router
  - cortex/gemini
  - cortex/ollama
last_updated: "2026-10-27"
status: "verified"
---

# 🔀 Multi-Model Agent Router Workspace

- **Location**: `C:\Users\soham\Desktop\Agent`
- **Domain**: Dynamic LLM Provider Routing, Local/Cloud Hybrid Architecture, Automated Failover
- **Primary Toolchains**: Python 3.12, Google Generative AI (Gemini), OpenRouter API, Ollama (Local)

## 🏗️ Architecture & Component Design

The project provides an extensible multi-provider router ([`models/router.py`](file:///c:/Users/soham/Desktop/Agent/models/router.py)) that decouples client prompts from specific LLM vendors:

```
                      [Operator / Client Prompt]
                                  │
                                  ▼
                        ┌───────────────────┐
                        │    ModelRouter    │
                        └───────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│ LocalProvider │         │ GeminiProvider│         │ OpenRouter    │
│  (Ollama)     │         │  (Google)     │         │  (Provider)   │
└───────────────┘         └───────────────┘         └───────────────┘
  ├── coder: qwen2.5:7b     └── gemini-pro            └── openrouter/auto
  └── reasoner: llama3
```

---

## 🛠️ Key Provider Implementations

| Provider | Module Path | Model Target & Failover Strategy |
|---|---|---|
| **`LocalProvider`** | [`providers/local_provider.py`](file:///c:/Users/soham/Desktop/Agent/providers/local_provider.py) | Communicates with local Ollama daemon (`http://127.0.0.1:11434`). Maps `"coder"` role to `qwen2.5:7b` and `"reasoner"` role to `llama3:latest`. |
| **`GeminiProvider`** | [`providers/gemini_provider.py`](file:///c:/Users/soham/Desktop/Agent/providers/gemini_provider.py) | Connects to Google Generative AI API using `GEMINI_API_KEY`. Provides fast cloud reasoning when local VRAM is constrained. |
| **`OpenRouterProvider`**| [`providers/openrouter_provider.py`](file:///c:/Users/soham/Desktop/Agent/providers/openrouter_provider.py) | Bridges through OpenRouter gateway (`openrouter/auto`), providing dynamic fallback to Claude, Mistral, or Llama models. |

---

## 🔗 Convergence with CortexOS
CortexOS's internal cognitive substrate ([`cortex/inference/ollama_bridge.py`](file:///c:/Users/soham/Desktop/self-conscious/cortex/inference/ollama_bridge.py)) directly implements this local-first zero-cloud philosophy, defaulting to local Ollama on the RTX 3050 GPU while maintaining architectural compatibility with cloud bridges.

---
## Related Notes
- [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]]
- [[01_Architecture/Local_Ollama_Inference_Substrate|Local Ollama Inference Substrate]]
- [[05_System_State/Local_Inference_Topology|Local Inference Topology]]
- [[07_Workspace_Index/Ollama_Testing_and_FineTuning|Ollama Testing & Fine-Tuning]]
