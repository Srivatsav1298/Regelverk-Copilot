from app.embeddings import get_embedding
from app.db import get_connection
from app.llm import translate_to_norwegian
from pathlib import Path
import re


def _lexical_fallback(question: str, top_k: int):
    blocks = _local_blocks()
    query_terms = set(re.findall(r"[\wæøå]+", question.lower()))
    scored = []
    for block in blocks:
        if "### SOURCE:" not in block:
            continue
        lines = block.strip().splitlines()
        source = lines[0].replace("### SOURCE:", "").strip()
        body = " ".join(lines[1:]).strip()
        terms = set(re.findall(r"[\wæøå]+", body.lower()))
        score = len(query_terms & terms)
        scored.append((score, source, body))
    scored.sort(reverse=True)
    return [{"source_name": source, "chunk_text": body, "distance": 1.0 / (1 + score)} for score, source, body in scored[:top_k]]


def _local_blocks():
    corpus_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "termination_law.txt"
    text = corpus_path.read_text(encoding="utf-8")
    return re.split(r"(?=### SOURCE:)", text)


def get_local_source(provision: str):
    """Return an exact local source even when vector retrieval is unavailable or mis-ranked."""
    for block in _local_blocks():
        if f"{provision} |" not in block:
            continue
        lines = block.strip().splitlines()
        return {"source_name": lines[0].replace("### SOURCE:", "").strip(), "chunk_text": " ".join(lines[1:]).strip(), "distance": 0.0}
    return None

def retrieve_chunks(question: str, top_k: int = 3):
    norwegian_query = translate_to_norwegian(question)
    try:
        query_embedding = get_embedding(norwegian_query, input_type="search_query")
    except Exception:
        return _lexical_fallback(f"{question} {norwegian_query}", top_k)

    try:
        conn = get_connection()
    except Exception:
        return _lexical_fallback(f"{question} {norwegian_query}", top_k)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source_name, chunk_text, embedding <=> %s::vector AS distance
        FROM document_chunks
        ORDER BY distance ASC
        LIMIT %s;
        """,
        (query_embedding, top_k),
    )
    results = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {"source_name": r[0], "chunk_text": r[1], "distance": float(r[2])}
        for r in results
    ]
