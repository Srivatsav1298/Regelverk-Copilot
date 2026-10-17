from pathlib import Path

from app import source_monitor


class FakeResponse:
    status_code = 200
    text = "<html> official text </html>"

    def raise_for_status(self):
        return None


def test_source_monitor_deduplicates_urls_and_marks_baseline(monkeypatch, tmp_path):
    calls = []
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(source_monitor, "STATE_PATH", state_path)
    monkeypatch.setattr(source_monitor, "SOURCES", [
        {"provision": "§ 1", "official_url": "https://example.test/law"},
        {"provision": "§ 2", "official_url": "https://example.test/law"},
    ])

    def fake_get(*args, **kwargs):
        calls.append(args[0])
        return FakeResponse()

    monkeypatch.setattr(source_monitor.requests, "get", fake_get)
    first = source_monitor.check_official_sources(force=True)
    assert first["status"] == "current"
    assert calls == ["https://example.test/law"]

    FakeResponse.text = "<html> updated official text </html>"
    second = source_monitor.check_official_sources(force=True)
    assert second["status"] == "changed"
    assert len(second["changed_sources"]) == 2


def test_source_monitor_tolerates_read_only_state(monkeypatch, tmp_path):
    monkeypatch.setattr(source_monitor, "STATE_PATH", tmp_path / "missing" / "state.json")
    monkeypatch.setattr(source_monitor, "SOURCES", [])
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("read-only")))
    result = source_monitor.check_official_sources(force=True)
    assert result["status"] == "current"
