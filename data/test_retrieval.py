import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer
from app.db import get_connection
from app.llm import translate_to_norwegian

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def search(query, top_k=3):
    # Translate first — our chunks are Norwegian, so we embed a Norwegian
    # version of the query for the closest possible same-language comparison.
    norwegian_query = translate_to_norwegian(query)
    print(f"  (translated to: {norwegian_query})")

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
    return results

if __name__ == "__main__":
    query = "What is the notice period if I want to terminate an employee?"
    print(f"Query: {query}\n")
    for source, text, distance in search(query):
        print(f"[{source}]  (distance={distance:.4f})")
        print(text[:200], "...\n")