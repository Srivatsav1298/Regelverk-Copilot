import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer
from app.db import get_connection
from chunk import parse_raw_file
from app.embeddings import get_embedding

load_dotenv()

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"   # multilingual, 384-dim, free, local

def create_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id SERIAL PRIMARY KEY,
            source_name TEXT NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding VECTOR(384)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Table ready.")

def ingest(filepath):
    print(f"Parsing {filepath}...")
    chunks = parse_raw_file(filepath)
    print(f"Found {len(chunks)} chunks.")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE document_chunks RESTART IDENTITY;")

    for i, chunk in enumerate(chunks):
        embedding_input = f"{chunk['source_name']}: {chunk['chunk_text']}"
        embedding = get_embedding(embedding_input)   # now via API, not local model
        cur.execute(
            "INSERT INTO document_chunks (source_name, chunk_text, embedding) VALUES (%s, %s, %s)",
            (chunk["source_name"], chunk["chunk_text"], embedding),
        )
        print(f"  Inserted {i+1}/{len(chunks)}: {chunk['source_name']}")

    conn.commit()
    cur.close()
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    create_table()
    ingest("data/raw/termination_law.txt")