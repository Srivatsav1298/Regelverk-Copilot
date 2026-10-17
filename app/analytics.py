"""Privacy-conscious daily visitor counting.

Only a salted hash of a browser-generated anonymous identifier is stored. No
IP address, user agent, name, case text or question is persisted.
"""

import hashlib
import os
import sqlite3
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.storage import DB_PATH


def _today() -> str:
    timezone = os.getenv("ANALYTICS_TIMEZONE", "Europe/Oslo")
    return datetime.now(ZoneInfo(timezone)).date().isoformat()


def _visitor_hash(visitor_id: str) -> str:
    salt = os.getenv("ANALYTICS_SALT", "regelverk-copilot-local-analytics")
    return hashlib.sha256(f"{salt}:{visitor_id}".encode("utf-8")).hexdigest()


def record_daily_visit(visitor_id: str) -> int:
    """Count one anonymous browser once per local calendar day."""
    visitor_hash = _visitor_hash(visitor_id)
    visit_date = _today()
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_visitors (
                visit_date TEXT NOT NULL,
                visitor_hash TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                PRIMARY KEY (visit_date, visitor_hash)
            )
        """)
        conn.execute(
            "INSERT OR IGNORE INTO daily_visitors (visit_date, visitor_hash, first_seen) VALUES (?, ?, ?)",
            (visit_date, visitor_hash, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return daily_visitor_count()
    finally:
        conn.close()


def daily_visitor_count() -> int:
    visit_date = _today()
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_visitors (
                visit_date TEXT NOT NULL,
                visitor_hash TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                PRIMARY KEY (visit_date, visitor_hash)
            )
        """)
        row = conn.execute("SELECT COUNT(*) FROM daily_visitors WHERE visit_date = ?", (visit_date,)).fetchone()
        return int(row[0] if row else 0)
    finally:
        conn.close()
