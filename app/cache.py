import time
import hashlib

_cache = {}
CACHE_TTL_SECONDS = 3600  # 1 hour
CACHE_VERSION = "regelverk-copilot-v3"


def _make_key(question: str, context: str = "") -> str:
    normalized = f"{CACHE_VERSION}:{question.strip().lower()}:{context.strip().lower()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_cached_response(question: str, context: str = ""):
    key = _make_key(question, context)
    entry = _cache.get(key)
    if entry is None:
        return None
    value, timestamp = entry
    if time.time() - timestamp > CACHE_TTL_SECONDS:
        del _cache[key]
        return None
    return value


def set_cached_response(question: str, response, context: str = ""):
    key = _make_key(question, context)
    _cache[key] = (response, time.time())
