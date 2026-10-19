"""Create and validate an atomic SQLite backup of the legal corpus."""

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.storage import DB_PATH


def backup_database(output_dir: Path) -> dict:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Corpus database does not exist: {DB_PATH}")
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = output_dir / f"legal_corpus-{stamp}.db"
    temporary = target.with_suffix(".tmp")
    source = sqlite3.connect(str(DB_PATH))
    destination = sqlite3.connect(str(temporary))
    try:
        source.backup(destination)
        destination.execute("PRAGMA integrity_check").fetchone()
        integrity = destination.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Backup integrity check failed: {integrity}")
        destination.commit()
    finally:
        destination.close()
        source.close()
    temporary.replace(target)
    manifest = {"created_at": datetime.now(timezone.utc).isoformat(), "database": str(target), "integrity": "ok", "source": str(DB_PATH)}
    (target.with_suffix(".json")).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    directory = Path(os.getenv("CORPUS_BACKUP_DIR", str(ROOT / "data" / "backups")))
    print(json.dumps(backup_database(directory), indent=2))
