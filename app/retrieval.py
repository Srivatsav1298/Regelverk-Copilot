"""Hybrid retrieval pipeline using local SQLite BM25 + dense vector similarity."""

import logging
from typing import Any, Dict, List, Optional
from app.embeddings import get_embedding
from app.llm import translate_to_norwegian
from app.storage import search_hybrid, get_chunk_by_provision, count_chunks

logger = logging.getLogger("regelverk-copilot")


def retrieve_chunks(question: str, top_k: int = 4, domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves grounded legal chunks using hybrid BM25 + dense vector ranking.
    Translates or enriches query terminology for Norwegian bokmål statutes.
    """
    norwegian_query = translate_to_norwegian(question)
    query_text = f"{question} {norwegian_query}".strip()

    query_embedding = None
    try:
        query_embedding = get_embedding(norwegian_query, input_type="search_query")
    except Exception as exc:
        logger.debug("Vector embedding generation skipped (%s), falling back to BM25", type(exc).__name__)

    results = search_hybrid(
        query_text=query_text,
        query_embedding=query_embedding,
        domain=domain,
        top_k=top_k,
    )

    if not results:
        # Broaden search without domain filter if no hits in specific domain
        if domain:
            results = search_hybrid(query_text=query_text, query_embedding=query_embedding, domain=None, top_k=top_k)

    return results


def get_local_source(provision: str) -> Optional[Dict[str, Any]]:
    """Return an exact source chunk by provision number."""
    return get_chunk_by_provision(provision)
