import json
import logging
import os
import urllib.request
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("regelverk-copilot")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
REMOTE_MODEL = os.getenv("REMOTE_MODEL", "nvidia/nemotron-3.5-lightning:free")


def detect_ollama_model() -> str:
    """Detect installed local Ollama models; fall back to llama3.2:latest."""
    env_model = os.getenv("OLLAMA_MODEL")
    if env_model:
        return env_model
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "RegelverkCopilot"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name") for m in data.get("models", []) if m.get("name")]
            if models:
                # Prefer llama3.2 if available, else first installed
                for preferred in ("llama3.2:latest", "llama3.2", "qwen3:4b", "llama3.1"):
                    if preferred in models:
                        return preferred
                return models[0]
    except Exception as exc:
        logger.debug("Ollama model auto-detection skipped: %s", exc)
    return "llama3.2:latest"


OLLAMA_MODEL = detect_ollama_model()


def runtime_config() -> dict:
    return {
        "provider": LLM_PROVIDER,
        "ollama_model": OLLAMA_MODEL,
        "ollama_base_url": OLLAMA_BASE_URL,
        "remote_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "embeddings_configured": bool(os.getenv("COHERE_API_KEY")),
    }
