"""Ingest all raw legal texts into the local hybrid SQLite storage engine."""

import os
import re
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.storage import init_storage, insert_chunk, get_db_connection, count_chunks
from app.embeddings import get_embedding

RAW_DIR = PROJECT_ROOT / "data" / "raw"

DOMAIN_MAPPING = {
    "termination_law.txt": "termination",
    "contracts_law.txt": "contracts",
    "working_time_law.txt": "working_time",
    "holiday_law.txt": "holidays",
    "workplace_rights_law.txt": "workplace_rights",
    "sickness_and_leave_law.txt": "sickness",
}

SOURCE_URL_MAPPING = {
    "termination": "https://lovdata.no/lov/2005-06-17-62/kapittel_15",
    "contracts": "https://lovdata.no/lov/2005-06-17-62/kapittel_14",
    "working_time": "https://lovdata.no/lov/2005-06-17-62/kapittel_10",
    "holidays": "https://lovdata.no/lov/1988-04-29-21",
    "workplace_rights": "https://lovdata.no/lov/2005-06-17-62/kapittel_2A",
    "sickness": "https://lovdata.no/lov/2005-06-17-62/kapittel_4",
}


def parse_raw_file(filepath: Path):
    text = filepath.read_text(encoding="utf-8")
    sections = re.split(r"(?=^### SOURCE:)", text, flags=re.MULTILINE)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        header_match = re.match(r"### SOURCE:\s*(.+)", section)
        if not header_match:
            continue
        source_name = header_match.group(1).strip()
        body = section[header_match.end():].strip()

        # Extract provision e.g. § 15-3 or § 14-6
        prov_match = re.search(r"§\s*[\d]+[a-zA-Z]?-?[\d]*", source_name)
        provision = prov_match.group(0).replace(" ", "") if prov_match else ""

        # Long provisions: split into paragraphs
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        for para in paragraphs:
            chunks.append({
                "source_name": source_name,
                "provision": provision,
                "chunk_text": para,
            })
    return chunks


def ingest_all(generate_embeddings: bool = True):
    print("Initializing storage tables...")
    init_storage()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM document_chunks;")
    cur.execute("DELETE FROM chunks_fts;")
    conn.commit()
    conn.close()

    total_inserted = 0
    cohere_active = bool(os.getenv("COHERE_API_KEY")) and generate_embeddings

    for raw_file in sorted(RAW_DIR.glob("*.txt")):
        filename = raw_file.name
        domain = DOMAIN_MAPPING.get(filename, "general")
        default_url = SOURCE_URL_MAPPING.get(domain, "https://lovdata.no")

        chunks = parse_raw_file(raw_file)
        print(f"\nProcessing {filename} ({len(chunks)} chunks, domain: {domain})...")

        for idx, chunk in enumerate(chunks, 1):
            embedding = None
            if cohere_active:
                embed_text = f"{chunk['source_name']}: {chunk['chunk_text']}"
                try:
                    embedding = get_embedding(embed_text, input_type="search_document")
                except Exception as exc:
                    print(f"  [Warn] Cohere embedding failed ({type(exc).__name__}), inserting without vector")
                    cohere_active = False

            insert_chunk(
                domain=domain,
                provision=chunk["provision"],
                source_name=chunk["source_name"],
                chunk_text=chunk["chunk_text"],
                url=default_url,
                embedding=embedding,
                metadata={"file": filename, "index": idx},
            )
            total_inserted += 1

        print(f"  -> Ingested {len(chunks)} chunks for {domain}.")

    print(f"\nIngestion finished successfully. Total indexed chunks: {count_chunks()}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    ingest_all(generate_embeddings=True)
