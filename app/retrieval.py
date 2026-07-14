# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer
from app.db import get_connection
from app.llm import translate_to_norwegian

_model = None

def get_embedding_model():
    # Load once, reuse — loading this on every request would be slow and wasteful.
    global _model
    if _model is None:
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model


def retrieve_chunks(question: str, top_k: int = 3):
    norwegian_query = translate_to_norwegian(question)
    model = get_embedding_model()
    query_embedding = model.encode(norwegian_query).tolist()

    conn = get_connection()
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