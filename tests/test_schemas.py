import pytest
from app.schemas import AskRequest, AskResponse, Citation

def test_citation_creation():
    citation = Citation(
        source_name="Arbeidsmiljøloven § 15-3 | Oppsigelsesfrister",
        excerpt="Test excerpt"
    )
    assert citation.source_name == "Arbeidsmiljøloven § 15-3 | Oppsigelsesfrister"
    assert citation.excerpt == "Test excerpt"

def test_ask_request():
    req = AskRequest(question="What is the notice period?")
    assert req.question == "What is the notice period?"

def test_ask_response():
    resp = AskResponse(
        answer="The notice period is one month.",
        citations=[],
        confidence="high"
    )
    assert resp.answer == "The notice period is one month."
    assert resp.citations == []
    assert resp.confidence == "high"
    # disclaimer default
    assert "general information" in resp.disclaimer.lower()

def test_ask_response_with_citations():
    cit = Citation(source_name="Test source", excerpt="Test")
    resp = AskResponse(
        answer="Answer",
        citations=[cit],
        confidence="low",
        disclaimer="Custom disclaimer"
    )
    assert len(resp.citations) == 1
    assert resp.citations[0].source_name == "Test source"
    assert resp.disclaimer == "Custom disclaimer"