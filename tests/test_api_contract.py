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
