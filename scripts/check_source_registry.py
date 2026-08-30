"""Cheap weekly source-registry check; interpretation still requires review."""

import sys
from pathlib import Path
import requests

# Make the script runnable as `python scripts/check_source_registry.py` from
# the repository root and from any other working directory (including CI).
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.source_manifest import SOURCES


def main() -> int:
    failures = []
    for source in SOURCES:
        try:
            response = requests.get(source["official_url"], timeout=15, allow_redirects=True)
            if response.status_code >= 400:
                failures.append(f"{source['provision']}: HTTP {response.status_code}")
        except requests.RequestException as exc:
            failures.append(f"{source['provision']}: {type(exc).__name__}")
    if failures:
        print("Source availability warnings:")
        print("\n".join(failures))
        return 1
    print(f"Checked {len(SOURCES)} official source references.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
