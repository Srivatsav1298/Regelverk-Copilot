from pathlib import Path

from data import ingest_all


def test_ingestion_restores_previous_corpus_when_rebuild_fails(monkeypatch, tmp_path):
    database = tmp_path / "legal_corpus.db"
    database.write_bytes(b"known-good-corpus")
    monkeypatch.setattr(ingest_all, "DB_PATH", Path(database))

    def fail_rebuild(*args, **kwargs):
        database.write_bytes(b"incomplete-corpus")
        raise RuntimeError("parser failed")

    monkeypatch.setattr(ingest_all, "_ingest_all", fail_rebuild)

    try:
        ingest_all.ingest_all(generate_embeddings=False)
    except RuntimeError:
        pass
    else:
        raise AssertionError("failed ingestion should raise")

    assert database.read_bytes() == b"known-good-corpus"
    assert not database.with_suffix(".db.ingest-backup").exists()
