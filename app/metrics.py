import time
import collections

MAX_RECORDS = 200

_records: collections.deque = collections.deque(maxlen=MAX_RECORDS)


def record_request(question_length: int, cache_hit: bool, confidence: str, latency_ms: float):
    _records.append({
        "question_length": question_length,
        "cache_hit": cache_hit,
        "confidence": confidence,
        "latency_ms": latency_ms,
        "timestamp": time.time(),
    })


def get_summary() -> dict:
    if not _records:
        return {
            "total_requests": 0,
            "cache_hit_rate_pct": 0.0,
            "avg_latency_ms": 0.0,
            "high_confidence_pct": 0.0,
            "low_confidence_pct": 0.0,
        }

    total = len(_records)
    cache_hits = sum(1 for r in _records if r["cache_hit"])
    high_conf = sum(1 for r in _records if r["confidence"] == "high")
    avg_latency = sum(r["latency_ms"] for r in _records) / total

    return {
        "total_requests": total,
        "cache_hit_rate_pct": round(cache_hits / total * 100, 1),
        "avg_latency_ms": round(avg_latency, 1),
        "high_confidence_pct": round(high_conf / total * 100, 1),
        "low_confidence_pct": round((total - high_conf) / total * 100, 1),
    }
