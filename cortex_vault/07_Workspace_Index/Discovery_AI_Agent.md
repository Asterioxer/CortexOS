---
title: "Discovery AI Agent (CrewAI Academic Researcher) Workspace"
type: "workspace_catalog"
tags:
  - cortex/workspaces
  - cortex/crewai
  - cortex/multi_agent
  - cortex/arxiv
  - cortex/research
last_updated: "2026-10-27"
status: "verified"
---

# 🛰️ Discovery AI Agent (CrewAI Academic Researcher) Workspace

- **Location**: `C:\Users\soham\Desktop\Discovery_AI_Agent`
- **Domain**: Multi-Agent Academic Paper Discovery, Synthesis & Literature Analysis
- **Framework**: CrewAI, FastAPI, Vite / React, arXiv API, Ollama Local Inference
- **Target Models**: `qwen2.5:7b` (Scout & Analyst), `llama3:latest` (Synthesizer & Visionary)

## 🏗️ Multi-Agent Architecture (`backend/agents.py`)

The system orchestrates a 4-agent collaborative crew using CrewAI:

```
[User Research Topic]
         │
         ▼
 1. Academic Scout (LLM: qwen2.5:7b)
    └── Tool: search_arxiv_tool (Queries arXiv API for latest CS papers)
         │
         ▼
 2. Deep Analyst (LLM: qwen2.5:7b)
    └── Tool: pdf_processor.py (Parses abstracts, methodologies, & benchmarks)
         │
         ▼
 3. Synthesizer (LLM: llama3:latest)
    └── Aggregates findings, resolves contradictions, & drafts structured executive report
         │
         ▼
 4. Visionary (LLM: llama3:latest)
    └── Derives open challenges, unresolved hypotheses, & future research trajectories
```

---

## 🛠️ Components & File Layout

| Path | Purpose & Function |
|---|---|
| **`backend/main.py`** | FastAPI server exposing asynchronous `/api/research` endpoint and WebSocket stream for live crew progress. |
| **`backend/agents.py`** | CrewAI agent declarations, roles, backstories, LLM initializers, and sequential process pipeline. |
| **`backend/tools/arxiv_tool.py`** | Automated query wrapper querying arXiv's search API and returning structured metadata (title, authors, summary, PDF URL). |
| **`backend/utils/pdf_processor.py`** | Extracts and cleans text sections from retrieved preprint PDFs for deep analytical ingestion. |
| **`frontend/src/components/ResearchForm.jsx`** | React research input form with real-time status indicators and Markdown preview for the generated literature report. |

---

## 🔗 Connection to CortexOS
The 4-perspective crew model (Scout, Analyst, Synthesizer, Visionary) is directly analogous to the tri-perspective cognitive arbitration loop inside CortexOS ([[01_Architecture/Global_Workspace_Theory|Global Workspace Theory]]). CortexOS can invoke this crew as an autonomous subagent when tasked with deep academic literature surveys.

---
## Related Notes
- [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]]
- [[07_Workspace_Index/Agentic_AI_and_Governance_Research|Agentic AI & Governance Research]]
- [[01_Architecture/Global_Workspace_Theory|Global Workspace Theory]]
- [[01_Architecture/Local_Ollama_Inference_Substrate|Local Ollama Inference Substrate]]
- [[05_System_State/Filesystem_and_Workspaces|Filesystem and Workspaces]]
