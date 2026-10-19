"""Non-destructive deployment smoke test.

Usage: ./venv/bin/python scripts/smoke_test.py --base-url https://your-host.example
The script never prints response bodies, question text, credentials, or tokens.
"""

import argparse
import json
import sys
from urllib.parse import urlparse

import requests


def check(base_url: str, timeout: float = 10.0) -> dict:
    base_url = base_url.rstrip("/")
    parsed = urlparse(base_url)
    result = {"base_url": base_url, "checks": [], "status": "PASS"}

    def add(name, status, detail):
        result["checks"].append({"name": name, "status": status, "detail": detail})
        if status in {"FAIL", "BLOCKED"}:
            result["status"] = "FAIL" if status == "FAIL" else "BLOCKED"

    if parsed.scheme != "https":
        add("https", "FAIL", "Deployment URL must use HTTPS.")
    else:
        add("https", "PASS", "HTTPS URL supplied.")

    session = requests.Session()
    for path in ("/api/v1/health", "/api/v1/ready", "/api/v1/freshness"):
        try:
            response = session.get(base_url + path, timeout=timeout)
            if response.status_code != 200:
                add(path, "FAIL", f"HTTP {response.status_code}")
                continue
            payload = response.json()
            add(path, "PASS", "JSON response received.")
            if path.endswith("/ready"):
                provider = payload.get("provider_diagnostics", {})
                if provider.get("reachable") is True:
                    add("provider-reachability", "PASS", "Provider reports reachable.")
                else:
                    add("provider-reachability", "BLOCKED", "Provider is not verified reachable.")
            if path.endswith("/freshness"):
                source = payload.get("source_monitor", {})
                if source.get("status") == "current":
                    add("source-freshness", "PASS", "Official source monitor is current.")
                else:
                    add("source-freshness", "BLOCKED", f"Source monitor status: {source.get('status', 'unknown')}")
        except (requests.RequestException, ValueError) as exc:
            add(path, "BLOCKED", type(exc).__name__)

    try:
        response = session.get(base_url + "/api/v1/health", headers={"Origin": base_url}, timeout=timeout)
        required = {"x-content-type-options", "x-frame-options", "content-security-policy"}
        present = {key.lower() for key in response.headers}
        missing = sorted(required - present)
        add("security-headers", "FAIL" if missing else "PASS", "Missing: " + ", ".join(missing) if missing else "Required headers present.")
    except requests.RequestException as exc:
        add("security-headers", "BLOCKED", type(exc).__name__)

    safe_question = "What is the statutory notice period in Norway?"
    try:
        response = session.post(base_url + "/api/v1/ask", json={"question": safe_question, "language": "en"}, timeout=timeout)
        if response.status_code != 200:
            add("ask-contract", "FAIL", f"HTTP {response.status_code}")
        else:
            payload = response.json()
            required = {"answer", "citations", "confidence", "generation_mode"}
            add("ask-contract", "PASS" if required <= payload.keys() else "FAIL", "Response contract checked without exposing answer content.")
    except (requests.RequestException, ValueError) as exc:
        add("ask-contract", "BLOCKED", type(exc).__name__)

    try:
        response = session.get(base_url + "/api/v1/metrics", timeout=timeout)
        add("admin-protection", "PASS" if response.status_code in {401, 503} else "FAIL", f"Unauthenticated metrics response: HTTP {response.status_code}")
    except requests.RequestException as exc:
        add("admin-protection", "BLOCKED", type(exc).__name__)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="Configured deployment base URL; no default is assumed.")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    report = check(args.base_url, args.timeout)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "PASS" else 2 if report["status"] == "FAIL" else 3)
