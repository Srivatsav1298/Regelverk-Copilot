"""Self-contained local hybrid storage engine for Regelverk Copilot.

Provides:
1. SQLite FTS5 BM25 full-text search with Norwegian-aware term handling.
2. Dense vector cosine similarity using numpy on normalized embeddings.
3. Reciprocal Rank Fusion (RRF) combining lexical and semantic retrieval.
4. Zero external cloud database dependency.
"""

import json
import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

logger = logging.getLogger("regelverk-copilot")

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "legal_corpus.db"


def get_db_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_storage():
    """Initializes the SQLite schema with relational and FTS5 virtual tables."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            provision TEXT NOT NULL,
            source_name TEXT NOT NULL,
            chunk_text TEXT NOT NULL,
            url TEXT,
            embedding BLOB,
            metadata_json TEXT
        );
    """)

    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            source_name,
            chunk_text,
            domain,
            provision,
            content='document_chunks',
            content_rowid='id'
        );
    """)

    # Triggers to keep FTS index synchronized
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON document_chunks BEGIN
            INSERT INTO chunks_fts(rowid, source_name, chunk_text, domain, provision)
            VALUES (new.id, new.source_name, new.chunk_text, new.domain, new.provision);
        END;
    """)

    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON document_chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, source_name, chunk_text, domain, provision)
            VALUES('delete', old.id, old.source_name, old.chunk_text, old.domain, old.provision);
        END;
    """)

    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON document_chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, source_name, chunk_text, domain, provision)
            VALUES('delete', old.id, old.source_name, old.chunk_text, old.domain, old.provision);
            INSERT INTO chunks_fts(rowid, source_name, chunk_text, domain, provision)
            VALUES (new.id, new.source_name, new.chunk_text, new.domain, new.provision);
        END;
    """)

    conn.commit()
    conn.close()


def insert_chunk(
    *,
    domain: str,
    provision: str,
    source_name: str,
    chunk_text: str,
    url: Optional[str] = None,
    embedding: Optional[List[float]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    conn = get_db_connection()
    cur = conn.cursor()

    embedding_blob = None
    if embedding is not None:
        arr = np.array(embedding, dtype=np.float32)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        embedding_blob = arr.tobytes()

    metadata_str = json.dumps(metadata or {}, ensure_ascii=False)

    cur.execute(
        """
        INSERT INTO document_chunks (domain, provision, source_name, chunk_text, url, embedding, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (domain, provision, source_name, chunk_text, url, embedding_blob, metadata_str),
    )
    chunk_id = cur.lastrowid
    conn.commit()
    conn.close()
    return chunk_id


def count_chunks() -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM document_chunks;")
    count = cur.fetchone()[0]
    conn.close()
    return count


STOPWORDS = {
    "hva", "er", "om", "på", "til", "av", "og", "for", "i", "en", "et", "den", "det", "som",
    "har", "jeg", "du", "vi", "han", "hun", "de", "kan", "må", "skal", "ved", "seg", "seg",
    "etter", "med", "fra", "inn", "ut", "hvor", "hvem", "hvilke", "hvilken", "hvilket",
    "what", "is", "the", "a", "an", "in", "on", "to", "for", "of", "and", "can", "i", "how",
    "do", "does", "are", "if", "with", "from", "at", "by", "this", "that"
}


def search_bm25(query: str, domain: Optional[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
    """Runs BM25 full-text search using FTS5 with stopword removal and phrase prioritization."""
    clean_query = "".join(c if c.isalnum() or c in "æøåÆØÅ§ " else " " for c in query)
    raw_tokens = [t.strip().lower() for t in clean_query.split() if len(t.strip()) > 1]
    
    # Filter stopwords unless all tokens would be removed
    content_tokens = [t for t in raw_tokens if t not in STOPWORDS]
    tokens = content_tokens if content_tokens else raw_tokens
    
    if not tokens:
        return []

    expanded_tokens = set(tokens)
    for t in tokens:
        if len(t) > 6:
            for suffix in ("møte", "møtet", "tid", "tiden", "beregning", "avtale", "krav", "periode", "rett"):
                if t.endswith(suffix) and len(t) - len(suffix) >= 4:
                    expanded_tokens.add(t[:-len(suffix)])
            expanded_tokens.add(t[:5])

    # Priority tokens: provisions or legal terms
    prov_tokens = [t for t in expanded_tokens if "§" in t or re.match(r"^\d+-\d+$", t)]
    
    # Construct FTS5 query: content tokens with prefix search
    token_clauses = [f'"{t}"*' for t in expanded_tokens if len(t) >= 3]
    fts_query = " OR ".join(token_clauses) if token_clauses else " OR ".join(f'"{t}"*' for t in tokens)
    if prov_tokens:
        # Boost specific provision search
        fts_query = f'("{prov_tokens[0]}"*) OR ({fts_query})'

    conn = get_db_connection()
    cur = conn.cursor()

    if domain and domain != "all":
        sql = """
            SELECT d.id, d.domain, d.provision, d.source_name, d.chunk_text, d.url, bm25(chunks_fts) as rank
            FROM chunks_fts f
            JOIN document_chunks d ON d.id = f.rowid
            WHERE chunks_fts MATCH ? AND d.domain = ?
            ORDER BY rank ASC
            LIMIT ?;
        """
        params = (fts_query, domain, top_k)
    else:
        sql = """
            SELECT d.id, d.domain, d.provision, d.source_name, d.chunk_text, d.url, bm25(chunks_fts) as rank
            FROM chunks_fts f
            JOIN document_chunks d ON d.id = f.rowid
            WHERE chunks_fts MATCH ?
            ORDER BY rank ASC
            LIMIT ?;
        """
        params = (fts_query, top_k)

    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "domain": r["domain"],
                "provision": r["provision"],
                "source_name": r["source_name"],
                "chunk_text": r["chunk_text"],
                "url": r["url"],
                "bm25_score": -float(r["rank"]),  # rank is negative in sqlite fts5, invert for higher=better
            })
        return results
    except Exception as exc:
        logger.warning("FTS search error (%s) on query %s", exc, fts_query)
        return []
    finally:
        conn.close()


def search_vector(query_embedding: List[float], domain: Optional[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
    """Calculates cosine similarity across stored chunk embeddings in memory using numpy."""
    conn = get_db_connection()
    cur = conn.cursor()

    if domain and domain != "all":
        cur.execute("SELECT id, domain, provision, source_name, chunk_text, url, embedding FROM document_chunks WHERE embedding IS NOT NULL AND domain = ?;", (domain,))
    else:
        cur.execute("SELECT id, domain, provision, source_name, chunk_text, url, embedding FROM document_chunks WHERE embedding IS NOT NULL;")

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return []

    q_arr = np.array(query_embedding, dtype=np.float32)
    q_norm = np.linalg.norm(q_arr)
    if q_norm > 0:
        q_arr = q_arr / q_norm

    scored = []
    for r in rows:
        c_bytes = r["embedding"]
        if not c_bytes:
            continue
        c_arr = np.frombuffer(c_bytes, dtype=np.float32)
        sim = float(np.dot(q_arr, c_arr))
        scored.append({
            "id": r["id"],
            "domain": r["domain"],
            "provision": r["provision"],
            "source_name": r["source_name"],
            "chunk_text": r["chunk_text"],
            "url": r["url"],
            "vector_score": sim,
            "distance": 1.0 - sim,
        })

    scored.sort(key=lambda x: x["vector_score"], reverse=True)
    return scored[:top_k]


def search_hybrid(
    query_text: str,
    query_embedding: Optional[List[float]] = None,
    domain: Optional[str] = None,
    top_k: int = 4,
    rrf_k: int = 60,
) -> List[Dict[str, Any]]:
    """Reciprocal Rank Fusion (RRF) combining BM25 and vector similarity rankings."""
    bm25_hits = search_bm25(query_text, domain=domain, top_k=top_k * 3)
    vector_hits = search_vector(query_embedding, domain=domain, top_k=top_k * 3) if query_embedding else []

    all_ids = set()
    hit_map = {}

    for rank, hit in enumerate(bm25_hits):
        cid = hit["id"]
        all_ids.add(cid)
        hit_map[cid] = hit
        hit["rrf_score"] = 1.0 / (rrf_k + rank + 1)

    for rank, hit in enumerate(vector_hits):
        cid = hit["id"]
        all_ids.add(cid)
        vec_score = 1.0 / (rrf_k + rank + 1)
        if cid in hit_map:
            hit_map[cid]["rrf_score"] = hit_map[cid].get("rrf_score", 0.0) + vec_score
            hit_map[cid]["vector_score"] = hit.get("vector_score")
            hit_map[cid]["distance"] = hit.get("distance", 0.5)
        else:
            hit_map[cid] = hit
            hit_map[cid]["rrf_score"] = vec_score

    combined = list(hit_map.values())
    combined.sort(key=lambda x: x.get("rrf_score", 0.0), reverse=True)

    results = []
    for hit in combined[:top_k]:
        distance = hit.get("distance")
        if distance is None:
            # Derived distance from rank
            distance = round(1.0 / (1.0 + hit.get("rrf_score", 0.1)), 4)
        results.append({
            "source_name": hit["source_name"],
            "chunk_text": hit["chunk_text"],
            "distance": float(distance),
            "domain": hit.get("domain", "termination"),
            "provision": hit.get("provision", ""),
            "url": hit.get("url"),
        })
    return results


def get_chunk_by_provision(provision: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT domain, provision, source_name, chunk_text, url FROM document_chunks WHERE provision = ? or source_name LIKE ? LIMIT 1;", (provision, f"%{provision}%"))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "source_name": row["source_name"],
            "chunk_text": row["chunk_text"],
            "distance": 0.0,
            "domain": row["domain"],
            "provision": row["provision"],
            "url": row["url"],
        }
    return None
