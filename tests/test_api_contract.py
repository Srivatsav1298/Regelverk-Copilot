from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_versioned_readiness_and_sources_are_public():
    assert client.get("/api/v1/health").status_code == 200
    sources = client.get("/api/v1/sources")
    assert sources.status_code == 200
    assert "domains" in sources.json()


def test_versioned_tools_manifest_is_mcp_shaped():
    payload = client.get("/api/v1/tools").json()
    names = {tool["name"] for tool in payload["tools"]}
    assert {"retrieve_legal_sources", "verify_citations", "calculate_notice_period"} <= names


def test_security_headers_are_present():
    response = client.get("/api/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in response.headers["content-security-policy"]


def test_source_freshness_unavailable_fails_closed(monkeypatch):
    import app.main as main

    monkeypatch.setattr(main, "source_freshness", lambda: {
        "status": "unavailable",
        "verified_corpus_allowed": False,
        "message": "official source unavailable",
    })
    response = TestClient(main.app).post("/api/v1/ask", json={
        "question": "What is the statutory holiday pay rate?",
        "language": "en",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["generation_mode"] == "unavailable"
    assert payload["confidence"] == "low"
    assert payload["escalation_reasons"] == ["official_source_unavailable"]
    assert payload["citations"] == []


def test_operational_metrics_require_admin_token(monkeypatch):
    import app.main as main

    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    assert TestClient(main.app).get("/api/v1/metrics").status_code == 503

    monkeypatch.setenv("ADMIN_TOKEN", "test-only-admin-token")
    client = TestClient(main.app)
    assert client.get("/api/v1/metrics").status_code == 401
    assert client.get("/api/v1/metrics", headers={"Authorization": "Bearer test-only-admin-token"}).status_code == 200
