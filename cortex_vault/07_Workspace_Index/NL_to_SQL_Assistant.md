---
title: "NL-to-SQL Assistant & Guardrailed Agent Workspace"
type: "workspace_catalog"
tags:
  - cortex/workspaces
  - cortex/nlp
  - cortex/sql
  - cortex/agents
  - cortex/evals
last_updated: "2026-10-27"
status: "verified"
---

# 🗄️ NL-to-SQL Assistant & Guardrailed Agent Workspace

- **Location**: `C:\Users\soham\Desktop\nl-to-sql-assistant`
- **Domain**: Schema-Aware Natural Language to SQL Generation, AST Guardrails, Multi-Model Evaluation
- **Primary Toolchains**: Python 3.12, FastAPI, LangChain, sqlglot, SQLite, Ollama (Local LLMs), OpenAI API, pytest

## 🏗️ Architecture & Component Breakdown

```
nl-to-sql-assistant/
├── src/
│   ├── agent.py               # Main ReAct / multi-turn conversational SQL agent
│   ├── tool_agent.py          # Tool-calling agent with iterative error correction
│   ├── api.py                 # Production FastAPI HTTP backend with rate limiting & timeouts
│   ├── database.py            # SQLite connection pool, query execution, & row-limiting
│   ├── sql_validator.py       # AST validator using sqlglot (read-only enforcement & DML blocking)
│   ├── schema_retriever.py    # Schema embedding & retrieval for dynamic schema pruning
│   ├── schema_metadata.py     # Schema dictionary for tables, columns, foreign keys, & business logic
│   ├── blog_schema.py         # Blog database schema definition
│   ├── saas_schema.py         # Multi-tenant SaaS database schema definition
│   ├── query_log.py           # Structured JSONL query audit logging (`logs/query_log.jsonl`)
│   ├── codegen.py             # Python script generator from validated SQL workflows
│   └── llm.py                 # Multi-backend LLM abstraction (Ollama local / OpenAI cloud)
├── data/
│   ├── ecommerce.db           # Seeded E-commerce relational database
│   ├── blog.db                # Articles, authors, comments, & readership telemetry
│   ├── saas.db                # Multi-tenant SaaS subscriptions, MRR, & user seats
│   ├── seed_db.py             # Synthetic data generator for ecommerce.db
│   ├── seed_blog_db.py        # Synthetic data generator for blog.db
│   └── seed_saas_db.py        # Synthetic data generator for saas.db
├── eval/
│   ├── compare_models.py      # Cross-model evaluation harness
│   ├── full_eval_qwen2.5_7b.md # Empirical benchmark log on 18 test queries
│   └── codegen_output_*.py    # Automated code generation outputs per model
└── tests/
    ├── test_api.py            # HTTP API endpoint tests
    ├── test_guardrails.py     # Security guardrail tests (blocking DROP, ALTER, UPDATE, injection)
    ├── ground_truth.py        # Gold-standard reference SQL queries
    └── run_eval.py            # Batch accuracy test runner
```

---

## 🛡️ AST Security Guardrails & Sandboxing

The system implements strict defensive guardrails in [`src/sql_validator.py`](file:///c:/Users/soham/Desktop/nl-to-sql-assistant/src/sql_validator.py):
1. **Read-Only Enforcement**: Uses `sqlglot` to parse generated SQL into an Abstract Syntax Tree (AST). Rejects any query containing `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, or `GRANT`.
2. **Execution Timeouts & Row Limits**: Wraps SQLite executions in a strict 5.0-second hardware timeout and enforces `LIMIT 100` if the generated query lacks an explicit bound.
3. **Schema Grounding**: Prevents hallucinated table names by validating all referenced AST table and column tokens against the active database catalog.

---

## 📊 Multi-Model Accuracy Benchmark

In `eval/compare_models.py`, Soham evaluated 4 models on a standardized battery of 18 analytical SQL queries (aggregations, multi-table JOINs, subqueries, date math):

| Model Evaluated | Backend | Syntax Pass Rate | Semantic Accuracy | Key Strengths / Bottlenecks |
|---|---|---|---|---|
| **`qwen2.5-coder:7b`** | Ollama (Local) | 94.4% | 88.9% | Strongest local SQL generation; accurate JOIN condition selection. |
| **`qwen2.5:7b`** | Ollama (Local) | 77.8% | 55.6% | Good natural language reasoning; occasional hallucinations on ambiguous metrics. |
| **`deepseek-coder-v2-small`** | Ollama (Local) | 83.3% | 72.2% | Excellent CTE generation; slightly slower inference on 4GB VRAM. |
| **`gemma3:4b`** | Ollama (Local) | 66.7% | 44.4% | Lightweight and fast, but struggles with nested subqueries and date arithmetic. |

---

## 🔗 Convergence with CortexOS
The guardrail and AST validation patterns from `nl-to-sql-assistant` mirror the [[01_Architecture/Governance_Cedar|Cedar Governance]] architecture inside CortexOS. CortexOS can also leverage this assistant as an internal skill to query local SQLite episodic memory databases (`cortex_memory.sqlite`).

---
## Related Notes
- [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]]
- [[01_Architecture/Governance_Cedar|Cedar Security Governance]]
- [[01_Architecture/Local_Ollama_Inference_Substrate|Local Ollama Inference Substrate]]
- [[05_System_State/Filesystem_and_Workspaces|Filesystem and Workspaces]]
- [[04_Skills_Catalog/Skills_Registry|Skills Registry]]
