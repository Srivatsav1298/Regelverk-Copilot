from app.embeddings import get_embedding
from app.db import get_connection
from app.llm import translate_to_norwegian

def retrieve_chunks(question: str, top_k: int = 3):
    norwegian_query = translate_to_norwegian(question)
    query_embedding = get_embedding(norwegian_query, input_type="search_query")

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