from app.source_manifest import corpus_metadata, freshness_report, topic_catalog, WORKFLOWS


def test_corpus_manifest_is_user_visible_and_versioned():
    metadata = corpus_metadata()
    assert metadata["corpus_version"]
    assert metadata["source_url"].startswith("https://")
    assert len(metadata["sources"]) == 6
    assert all(source["status"] == "supported" for source in metadata["sources"])


def test_catalogue_is_transparent_about_planned_coverage():
    domains = {item["domain"]: item for item in topic_catalog()}
    assert domains["termination"]["status"] == "supported"
    assert domains["working_time"]["status"] == "planned"
    assert any(workflow["id"] == "hiring" for workflow in WORKFLOWS)


def test_freshness_report_exposes_release_state():
    report = freshness_report()
    assert report["corpus_version"]
    assert report["release_status"] in {"current", "needs_review"}
