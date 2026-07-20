import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import time
from app.cache import get_cached_response, set_cached_response, _cache, CACHE_TTL_SECONDS


def test_cache_miss_returns_none():
    assert get_cached_response("a question never asked before xyz123") is None


def test_cache_set_then_get_returns_same_value():
    set_cached_response("what is the notice period", {"answer": "one month"})
    result = get_cached_response("what is the notice period")
    assert result == {"answer": "one month"}


def test_cache_is_case_and_whitespace_insensitive():
    set_cached_response("  What Is The Notice Period  ", {"answer": "cached"})
    result = get_cached_response("what is the notice period")
    assert result == {"answer": "cached"}
