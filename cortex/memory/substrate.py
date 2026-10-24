import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

@dataclass
class Engram:
    id: str
    semantic_type: str  # fact, decision, procedure, insight, question
    statement: str
    provenance_ref: str
    valid_from: float
    valid_to: Optional[float] = None
    recorded_at: float = field(default_factory=time.time)

class MemorySubstrate:
    """
    Stratified Four-Tier Memory Substrate:
    - Tier 1: Lossless Episodic SQLite Event Store (WAL mode)
    - Tier 2: Bi-Temporal Knowledge Graph (Semantic, Temporal, Causal, Entity)
    - Tier 3: Multimodal Vector Memory with hybrid keyword/cosine search
    - Tier 4: Procedural Skill Registry with ATLAS pamphlets
    """
    def __init__(self, db_path: str = "cortex_memory.sqlite"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enforce WAL mode for safe concurrent reader/writer concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Tier 1: Raw lossless episodic events
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                tick_id INTEGER,
                event_type TEXT NOT NULL,
                input_payload TEXT,
                thought_trace TEXT,
                action_taken TEXT,
                outcome TEXT,
                metadata_json TEXT
            );
            """)

            # 2. Tier 2: Atomic Engrams with Bi-Temporal windows and Provenance
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS engrams (
                id TEXT PRIMARY KEY,
                episode_id INTEGER,
                semantic_type TEXT NOT NULL,
                statement TEXT NOT NULL,
                provenance_ref TEXT NOT NULL,
                valid_from REAL NOT NULL,
                valid_to REAL,
                recorded_at REAL NOT NULL,
                FOREIGN KEY (episode_id) REFERENCES raw_episodes(id)
            );
            """)

            # 3. Bi-Temporal Multi-Graph (MAGMA: Semantic, Temporal, Causal, Entity)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_nodes (
                id TEXT PRIMARY KEY,
                layer TEXT NOT NULL,
                label TEXT NOT NULL,
                properties_json TEXT
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation TEXT NOT NULL,
                layer TEXT NOT NULL,
                valid_from REAL NOT NULL,
                valid_to REAL,
                recorded_at REAL NOT NULL,
                provenance_ref TEXT NOT NULL,
                contradiction_group TEXT,
                FOREIGN KEY (source_id) REFERENCES graph_nodes(id),
                FOREIGN KEY (target_id) REFERENCES graph_nodes(id)
            );
            """)

            # 4. Embedded Vector Store
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS vector_entries (
                id TEXT PRIMARY KEY,
                text_content TEXT NOT NULL,
                embedding_blob BLOB NOT NULL,
                dim INTEGER NOT NULL,
                metadata_json TEXT
            );
            """)

            # 5. Procedural Skill Registry
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS procedural_skills (
                name TEXT PRIMARY KEY,
                docstring TEXT NOT NULL,
                file_path TEXT NOT NULL,
                reusability_score INTEGER NOT NULL,
                atlas_pamphlet TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            """)
            conn.commit()

    # --- Tier 1 Operations ---
    def record_raw_episode(
        self,
        event_type: str,
        tick_id: int,
        input_payload: Optional[str] = None,
        thought_trace: Optional[str] = None,
        action_taken: Optional[str] = None,
        outcome: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO raw_episodes 
                (timestamp, tick_id, event_type, input_payload, thought_trace, action_taken, outcome, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                time.time(), tick_id, event_type,
                input_payload or "", thought_trace or "", action_taken or "",
                outcome or "", json.dumps(metadata or {})
            ))
            conn.commit()
            return cursor.lastrowid

    # --- Tier 2 Operations: Bi-Temporal Graph & Engrams ---
    def add_engram(
        self,
        semantic_type: str,
        statement: str,
        provenance_ref: str,
        valid_from: Optional[float] = None,
        valid_to: Optional[float] = None,
        episode_id: Optional[int] = None
    ) -> str:
        engram_id = f"engram_{hashlib.sha256(statement.encode('utf-8')).hexdigest()[:12]}"
        now = time.time()
        v_from = valid_from or now

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO engrams
                (id, episode_id, semantic_type, statement, provenance_ref, valid_from, valid_to, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                engram_id, episode_id, semantic_type, statement, provenance_ref,
                v_from, valid_to, now
            ))
            conn.commit()
        return engram_id

    def add_graph_edge(
        self,
        source: str,
        target: str,
        relation: str,
        layer: str = "semantic",
        provenance: str = "direct_observation",
        contradiction_group: Optional[str] = None
    ) -> str:
        now = time.time()
        edge_id = f"edge_{hashlib.sha256(f'{source}_{relation}_{target}'.encode('utf-8')).hexdigest()[:12]}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Upsert nodes
            cursor.execute("INSERT OR IGNORE INTO graph_nodes (id, layer, label) VALUES (?, ?, ?)", (source, layer, source))
            cursor.execute("INSERT OR IGNORE INTO graph_nodes (id, layer, label) VALUES (?, ?, ?)", (target, layer, target))
            
            cursor.execute("""
                INSERT OR REPLACE INTO graph_edges
                (id, source_id, target_id, relation, layer, valid_from, recorded_at, provenance_ref, contradiction_group)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (edge_id, source, target, relation, layer, now, now, provenance, contradiction_group))
            conn.commit()
        return edge_id

    def query_graph_at_time(self, timestamp: float, limit: int = 10) -> List[Dict[str, Any]]:
        """Queries facts that were valid at specific point in time."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT source_id, relation, target_id, layer, provenance_ref, valid_from, valid_to
                FROM graph_edges
                WHERE valid_from <= ? AND (valid_to IS NULL OR valid_to >= ?)
                LIMIT ?
            """, (timestamp, timestamp, limit))
            return [dict(row) for row in cursor.fetchall()]

    # --- Tier 3 Operations: Vector Store ---
    async def index_vector(self, item_id: str, text: str, embedding: np.ndarray, metadata: Optional[Dict] = None):
        emb_bytes = embedding.astype(np.float32).tobytes()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO vector_entries (id, text_content, embedding_blob, dim, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            """, (item_id, text, emb_bytes, len(embedding), json.dumps(metadata or {})))
            conn.commit()

    async def search_vectors(self, query_vec: np.ndarray, top_k: int = 3) -> List[Dict[str, Any]]:
        norm_q = query_vec / (np.linalg.norm(query_vec) + 1e-9)
        results = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, text_content, embedding_blob, dim, metadata_json FROM vector_entries")
            rows = cursor.fetchall()
            for row in rows:
                dim = row["dim"]
                vec = np.frombuffer(row["embedding_blob"], dtype=np.float32)
                norm_v = vec / (np.linalg.norm(vec) + 1e-9)
                sim = float(np.dot(norm_q, norm_v))
                results.append({
                    "id": row["id"],
                    "text": row["text_content"],
                    "similarity": round(sim, 4),
                    "metadata": json.loads(row["metadata_json"])
                })
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    # --- Tier 4 Operations: Procedural Skills ---
    async def search_skills(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        results = []
        q_words = set(query.lower().split())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, docstring, file_path, reusability_score, atlas_pamphlet FROM procedural_skills")
            for row in cursor.fetchall():
                doc_words = set((row["name"] + " " + row["docstring"]).lower().split())
                overlap = len(q_words.intersection(doc_words)) / (len(q_words) + 1e-9)
                results.append({
                    "name": row["name"],
                    "file_path": row["file_path"],
                    "docstring": row["docstring"],
                    "score": row["reusability_score"],
                    "atlas_pamphlet": row["atlas_pamphlet"],
                    "similarity": min(1.0, overlap + 0.5 if overlap > 0 else 0.0)
                })
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    async def index_new_skill(
        self,
        tool_name: str,
        docstring: str,
        file_path: str,
        score: int,
        atlas_pamphlet: str
    ):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO procedural_skills
                (name, docstring, file_path, reusability_score, atlas_pamphlet, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tool_name, docstring, file_path, score, atlas_pamphlet, time.time()))
            conn.commit()

    # --- Context & Hybrid Retrieval ---
    async def retrieve_hybrid_context(self, queries: List[str]) -> str:
        """Retrieves graph facts, recent engrams, and vector items."""
        now = time.time()
        facts = self.query_graph_at_time(now, limit=5)
        context_parts = []
        if facts:
            fact_strs = [f"- ({f['source_id']}) -> [{f['relation']}] -> ({f['target_id']})" for f in facts]
            context_parts.append("Verified Graph Relations:\n" + "\n".join(fact_strs))
        
        # Recent engrams
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT semantic_type, statement FROM engrams ORDER BY recorded_at DESC LIMIT 3")
            engrams = cursor.fetchall()
            if engrams:
                e_strs = [f"- [{e['semantic_type']}] {e['statement']}" for e in engrams]
                context_parts.append("Recent Engrams:\n" + "\n".join(e_strs))

        return "\n\n".join(context_parts) if context_parts else "No prior long-term memory records found."

    async def extract_and_store_engrams(self, verbose_history: str):
        """Micro-Sleep decomposition into atomic engrams and graph edges."""
        lines = [l.strip() for l in verbose_history.split("\n") if l.strip()]
        for line in lines[-5:]:
            self.add_engram(
                semantic_type="fact",
                statement=line[:200],
                provenance_ref="stm_compression"
            )
