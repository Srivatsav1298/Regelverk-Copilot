import time
import hashlib

_cache = {}
CACHE_TTL_SECONDS = 3600  # 1 hour


def _make_key(question: str) -> str:
    normalized = question.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_cached_response(question: str):
    key = _make_key(question)
    entry = _cache.get(key)
    if entry is None:
        return None
    value, timestamp = entry
    if time.time() - timestamp > CACHE_TTL_SECONDS:
        del _cache[key]
        return None
    return value


def set_cached_response(question: str, response):
    key = _make_key(question)
    _cache[key] = (response, time.time())
