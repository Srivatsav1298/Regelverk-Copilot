import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.metrics import record_request, get_summary, _records


def test_store_starts_empty():
    _records.clear()
    summary = get_summary()
    assert summary["total_requests"] == 0


def test_recorded_request_appears_in_summary():
    _records.clear()
    record_request(question_length=20, cache_hit=False, confidence="high", latency_ms=150.0)
    summary = get_summary()
    assert summary["total_requests"] == 1
    assert summary["high_confidence_pct"] == 100.0
    assert summary["low_confidence_pct"] == 0.0


def test_summary_computes_rates_correctly():
    _records.clear()
    record_request(question_length=10, cache_hit=True, confidence="high", latency_ms=50.0)
    record_request(question_length=20, cache_hit=True, confidence="high", latency_ms=60.0)
    record_request(question_length=30, cache_hit=False, confidence="low", latency_ms=200.0)
    record_request(question_length=40, cache_hit=False, confidence="high", latency_ms=300.0)

    summary = get_summary()
    assert summary["total_requests"] == 4
    assert summary["cache_hit_rate_pct"] == 50.0
    assert summary["avg_latency_ms"] == 152.5
    assert summary["high_confidence_pct"] == 75.0
    assert summary["low_confidence_pct"] == 25.0
