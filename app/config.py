import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
REMOTE_MODEL = os.getenv("REMOTE_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")


def runtime_config() -> dict:
    return {
        "provider": LLM_PROVIDER,
        "ollama_model": OLLAMA_MODEL,
        "ollama_base_url": OLLAMA_BASE_URL,
        "remote_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "embeddings_configured": bool(os.getenv("COHERE_API_KEY")),
    }
