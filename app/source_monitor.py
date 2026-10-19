"""Safe freshness monitoring for official legal sources.

This deliberately does not silently replace the legal corpus. A changed source
must be reviewed and re-ingested before it can be presented as verified.
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict

import requests

from app.source_manifest import SOURCES

STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "source_monitor.json"
MONITOR_TTL_SECONDS = int(os.getenv("SOURCE_MONITOR_TTL_SECONDS", "21600"))


def _normalise(content: str) -> str:
    return re.sub(r"\s+", " ", content).strip()


def _load_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {"sources": {}, "checked_at": None}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sources": {}, "checked_at": None}


def _save_state(state: Dict[str, Any]) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary = STATE_PATH.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(STATE_PATH)
    except OSError:
        # Read-only containers can still serve answers. Freshness remains
        # available for this request without making the API fail closed.
        return


def check_official_sources(force: bool = False) -> Dict[str, Any]:
    previous = _load_state()
    checked_at = previous.get("checked_at")
    if not force and checked_at and time.time() - float(previous.get("checked_epoch", 0)) < MONITOR_TTL_SECONDS:
        return previous

    sources: Dict[str, Any] = {}
    changed = []
    unavailable = []
    unique_urls = {source["official_url"] for source in SOURCES}
    fetched: Dict[str, Any] = {}
    for url in unique_urls:
        try:
            response = requests.get(url, timeout=20, allow_redirects=True, headers={"User-Agent": "Regelverk-Copilot-source-monitor/1.0"})
            response.raise_for_status()
            fetched[url] = {"digest": hashlib.sha256(_normalise(response.text).encode("utf-8")).hexdigest(), "http_status": response.status_code}
        except requests.RequestException as exc:
            fetched[url] = {"error": type(exc).__name__}

    for source in SOURCES:
        url = source["official_url"]
        key = f"{source['provision']}|{url}"
        result = fetched[url]
        if "error" in result:
            unavailable.append({"provision": source["provision"], "url": url, "error": result["error"]})
            sources[key] = {"provision": source["provision"], "url": url, "status": "unavailable", "error": result["error"]}
            continue
        try:
            digest = result["digest"]
            old = previous.get("sources", {}).get(key, {})
            baseline = old.get("baseline_sha256", old.get("sha256", digest))
            status = "changed" if baseline != digest else "current"
            if status == "changed":
                changed.append({"provision": source["provision"], "url": url})
            sources[key] = {"provision": source["provision"], "url": url, "baseline_sha256": baseline, "sha256": digest, "status": status, "http_status": result["http_status"]}
        except (KeyError, TypeError) as exc:
            unavailable.append({"provision": source["provision"], "url": url, "error": type(exc).__name__})
            sources[key] = {"provision": source["provision"], "url": url, "status": "unavailable", "error": type(exc).__name__}

    state = {
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checked_epoch": time.time(),
        "status": "changed" if changed else ("unavailable" if unavailable else "current"),
        "changed_sources": changed,
        "unavailable_sources": unavailable,
        "sources": sources,
    }
    _save_state(state)
    return state


def source_freshness(force: bool = False) -> Dict[str, Any]:
    state = check_official_sources(force=force)
    return {
        "status": state.get("status", "unknown"),
        "checked_at": state.get("checked_at"),
        "changed_sources": state.get("changed_sources", []),
        "unavailable_sources": state.get("unavailable_sources", []),
        "verified_corpus_allowed": state.get("status") == "current",
        "message": {
            "current": "Official source pages match the indexed corpus snapshot.",
            "changed": "An official source changed. Re-ingestion and review are required before answers can be marked verified.",
            "unavailable": "Some official sources could not be checked; the last indexed corpus remains available with a freshness warning.",
        }.get(state.get("status"), "Source freshness has not been established."),
    }


def acknowledge_current_snapshot() -> Dict[str, Any]:
    """Mark the currently observed hashes as the reviewed corpus baseline."""
    state = check_official_sources(force=True)
    for source in state.get("sources", {}).values():
        if source.get("sha256"):
            source["baseline_sha256"] = source["sha256"]
            source["status"] = "current"
    state["status"] = "current"
    state["changed_sources"] = []
    _save_state(state)
    return source_freshness(force=False)
