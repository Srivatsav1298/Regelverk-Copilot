"""Check official sources and fail CI when the reviewed legal baseline changed."""

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.source_monitor import source_freshness


def main() -> int:
    report = source_freshness(force=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] == "changed":
        print("Official source content changed; review and re-ingest before deployment.", file=sys.stderr)
        return 2
    if report["status"] == "unavailable":
        print("One or more official sources were unavailable; do not claim freshness.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
