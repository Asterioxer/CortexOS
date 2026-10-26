---
title: "4-Tier Memory Substrate"
type: "architecture"
tags:
  - cortex/memory
  - cortex/wal
  - cortex/graph
  - cortex/working_memory
last_updated: "2026-10-26"
---

# 🧠 4-Tier Memory Substrate

CortexOS employs a multi-timescale memory hierarchy that bridges millisecond-level reactive context with permanent structural knowledge.

## Tier Overview

| Tier | Subsystem | Storage Medium | Characteristics |
|------|-----------|----------------|-----------------|
| **Tier 1** | Working Memory Blocks | JSON (`.cortex/working_memory_state.json`) | 4 in-context character-bounded self-editing blocks (Persona, Human, Workspace, STM). |
| **Tier 2** | Episodic WAL (Write-Ahead Log) | SQLite (`cortex_memory.sqlite`) | Append-only episodic traces with atomic engrams, tick IDs, timestamps, and causal parents. |
| **Tier 3** | Vector Retrieval & Semantic Memory | SQLite Vector / LanceDB | Dense text embeddings, cosine semantic similarity, and low-rank semantic clustering. |
| **Tier 4** | Bi-Temporal Knowledge Graph | Kùzu Graph DB (`kuzu_storage/`) | Bi-temporal entity-relation-entity graph with transaction-time and valid-time intervals. |

## 1. Working Memory (CoALA / Letta Architecture)
Working memory is partitioned into 4 persistent self-editing blocks:
1. `persona_self`: CortexOS core identity, first-person directives, calibrated restraint.
2. `human_profile`: Operator profile, preferences, current emotional tone (urgency score).
3. `workspace_state`: Real-time somatosensory hardware telemetry, focused application, media status.
4. `scratchpad_stm`: Short-term memory buffer, recent thoughts, reflexive action traces.

## 2. Episodic WAL & Consolidation
- Every cognitive tick logs an atomic engram to `cortex_memory.sqlite`.
- During idle periods on AC power, the `DigitalSleepPipeline` activates 4 consolidation stages:
  1. WAL Extraction of unconsolidated engrams.
  2. Bigram & entity extraction.
  3. Bi-temporal graph assertion.
  4. STM compression and working memory consolidation.

## 3. Bi-Temporal Kùzu Graph
- Nodes: Entities (Code, Modules, Hardware, People, Concepts).
- Edges: Typed relationships (`DEPENDS_ON`, `CALLS`, `MODIFIES`, `AUTHOR_OF`).
- Bi-temporal timestamps: `valid_from`, `valid_to`, `tx_from`, `tx_to`.
