# pyrefly: ignore [missing-import]
import time
import json
import os
from pathlib import Path
import logging
from fastapi import FastAPI, HTTPException, Request, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.schemas import AskRequest, AskResponse, CaseAssessmentRequest, CaseAssessmentResponse, BriefRequest, FeedbackRequest, CalculationRequest, CorrectionRequest, VisitRequest
from app.agent import run_retrieval_workflow, extract_case_signals, run_case_tools
from app.llm import generate_answer, generate_case_assessment, provider_name
from app.tools import tool_manifest
from app.verification import verify_citations
from app.cache import get_cached_response, set_cached_response
from app.metrics import record_request, get_summary
from app.source_manifest import corpus_metadata, topic_catalog, freshness_report, WORKFLOWS
from app.decision_tools import calculate_employment_rule, calculate_holiday_pay_amount
from app.brief import render_decision_brief
from app.analytics import record_daily_visit, daily_visitor_count
from app.source_monitor import source_freshness

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("regelverk-copilot")

limiter = Limiter(key_func=get_remote_address)
RATE_LIMIT_ASK = os.getenv("RATE_LIMIT_ASK", "120/minute")
RATE_LIMIT_ASSESS = os.getenv("RATE_LIMIT_ASSESS", "60/minute")
app = FastAPI(title="Regelverk Copilot", version="2.0.0", docs_url="/docs", redoc_url="/redoc")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",")],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "answer": "You've reached the request limit for this demo (5 questions per minute). Please wait a moment and try again.",
            "citations": [],
            "confidence": "low",
            "disclaimer": "This is general information based on Arbeidsmiljøloven, not legal advice. Consult a qualified professional for your specific situation.",
        },
    )


app.mount("/static", StaticFiles(directory="app/static"), name="static")
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")


@app.get("/")
def serve_ui():
    built_index = frontend_dist / "index.html"
    return FileResponse(built_index if built_index.exists() else "app/static/index.html")


@app.get("/dashboard")
def serve_dashboard():
    return FileResponse("app/static/dashboard.html")


@app.get("/health")
def health_check():
    from app.config import runtime_config
    return {"status": "ok", "runtime": runtime_config()}


@app.get("/ready")
def readiness_check():
    from app.config import runtime_config
    config = runtime_config()
    corpus = corpus_metadata()
    return {"ready": True, "provider": provider_name(), "local_first": provider_name() == "ollama", "config": config, "corpus": corpus}


@app.get("/sources")
def sources():
    return corpus_metadata()


@app.get("/topics")
def topics():
    return {"topics": topic_catalog(), "workflows": WORKFLOWS, "language": ["nb", "en"]}


@app.get("/freshness")
def freshness():
    return {**freshness_report(), "source_monitor": source_freshness()}


@app.get("/tools")
def tools_manifest():
    """MCP-shaped discovery endpoint for integrations and interview demos."""
    return tool_manifest()


@app.get("/metrics")
def metrics():
    return get_summary()


@app.get("/evals")
def evals():
    return {"status": "available", "message": "Run eval/run_eval.py to populate a model evaluation report.", "corpus": corpus_metadata()}


@app.post("/ask", response_model=AskResponse)
@limiter.limit(RATE_LIMIT_ASK)
def ask(request: Request, ask_request: AskRequest):
    if not ask_request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(ask_request.question) > 500:
        raise HTTPException(status_code=400, detail="Question is too long (max 500 characters).")

    logger.info(f"Received question (length={len(ask_request.question)} chars)")

    source_status = source_freshness()
    if source_status["status"] == "changed":
        message = (
            "I’m pausing verified answers because an official source changed. The source must be re-ingested and reviewed before this question can be answered as current."
            if ask_request.language == "en" else
            "Jeg setter kvalitetssikrede svar på pause fordi en offisiell kilde er endret. Kilden må hentes inn på nytt og kvalitetssikres før spørsmålet kan besvares som gjeldende rett."
        )
        result = AskResponse(answer=message, citations=[], confidence="low", escalation_level="urgent", escalation_reasons=["official_source_changed"], clarifying_questions=[])
        result.corpus = {**corpus_metadata(), "freshness_warning": True, "source_monitor": source_status}
        return result

    cache_context = json.dumps({"audience": ask_request.audience, "domain": ask_request.domain, "as_of_date": ask_request.as_of_date}, sort_keys=True)
    cached = None if ask_request.include_trace else get_cached_response(f"{ask_request.language}:{ask_request.question}", cache_context)
    if cached is not None:
        logger.info("Cache hit — returning cached response")
        record_request(
            question_length=len(ask_request.question),
            cache_hit=True,
            confidence=cached.confidence,
            latency_ms=0.0,
            provider=provider_name(),
        )
        return cached

    logger.info("Cache miss — calling retrieval + generation")
    start = time.perf_counter()
    chunks, workflow = run_retrieval_workflow(ask_request.question, top_k=4)
    intent = workflow["intent"]
    coverage = intent.get("coverage", {})

    # Only reject if domain is planned and no supported chunks were retrieved, or no chunks matched
    response_plan = workflow.get("response_plan", {})
    if not chunks and (coverage.get("status") == "planned" or intent.get("domain") == "unknown") and not response_plan.get("calculation"):
        result = AskResponse(
            answer="I can’t safely answer this from the reviewed employment-law sources currently available. Choose a supported topic or consult a qualified adviser for this question." if ask_request.language == "en" else "Jeg kan ikke svare trygt på dette med de kvalitetssikrede arbeidsrettskildene som er tilgjengelige nå. Velg et støttet tema eller kontakt en kvalifisert rådgiver.",
            citations=[], confidence="low", domain=intent.get("domain"), subtopic=intent.get("intent"),
            escalation_level="review", escalation_reasons=["topic_not_in_reviewed_corpus"],
            clarifying_questions=["Hvilket konkret arbeidsforhold eller regelverk gjelder?"]
        )
        result.corpus = corpus_metadata()
        record_request(question_length=len(ask_request.question), cache_hit=False, confidence="low", latency_ms=(time.perf_counter()-start)*1000, provider=provider_name(), metadata={"unsupported": True}, tools=workflow["tools"])
        return result

    result = generate_answer(ask_request.question, chunks, language=ask_request.language, audience=ask_request.audience, plan=workflow.get("response_plan"))
    result.corpus = corpus_metadata()
    for citation in result.citations:
        citation.url = citation.url or next((item["official_url"] for item in result.corpus["sources"] if item["provision"] in citation.source_name), result.corpus["source_url"])
        citation.source_status = citation.source_status or "supported"
    result.domain = intent.get("domain")
    result.subtopic = intent.get("intent")
    result.related_topics = [item["domain"] for item in topic_catalog() if item["domain"] != result.domain][:3]

    verification_results = verify_citations(result.citations, chunks)
    unverified_count = sum(1 for v in verification_results if not v["verified"])

    if unverified_count > 0:
        result.confidence = "low"
        logger.info(f"Downgraded confidence: {unverified_count} unverified citation(s)")
    result.escalation_level = "review" if result.confidence == "low" else "none"

    if ask_request.include_trace:
        result.trace = {**workflow, **(result.trace or {}), "provider": provider_name(), "citation_checks": len(verification_results), "unverified_citations": unverified_count}

    latency_ms = (time.perf_counter() - start) * 1000
    record_request(
        question_length=len(ask_request.question),
        cache_hit=False,
        confidence=result.confidence,
        latency_ms=latency_ms,
        provider=provider_name(),
        metadata={"fallback": bool(result.trace and result.trace.get("fallback")) or (result.confidence == "low" and not result.citations), "citation_checks": len(verification_results), "verified_citations": len(verification_results) - unverified_count, "retrieved": len(chunks)},
        tools=workflow["tools"],
    )

    if not ask_request.include_trace:
        set_cached_response(f"{ask_request.language}:{ask_request.question}", result, cache_context)
    return result


@app.post("/assess", response_model=CaseAssessmentResponse)
@limiter.limit(RATE_LIMIT_ASSESS)
def assess(request: Request, case: CaseAssessmentRequest):
    if not case.situation.strip() or len(case.situation) > 1200:
        raise HTTPException(status_code=400, detail="Describe a situation between 1 and 1200 characters.")
    started = time.perf_counter()
    deterministic = run_case_tools(case)
    query = f"{case.situation} {case.termination_reason} age {case.employee_age or ''} years employed {case.years_employed or ''}"
    chunks, workflow = run_retrieval_workflow(query, top_k=4)
    result = generate_case_assessment(case, chunks, deterministic=deterministic)
    for citation in result.citations:
        citation.url = citation.url or corpus_metadata()["source_url"]
        citation.source_status = citation.source_status or "supported"
    checks = verify_citations(result.citations, chunks)
    if any(not item["verified"] for item in checks):
        result.confidence = "low"
    result.corpus = corpus_metadata()
    result.escalation_level = "urgent" if result.risk_level == "high" else "review"
    result.trace = {**workflow, "provider": provider_name(), "signals": extract_case_signals(case.situation), "deterministic": deterministic, "citation_checks": len(checks)}
    record_request(question_length=len(case.situation), cache_hit=False, confidence=result.confidence, latency_ms=(time.perf_counter() - started) * 1000, route="assess", provider=provider_name(), tools=workflow["tools"] + ["extract_case_facts", "calculate_notice_period", "detect_protected_situation", "check_missing_information", "verify_citations"], metadata={"fallback": not result.citations, "citation_checks": len(checks), "verified_citations": len(checks) - sum(1 for item in checks if not item["verified"]), "retrieved": len(chunks)})
    return result


@app.post("/brief", response_class=HTMLResponse)
def brief(request: BriefRequest):
    """Render an ephemeral print-ready brief; the server does not store the case."""
    return HTMLResponse(render_decision_brief(request.case, request.assessment))


@app.post("/feedback")
def feedback(request: FeedbackRequest):
    # Deliberately record only aggregate-safe feedback, never the case or answer text.
    logger.info("Anonymous feedback received: helpful=%s category=%s", request.helpful, request.category)
    return {"accepted": True, "stored_fields": ["helpful", "category"]}


@app.post("/calculate")
def calculate(payload: CalculationRequest):
    if payload.rule == "holiday_pay_amount":
        result = calculate_holiday_pay_amount(remuneration=payload.inputs.get("remuneration"), rate_pct=payload.inputs.get("rate_pct"))
        return {"rule": payload.rule, "result": result, "source_version": corpus_metadata()["corpus_version"], "review_required": True}
    result = calculate_employment_rule(payload.rule, payload.inputs, payload.language)
    return {"rule": payload.rule, "result": result, "source_version": corpus_metadata()["corpus_version"], "review_required": True}


@app.post("/corrections")
def corrections(payload: CorrectionRequest):
    # Store no case text by default; operational logging contains only metadata.
    logger.info("Anonymous correction received: category=%s message_length=%s", payload.category, len(payload.message))
    return {"accepted": True, "stored_fields": ["helpful", "category", "message_length", "source_version"]}


# Versioned API aliases. Legacy routes above remain supported for existing demos.
api_router = APIRouter(prefix="/api/v1")


@api_router.post("/ask", response_model=AskResponse)
def api_ask(request: Request, payload: AskRequest):
    return ask(request, payload)


@api_router.post("/assess", response_model=CaseAssessmentResponse)
def api_assess(request: Request, payload: CaseAssessmentRequest):
    return assess(request, payload)


@api_router.post("/brief", response_class=HTMLResponse)
def api_brief(payload: BriefRequest):
    return brief(payload)


@api_router.get("/sources")
def api_sources():
    return sources()


@api_router.get("/topics")
def api_topics():
    return topics()


@api_router.get("/freshness")
def api_freshness():
    return freshness()


@api_router.post("/calculate")
def api_calculate(payload: CalculationRequest):
    return calculate(payload)


@api_router.post("/corrections")
def api_corrections(payload: CorrectionRequest):
    return corrections(payload)


@api_router.get("/health")
def api_health():
    return health_check()


@api_router.get("/ready")
def api_ready():
    return readiness_check()


@api_router.get("/metrics")
def api_metrics():
    return metrics()


@api_router.get("/tools")
def api_tools():
    return tools_manifest()


@api_router.get("/evals")
def api_evals():
    return evals()


@api_router.post("/feedback")
def api_feedback(payload: FeedbackRequest):
    return feedback(payload)


@api_router.post("/visits")
def api_record_visit(payload: VisitRequest):
    if not 16 <= len(payload.visitor_id) <= 128:
        raise HTTPException(status_code=400, detail="Invalid anonymous visitor identifier.")
    return {"date": "today", "daily_visitors": record_daily_visit(payload.visitor_id), "privacy": "anonymous_daily_count"}


@api_router.get("/visits/today")
def api_daily_visitors():
    return {"date": "today", "daily_visitors": daily_visitor_count(), "privacy": "anonymous_daily_count"}


app.include_router(api_router)
