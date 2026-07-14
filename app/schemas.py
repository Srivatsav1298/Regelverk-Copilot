# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List, Literal


class Citation(BaseModel):
    source_name: str   # e.g. "Arbeidsmiljøloven § 15-3 | Oppsigelsesfrister"
    excerpt: str       # the specific sentence(s) that support the answer


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    confidence: Literal["high", "low"]
    disclaimer: str = (
        "This is general information based on Arbeidsmiljøloven, not legal advice. "
        "Consult a qualified professional for your specific situation."
    )