"""Generate a conservative, machine-readable release gate report."""

import argparse
import csv
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.llm import provider_diagnostics
from app.source_monitor import source_freshness
from app.storage import DB_PATH


def item(name, status, evidence, action=None):
    value = {"name": name, "status": status, "evidence": evidence}
    if action:
        value["required_action"] = action
    return value


def build_report(production_url: str | None = None) -> dict:
    checks = []
    provider = provider_diagnostics()
    checks.append(item("provider_connectivity", "PASS" if provider.get("reachable") is True else "BLOCKED", provider, "Configure and verify the provider before launch."))
    freshness = source_freshness(force=True)
    source_status = freshness.get("status")
    checks.append(item("legal_source_freshness", "PASS" if source_status == "current" else "FAIL" if source_status == "changed" else "BLOCKED", freshness, "Restore Lovdata access and run check_source_freshness.py."))

    try:
        conn = sqlite3.connect(str(DB_PATH))
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        backup_status = "PASS" if integrity == "ok" else "FAIL"
    except Exception as exc:
        backup_status, integrity = "FAIL", type(exc).__name__
    checks.append(item("local_corpus_integrity", backup_status, {"integrity": integrity, "backup_tool": "present"}, "Run and retain an off-host backup."))

    review_file = ROOT / "eval" / "production_readiness_review.csv"
    with review_file.open(newline="", encoding="utf-8") as handle:
        reviewer_statuses = {row["reviewer_status"] for row in csv.DictReader(handle)}
    review_pass = reviewer_statuses == {"APPROVED"}
    checks.append(item("independent_legal_review", "PASS" if review_pass else "BLOCKED", {"statuses": sorted(reviewer_statuses)}, "A qualified Norwegian employment-law reviewer must assess every case."))
    checks.append(item("admin_secret", "PASS" if os.getenv("ADMIN_TOKEN") else "BLOCKED", {"configured": bool(os.getenv("ADMIN_TOKEN"))}, "Set ADMIN_TOKEN in the deployment secret store."))
    cors = os.getenv("CORS_ORIGINS", "*")
    checks.append(item("cors_configuration", "PASS" if cors.strip() != "*" else "BLOCKED", {"wildcard": cors.strip() == "*"}, "Set CORS_ORIGINS to the exact production frontend origin."))
    checks.append(item("citation_validation", "PASS" if (ROOT / "app" / "verification.py").exists() else "FAIL", {"verifier_present": (ROOT / "app" / "verification.py").exists()}, "Run the citation verification test suite."))
    checks.append(item("offhost_backup", "PASS" if os.getenv("BACKUP_VERIFIED") == "true" else "BLOCKED", {"verified_by_environment": os.getenv("BACKUP_VERIFIED") == "true"}, "Configure encrypted off-host backups, then set BACKUP_VERIFIED=true only after a successful restore drill."))
    checks.append(item("hosting_smoke_test", "PASS" if production_url else "NOT_TESTED", {"base_url_supplied": bool(production_url)}, "Run smoke_test.py with the real HTTPS deployment URL."))
    overall = "GO" if all(check["status"] == "PASS" for check in checks) else "NO-GO"
    return {"overall_recommendation": overall, "checks": checks, "repository": "Regelverk-Copilot", "production_url_supplied": bool(production_url)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--production-url", default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    report = build_report(args.production_url)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    raise SystemExit(0 if report["overall_recommendation"] == "GO" else 2)
