# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List, Literal, Optional

DISCLAIMER = (
    "This is general information based on Arbeidsmiljøloven, not legal advice. "
    "Consult a qualified professional for your specific situation."
)


class Citation(BaseModel):
    source_name: str   # e.g. "Arbeidsmiljøloven § 15-3 | Oppsigelsesfrister"
    excerpt: str       # the specific sentence(s) that support the answer


class AskRequest(BaseModel):
    question: str
    language: Literal["auto", "nb", "en"] = "auto"
    audience: Literal["employer", "employee"] = "employer"
    include_trace: bool = False


class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    confidence: Literal["high", "low"]
    disclaimer: str = DISCLAIMER
    trace: Optional[dict] = None
    corpus: Optional[dict] = None
    escalation_level: Literal["none", "review", "urgent"] = "none"


class CaseAssessmentRequest(BaseModel):
    situation: str
    domain: str = "termination"
    audience: Literal["employer", "employee"] = "employer"
    termination_reason: str = ""
    employee_age: Optional[int] = None
    years_employed: Optional[float] = None
    on_sick_leave: bool = False
    pregnant_or_parental_leave: bool = False
    in_probation: bool = False
    immediate_dismissal: bool = False
    notice_date: Optional[str] = None
    language: Literal["nb", "en"] = "nb"


class CaseAssessmentResponse(BaseModel):
    summary: str
    risk_level: Literal["low", "medium", "high", "unknown"]
    next_steps: List[str]
    questions_to_confirm: List[str]
    citations: List[Citation]
    confidence: Literal["high", "low"]
    disclaimer: str = DISCLAIMER
    trace: Optional[dict] = None
    corpus: Optional[dict] = None
    escalation_level: Literal["none", "review", "urgent"] = "review"


class BriefRequest(BaseModel):
    case: CaseAssessmentRequest
    assessment: CaseAssessmentResponse


class FeedbackRequest(BaseModel):
    helpful: bool
    category: Optional[Literal["accuracy", "citation", "language", "latency", "other"]] = None
