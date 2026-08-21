import time
import collections

MAX_RECORDS = 200

_records: collections.deque = collections.deque(maxlen=MAX_RECORDS)


def record_request(question_length: int, cache_hit: bool, confidence: str, latency_ms: float, *, route="ask", provider="unknown", tools=None, metadata=None):
    _records.append({
        "question_length": question_length,
        "cache_hit": cache_hit,
        "confidence": confidence,
        "latency_ms": latency_ms,
        "timestamp": time.time(),
        "route": route,
        "provider": provider,
        "tools": tools or [],
        "metadata": metadata or {},
    })


def get_summary() -> dict:
    if not _records:
        return {
            "total_requests": 0,
            "cache_hit_rate_pct": 0.0,
            "avg_latency_ms": 0.0,
            "high_confidence_pct": 0.0,
            "low_confidence_pct": 0.0,
            "providers": {},
            "routes": {},
        }

    total = len(_records)
    cache_hits = sum(1 for r in _records if r["cache_hit"])
    high_conf = sum(1 for r in _records if r["confidence"] == "high")
    avg_latency = sum(r["latency_ms"] for r in _records) / total
    providers = collections.Counter(r["provider"] for r in _records)
    routes = collections.Counter(r["route"] for r in _records)
    verified = [r["metadata"]["verified_citations"] for r in _records if "verified_citations" in r["metadata"]]
    citation_total = [r["metadata"]["citation_checks"] for r in _records if "citation_checks" in r["metadata"]]
    fallbacks = sum(1 for r in _records if r["metadata"].get("fallback"))

    return {
        "total_requests": total,
        "cache_hit_rate_pct": round(cache_hits / total * 100, 1),
        "avg_latency_ms": round(avg_latency, 1),
        "high_confidence_pct": round(high_conf / total * 100, 1),
        "low_confidence_pct": round((total - high_conf) / total * 100, 1),
        "providers": dict(providers),
        "routes": dict(routes),
        "fallback_rate_pct": round(fallbacks / total * 100, 1),
        "citation_verification_rate_pct": round(sum(verified) / sum(citation_total) * 100, 1) if sum(citation_total) else 0.0,
    }
