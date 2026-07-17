import os
# pyrefly: ignore [missing-import]
import cohere
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

co = cohere.Client(os.environ["COHERE_API_KEY"])


def get_embedding(text: str, input_type: str = "search_document") -> list:
    """
    Gets a multilingual sentence embedding via Cohere's free-tier API,
    instead of loading a model locally. Keeps PyTorch/model weights
    entirely out of our deployed container's memory.

    input_type differs for stored documents ("search_document") vs.
    user queries ("search_query") — Cohere's embed-multilingual-v3.0
    uses this to optimize the embedding for each role, which slightly
    improves retrieval quality over treating both identically.
    """
    response = co.embed(
        texts=[text],
        model="embed-multilingual-v3.0",
        input_type=input_type,
    )
    return response.embeddings[0]