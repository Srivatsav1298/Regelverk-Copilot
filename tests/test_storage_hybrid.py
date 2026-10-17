"""Tests for local hybrid SQLite storage engine and multi-domain retrieval."""

from app.storage import search_bm25, search_hybrid, count_chunks, get_chunk_by_provision
from app.retrieval import retrieve_chunks


def test_sqlite_storage_contains_ingested_provisions():
    count = count_chunks()
    assert count >= 25, f"Expected at least 25 chunks, got {count}"


def test_bm25_retrieves_exact_statutory_provisions():
    tests = [
        ("drøftingsmøte", "§ 15-1"),
        ("oppsigelsesfrist fem år", "§ 15-3"),
        ("formkrav skriftlig", "§ 15-4"),
        ("prøvetid", "§ 15-6"),
        ("saklig grunn nedbemanning", "§ 15-7"),
        ("sykefravær 12 måneder", "§ 15-8"),
        ("graviditet foreldrepermisjon", "§ 15-9"),
        ("suspensjon", "§ 15-13"),
        ("avskjed grovt pliktbrudd", "§ 15-14"),
        ("arbeidsavtale minimumskrav", "§ 14-6"),
        ("overtid 40 prosent", "§ 10-6"),
        ("feriepenger", "Ferieloven § 10"),
        ("varsle kritikkverdige forhold", "§ 2A-1"),
    ]
    for query, expected_provision in tests:
        results = search_bm25(query, top_k=3)
        assert results, f"No results found for {query}"
        matching = any(expected_provision in r["provision"] or expected_provision in r["source_name"] for r in results)
        assert matching, f"Expected {expected_provision} in top results for '{query}', got {[r['source_name'] for r in results]}"


def test_domain_filtered_retrieval():
    results = retrieve_chunks("feriedager", top_k=2, domain="holidays")
    assert results
    assert any("Ferieloven" in r["source_name"] for r in results)


def test_get_chunk_by_exact_provision():
    chunk = get_chunk_by_provision("§ 15-1")
    assert chunk is not None
    assert "Drøfting" in chunk["source_name"]
