---
title: "DeepThought Culture Multi-Agent Intelligence Workspace"
type: "workspace_catalog"
tags:
  - cortex/workspaces
  - cortex/langgraph
  - cortex/multi_agent
  - cortex/b2b_discovery
  - cortex/scraping
last_updated: "2026-10-27"
status: "verified"
---

# 🌐 DeepThought Culture Multi-Agent Intelligence Workspace

- **Location**: `C:\Users\soham\Desktop\deepthought_culture`
- **Domain**: Autonomous Multi-Agent B2B Discovery, Lead Scoring, Web Scraping & Enterprise Proposal Generation
- **Framework**: LangGraph, Python 3.12, BeautifulSoup / Playwright Scraper, Multi-Provider LLM Engine
- **Supported Providers**: Google Gemini, Groq (Llama-3-70B), Ollama (Local), OpenRouter

## 🔄 LangGraph Cyclic Workflow (`src/graph.py`)

The pipeline models a complex cyclical graph of specialized autonomous agents:

```
[Target ICP Parameters]
          │
          ▼
   ┌──────────────┐
   │  Discovery   │ ──► Searches web & company directories for prospect organizations
   └──────────────┘
          │
          ▼
   ┌──────────────┐
   │ Eligibility  │ ──► Filters out non-compliant or sub-scale candidates
   └──────────────┘
          │
          ▼
   ┌──────────────┐
   │   Research   │ ──► Scrapes corporate websites, executive bios, & recent initiatives
   └──────────────┘
          │
          ▼
   ┌──────────────┐
   │   Scoring    │ ──► Computes multi-attribute ICP fit score (0.0 to 1.0)
   └──────────────┘
          │
          ▼
   ┌──────────────┐
   │  Validation  │ ──► Cross-checks claims to eliminate hallucinated contacts/revenue
   └──────────────┘
          │
          ├── [Score >= Threshold] ──► ┌──────────────┐
          │                            │   Outreach   │ ──► Generates custom proposals
          └── [Score < Threshold]      └──────────────┘
                   │
                   ▼
             [Drop / Log]
```

---

## 🛠️ Specialized Subsystems & Providers

| Subsystem | File Path | Functionality |
|---|---|---|
| **Graph Controller** | [`src/graph.py`](file:///c:/Users/soham/Desktop/deepthought_culture/src/graph.py) | Compiles the LangGraph `StateGraph` with conditional routing between research and validation. |
| **Shared State Schema** | [`src/state.py`](file:///c:/Users/soham/Desktop/deepthought_culture/src/state.py) | Defines `AgentState` TypedDict holding company profiles, scrape artifacts, scores, and logs. |
| **Provider Factory** | [`src/providers/factory.py`](file:///c:/Users/soham/Desktop/deepthought_culture/src/providers/factory.py) | Dynamic instantiation of LLM backends (Gemini 1.5 Pro, Groq, Ollama, OpenRouter). |
| **Web Scraper** | [`src/utils/scraper.py`](file:///c:/Users/soham/Desktop/deepthought_culture/src/utils/scraper.py) | Robust DOM extraction, robots.txt parsing, rate limiting, and markdown conversion. |
| **Exporter** | [`src/utils/export.py`](file:///c:/Users/soham/Desktop/deepthought_culture/src/utils/export.py) | Serializes validated prospect batches into CSV (`sample-output.csv`) and markdown proposals (`sample-proposal-1000-companies.md`). |

---

## 🔗 Architectural Synergies with CortexOS
The provider abstraction layer (`src/providers/`) and defensive scraping utilities provide valuable blueprints for CortexOS's external telemetry gathering and multi-model failover mechanisms.

---
## Related Notes
- [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]]
- [[07_Workspace_Index/Agentic_AI_and_Governance_Research|Agentic AI & Governance Research]]
- [[01_Architecture/Local_Ollama_Inference_Substrate|Local Ollama Inference Substrate]]
- [[05_System_State/Filesystem_and_Workspaces|Filesystem and Workspaces]]
