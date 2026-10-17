# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import Any, Dict, List, Literal, Optional

DISCLAIMER = (
    "This is general information based on Arbeidsmiljøloven, not legal advice. "
    "Consult a qualified professional for your specific situation."
)


class Citation(BaseModel):
    source_name: str   # e.g. "Arbeidsmiljøloven § 15-3 | Oppsigelsesfrister"
    excerpt: str       # the specific sentence(s) that support the answer
    url: Optional[str] = None
    verified: Optional[bool] = None
    source_status: Optional[Literal["supported", "under_review", "planned"]] = None


class AskRequest(BaseModel):
    question: str
    language: Literal["auto", "nb", "en"] = "auto"
    audience: Literal["employer", "employee"] = "employer"
    include_trace: bool = False
    domain: Optional[str] = None
    as_of_date: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    confidence: Literal["high", "low"]
    disclaimer: str = DISCLAIMER
    trace: Optional[dict] = None
    corpus: Optional[dict] = None
    escalation_level: Literal["none", "review", "urgent"] = "none"
    domain: Optional[str] = None
    subtopic: Optional[str] = None
    applicability: List[str] = []
    clarifying_questions: List[str] = []
    related_topics: List[str] = []
    calculation_results: Dict[str, Any] = {}
    escalation_reasons: List[str] = []


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
    subtopic: Optional[str] = None
    as_of_date: Optional[str] = None


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
    domain: Optional[str] = None
    subtopic: Optional[str] = None
    applicability: List[str] = []
    clarifying_questions: List[str] = []
    related_topics: List[str] = []
    calculation_results: Dict[str, Any] = {}
    escalation_reasons: List[str] = []


class CalculationRequest(BaseModel):
    rule: str
    inputs: Dict[str, Any] = {}
    language: Literal["nb", "en"] = "nb"


class CorrectionRequest(BaseModel):
    helpful: Optional[bool] = None
    category: Optional[Literal["accuracy", "citation", "language", "scope", "other"]] = None
    message: str = ""
    source_version: Optional[str] = None


class BriefRequest(BaseModel):
    case: CaseAssessmentRequest
    assessment: CaseAssessmentResponse


class FeedbackRequest(BaseModel):
    helpful: bool
    category: Optional[Literal["accuracy", "citation", "language", "latency", "other"]] = None


class VisitRequest(BaseModel):
    # Generated locally in the browser; never a name, email, IP or case ID.
    visitor_id: str
