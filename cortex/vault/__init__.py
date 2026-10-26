"""CortexOS Obsidian Knowledge Vault, Grounded RAG & Pair Copilot Module.

Provides:
  - ObsidianVault: Second-brain knowledge graph management with wikilinks and frontmatter.
  - VaultRAG: Anti-hallucination hybrid semantic & lexical retrieval over vault notes.
  - VaultSync: Isolated Git backup and private repository sync.
  - PairCopilot: Real-time autonomous pair programming execution assistant.
"""

from cortex.vault.vault_manager import ObsidianVault, get_vault
from cortex.vault.rag_engine import VaultRAG, get_vault_rag
from cortex.vault.git_sync import VaultSync, get_vault_sync
from cortex.vault.copilot_pair import PairCopilot, get_pair_copilot

__all__ = [
    "ObsidianVault",
    "VaultRAG",
    "VaultSync",
    "PairCopilot",
    "get_vault",
    "get_vault_rag",
    "get_vault_sync",
    "get_pair_copilot",
]
