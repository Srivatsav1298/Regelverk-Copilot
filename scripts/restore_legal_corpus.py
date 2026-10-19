"""Validate and atomically restore a previously created corpus backup."""

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.storage import DB_PATH


def restore_database(backup: Path, target: Path = DB_PATH) -> dict:
    if not backup.exists():
        raise FileNotFoundError(f"Backup does not exist: {backup}")
    check = sqlite3.connect(str(backup))
    try:
        integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Backup integrity check failed: {integrity}")
    finally:
        check.close()
    temporary = target.with_suffix(".restore.tmp")
    temporary.write_bytes(backup.read_bytes())
    temporary.replace(target)
    return {"restored": str(target), "source": str(backup), "integrity": "ok"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", type=Path)
    parser.add_argument("--target", type=Path, default=DB_PATH)
    args = parser.parse_args()
    print(restore_database(args.backup, args.target))
