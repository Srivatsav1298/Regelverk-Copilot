"""Download changed official pages into a review-only source package.

The output is deliberately not loaded into the answer index. A maintainer
reviews the snapshots, updates the curated raw corpus, runs the tests, and
only then acknowledges the source baseline.
"""

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "source_candidates"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.source_monitor import check_official_sources
from app.source_manifest import SOURCES


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def main() -> int:
    report = check_official_sources(force=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    written = []
    urls = {item["url"] for item in report.get("changed_sources", [])}
    if not urls and report.get("status") == "current":
        print(json.dumps({"status": "current", "written": []}, ensure_ascii=False, indent=2))
        return 0

    for url in sorted(urls):
        response = requests.get(url, timeout=30, allow_redirects=True, headers={"User-Agent": "Regelverk-Copilot-source-review/1.0"})
        response.raise_for_status()
        digest = hashlib.sha256(re.sub(r"\s+", " ", response.text).strip().encode("utf-8")).hexdigest()
        path = OUTPUT / f"{slug(url)}.html"
        path.write_text(response.text, encoding="utf-8")
        written.append({"url": url, "sha256": digest, "path": str(path.relative_to(ROOT))})

    package = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": report.get("status"),
        "changed_sources": report.get("changed_sources", []),
        "unavailable_sources": report.get("unavailable_sources", []),
        "candidate_files": written,
        "review_required": True,
        "next_step": "Review candidates, update data/raw, run ingestion and tests, then acknowledge the reviewed baseline.",
        "manifest_source_count": len(SOURCES),
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(package, ensure_ascii=False, indent=2))
    return 0 if not report.get("unavailable_sources") else 1


if __name__ == "__main__":
    raise SystemExit(main())
