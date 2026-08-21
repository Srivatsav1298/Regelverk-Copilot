from app.source_manifest import corpus_metadata


def test_corpus_manifest_is_user_visible_and_versioned():
    metadata = corpus_metadata()
    assert metadata["corpus_version"]
    assert metadata["source_url"].startswith("https://")
    assert len(metadata["sources"]) == 6
    assert all(source["status"] == "supported" for source in metadata["sources"])
