import pytest
from app.verification import verify_citations
from app.schemas import Citation

def test_verify_citations_all_match():
    citations = [
        Citation(source_name="Source A", excerpt="exact text"),
        Citation(source_name="Source B", excerpt="Another excerpt")
    ]
    retrieved_chunks = [
        {"source_name": "Source A", "chunk_text": "This is exact text in chunk"},
        {"source_name": "Source B", "chunk_text": "Another excerpt appears here"}
    ]
    result = verify_citations(citations, retrieved_chunks)
    assert len(result) == 2
    assert result[0]["verified"] is True
    assert result[1]["verified"] is True

def test_verify_citations_no_match():
    citations = [
        Citation(source_name="Source A", excerpt="not present")
    ]
    retrieved_chunks = [
        {"source_name": "Source A", "chunk_text": "completely different text"}
    ]
    result = verify_citations(citations, retrieved_chunks)
    assert result[0]["verified"] is False

def test_verify_citations_partial_match():
    citations = [
        Citation(source_name="Source A", excerpt="partial text")
    ]
    retrieved_chunks = [
        {"source_name": "Source A", "chunk_text": "This contains partial text indeed"}
    ]
    result = verify_citations(citations, retrieved_chunks)
    assert result[0]["verified"] is True

def test_verify_citations_source_name_prefix():
    # citation source_name may be truncated; matching uses startswith
    citations = [
        Citation(source_name="Arbeidsmiljøloven § 15-3", excerpt="text")
    ]
    retrieved_chunks = [
        {"source_name": "Arbeidsmiljøloven § 15-3 | Oppsigelsesfrister", "chunk_text": "some text here"}
    ]
    result = verify_citations(citations, retrieved_chunks)
    # Should match because source_name starts with citation.source_name
    assert result[0]["verified"] is True

def test_verify_citations_whitespace_normalization():
    citations = [
        Citation(source_name="Source", excerpt="  multiple   spaces  ")
    ]
    retrieved_chunks = [
        {"source_name": "Source", "chunk_text": "multiple spaces"}
    ]
    result = verify_citations(citations, retrieved_chunks)
    # After normalization, both become "multiple spaces"
    assert result[0]["verified"] is True

def test_verify_citations_multiple_chunks():
    citations = [
        Citation(source_name="Source A", excerpt="find me")
    ]
    retrieved_chunks = [
        {"source_name": "Source B", "chunk_text": "not here"},
        {"source_name": "Source A", "chunk_text": "you can find me in this chunk"}
    ]
    result = verify_citations(citations, retrieved_chunks)
    assert result[0]["verified"] is True

def test_verify_citations_empty_lists():
    result = verify_citations([], [])
    assert result == []