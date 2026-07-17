import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.embeddings import get_embedding
from app.db import get_connection
from app.llm import translate_to_norwegian

def search(query, top_k=6):
    norwegian_query = translate_to_norwegian(query)
    print(f"  (translated to: {norwegian_query})")

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
    return results

if __name__ == "__main__":
    query = "What is the notice period if I want to terminate an employee?"
    print(f"Query: {query}\n")
    for source, text, distance in search(query):
        print(f"[{source}]  (distance={distance:.4f})")
        print(text[:200], "...\n")