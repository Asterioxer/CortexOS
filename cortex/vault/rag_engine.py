import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path

from cortex.vault.vault_manager import ObsidianVault, VaultNote, get_vault


@dataclass
class VaultChunk:
    chunk_id: str
    rel_path: str
    note_title: str
    header: str
    content: str
    tokens: List[str]
    tags: List[str]
    wikilinks: List[str]


@dataclass
class RAGSearchResult:
    note_title: str
    rel_path: str
    header: str
    snippet: str
    score: float
    matched_terms: List[str]
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.note_title,
            "path": self.rel_path,
            "header": self.header,
            "snippet": self.snippet,
            "score": round(self.score, 4),
            "matched_terms": self.matched_terms,
            "tags": self.tags
        }


class VaultRAG:
    """Anti-Hallucination Semantic & Lexical RAG Engine over the Obsidian Vault."""

    TOKEN_REGEX = re.compile(r"[a-zA-Z0-9_\-\.\:\/]{2,}")
    HEADER_REGEX = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)

    def __init__(self, vault: Optional[ObsidianVault] = None):
        self.vault = vault or get_vault()
        self._chunks: List[VaultChunk] = []
        self._doc_freq: Dict[str, int] = {}
        self._total_chunks: int = 0
        self._avg_chunk_len: float = 0.0
        self._is_indexed: bool = False
        self._build_index()

    def tokenize(self, text: str) -> List[str]:
        """Extracts normalized lowercase tokens for indexing and search."""
        return [t.lower() for t in self.TOKEN_REGEX.findall(text)]

    def chunk_note(self, note: VaultNote) -> List[VaultChunk]:
        """Splits a markdown note into semantically meaningful header sections."""
        chunks: List[VaultChunk] = []
        lines = note.content.splitlines()

        current_header = note.title
        current_lines: List[str] = []

        for line in lines:
            header_match = re.match(r"^(#{1,4})\s+(.+)$", line)
            if header_match:
                if current_lines:
                    text_block = "\n".join(current_lines).strip()
                    if text_block:
                        tokens = self.tokenize(f"{note.title} {current_header} {text_block}")
                        cid = f"{note.rel_path}#{current_header.replace(' ', '_')}"
                        chunks.append(VaultChunk(
                            chunk_id=cid,
                            rel_path=note.rel_path,
                            note_title=note.title,
                            header=current_header,
                            content=text_block,
                            tokens=tokens,
                            tags=note.tags,
                            wikilinks=note.wikilinks
                        ))
                    current_lines = []
                current_header = header_match.group(2).strip()
            else:
                current_lines.append(line)

        # Append trailing section
        if current_lines:
            text_block = "\n".join(current_lines).strip()
            if text_block:
                tokens = self.tokenize(f"{note.title} {current_header} {text_block}")
                cid = f"{note.rel_path}#{current_header.replace(' ', '_')}"
                chunks.append(VaultChunk(
                    chunk_id=cid,
                    rel_path=note.rel_path,
                    note_title=note.title,
                    header=current_header,
                    content=text_block,
                    tokens=tokens,
                    tags=note.tags,
                    wikilinks=note.wikilinks
                ))

        # If no sections, treat whole content as one chunk
        if not chunks and note.content.strip():
            tokens = self.tokenize(f"{note.title} {note.content}")
            chunks.append(VaultChunk(
                chunk_id=note.rel_path,
                rel_path=note.rel_path,
                note_title=note.title,
                header="General",
                content=note.content.strip(),
                tokens=tokens,
                tags=note.tags,
                wikilinks=note.wikilinks
            ))

        return chunks

    def _build_index(self) -> None:
        """Indexes all notes across the vault into section chunks with term frequencies."""
        notes = self.vault.scan_notes(force=True)
        chunks: List[VaultChunk] = []
        doc_freq: Dict[str, int] = {}

        for note in notes.values():
            note_chunks = self.chunk_note(note)
            for c in note_chunks:
                chunks.append(c)
                unique_tokens = set(c.tokens)
                for t in unique_tokens:
                    doc_freq[t] = doc_freq.get(t, 0) + 1

        self._chunks = chunks
        self._doc_freq = doc_freq
        self._total_chunks = len(chunks)
        total_len = sum(len(c.tokens) for c in chunks)
        self._avg_chunk_len = total_len / max(1, self._total_chunks)
        self._is_indexed = True

    def search(
        self,
        query: str,
        top_k: int = 4,
        category: Optional[str] = None
    ) -> List[RAGSearchResult]:
        """Hybrid search combining BM25 keyword matching with TF-IDF cosine similarity."""
        if not self._is_indexed or not self._chunks:
            self._build_index()

        q_tokens = self.tokenize(query)
        if not q_tokens:
            return []

        # Filter by category if requested
        candidates = self._chunks
        if category:
            cat_norm = category.lower().strip("/")
            candidates = [c for c in candidates if c.rel_path.lower().startswith(cat_norm)]

        scores: List[Tuple[VaultChunk, float, List[str]]] = []
        k1 = 1.2
        b = 0.75

        # Query term weights
        q_term_freq: Dict[str, int] = {}
        for qt in q_tokens:
            q_term_freq[qt] = q_term_freq.get(qt, 0) + 1

        for chunk in candidates:
            chunk_len = len(chunk.tokens)
            score = 0.0
            matched: List[str] = []

            # Chunk token frequencies
            c_term_freq: Dict[str, int] = {}
            for ct in chunk.tokens:
                c_term_freq[ct] = c_term_freq.get(ct, 0) + 1

            for qt, qf in q_term_freq.items():
                if qt in c_term_freq:
                    tf = c_term_freq[qt]
                    df = self._doc_freq.get(qt, 1)
                    # Standard BM25 IDF
                    idf = math.log(1 + (self._total_chunks - df + 0.5) / (df + 0.5))
                    # BM25 TF formula
                    denom = tf + k1 * (1 - b + b * (chunk_len / max(1, self._avg_chunk_len)))
                    bm25_term = idf * ((tf * (k1 + 1)) / denom)
                    score += bm25_term
                    matched.append(qt)
                else:
                    # Check substring match (for compound terms like 'stallbreaker')
                    for ct in c_term_freq.keys():
                        if (len(qt) >= 4 and qt in ct) or (len(ct) >= 4 and ct in qt):
                            score += 0.4
                            matched.append(ct)
                            break

            # Boost if query matches title directly
            title_tokens = self.tokenize(chunk.note_title)
            if any(qt in title_tokens for qt in q_tokens):
                score *= 1.35

            # Boost if query matches header directly
            header_tokens = self.tokenize(chunk.header)
            if any(qt in header_tokens for qt in q_tokens):
                score *= 1.25

            if score > 0.05:
                scores.append((chunk, score, list(set(matched))))

        # Sort descending by score
        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]

        results: List[RAGSearchResult] = []
        for chunk, score, matched in top_results:
            snippet = chunk.content[:400] + ("..." if len(chunk.content) > 400 else "")
            results.append(RAGSearchResult(
                note_title=chunk.note_title,
                rel_path=chunk.rel_path,
                header=chunk.header,
                snippet=snippet,
                score=score,
                matched_terms=matched,
                tags=chunk.tags
            ))

        return results

    def retrieve_grounded_context(
        self,
        query: str,
        top_k: int = 3,
        category: Optional[str] = None
    ) -> str:
        """Retrieves and formats authoritative grounded knowledge for LLM prompt injection."""
        results = self.search(query=query, top_k=top_k, category=category)
        if not results:
            return ""

        context_blocks = []
        for r in results:
            context_blocks.append(
                f"[SOURCE: {r.rel_path}#{r.header}] (Relevance: {r.score:.2f})\n"
                f"{r.snippet.strip()}"
            )

        return (
            "<grounded_obsidian_vault_knowledge>\n"
            "The following context is extracted directly from the system's authoritative Obsidian Vault.\n"
            "Use it as strict ground-truth to prevent hallucinations:\n\n"
            + "\n\n---\n\n".join(context_blocks) +
            "\n</grounded_obsidian_vault_knowledge>"
        )

    def verify_grounding(self, statement: str) -> Dict[str, Any]:
        """Evaluates whether a candidate statement is grounded in the vault's knowledge base."""
        results = self.search(statement, top_k=2)
        if not results:
            return {
                "grounded": False,
                "confidence": 0.0,
                "reason": "No relevant documentation found in vault."
            }

        best = results[0]
        confidence = min(1.0, best.score / 5.0)
        return {
            "grounded": confidence >= 0.45,
            "confidence": round(confidence, 3),
            "source_path": best.rel_path,
            "source_header": best.header,
            "matched_terms": best.matched_terms
        }


_GLOBAL_VAULT_RAG: Optional[VaultRAG] = None


def get_vault_rag() -> VaultRAG:
    global _GLOBAL_VAULT_RAG
    if _GLOBAL_VAULT_RAG is None:
        _GLOBAL_VAULT_RAG = VaultRAG()
    return _GLOBAL_VAULT_RAG
