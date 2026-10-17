"""Acknowledge a reviewed source snapshot after corpus re-ingestion."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.source_monitor import acknowledge_current_snapshot


if __name__ == "__main__":
    if "--reviewed" not in sys.argv:
        raise SystemExit("Refusing to acknowledge automatically. Re-run with --reviewed after manual review, ingestion and tests.")
    print(acknowledge_current_snapshot())
