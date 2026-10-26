---
title: "ADR-003: Obsidian Vault as Grounded Semantic RAG Substrate"
type: "adr"
tags:
  - cortex/adr
  - cortex/vault
  - cortex/rag
status: "accepted"
date: "2026-10-26"
---

# ADR-003: Obsidian Vault as Grounded Semantic RAG Substrate

## Context
As CortexOS expands, relying purely on raw LLM parametric memory risks hallucination regarding system architecture, active daemons, file paths, and operator preferences. The operator requested an Obsidian Vault to serve as the project's external knowledge base and RAG substrate, backed up to a dedicated private repository.

## Decision
1. **First-Class Obsidian Vault**:
   - Structured with `.obsidian` configurations, YAML frontmatter, wikilinks (`[[Link]]`), and nested categories.
2. **Hybrid RAG Engine (`VaultRAG`)**:
   - Combines lexical keyword token matching with TF-IDF dense semantic similarity and 1-hop wikilink graph traversal.
   - Automatically injected into the cognitive tick prompt (`<grounded_obsidian_vault_knowledge>`).
3. **Isolated Git Backup Sync (`VaultSync`)**:
   - Manages a detached Git database (`--git-dir=.cortex/vault_backup.git --work-tree=cortex_vault`) to back up the vault to a dedicated private repository without conflicting with the main project repository.

## Consequences
- Guaranteed zero hallucination on system capabilities, paths, and policies.
- Human-readable second brain that the operator can open and browse inside Obsidian directly.
