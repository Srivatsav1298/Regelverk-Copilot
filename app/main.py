# pyrefly: ignore [missing-import]
import time
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.schemas import AskRequest, AskResponse
from app.retrieval import retrieve_chunks
from app.llm import generate_answer
from app.verification import verify_citations
from app.cache import get_cached_response, set_cached_response
from app.metrics import record_request, get_summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("regelverk-copilot")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Regelverk Copilot")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


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


@app.get("/")
def serve_ui():
    return FileResponse("app/static/index.html")


@app.get("/dashboard")
def serve_dashboard():
    return FileResponse("app/static/dashboard.html")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return get_summary()


@app.post("/ask", response_model=AskResponse)
@limiter.limit("5/minute")
def ask(request: Request, ask_request: AskRequest):
    if not ask_request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(ask_request.question) > 500:
        raise HTTPException(status_code=400, detail="Question is too long (max 500 characters).")

    logger.info(f"Received question (length={len(ask_request.question)} chars)")

    cached = get_cached_response(ask_request.question)
    if cached is not None:
        logger.info("Cache hit — returning cached response")
        record_request(
            question_length=len(ask_request.question),
            cache_hit=True,
            confidence=cached.confidence,
            latency_ms=0.0,
        )
        return cached

    logger.info("Cache miss — calling retrieval + generation")
    start = time.perf_counter()
    chunks = retrieve_chunks(ask_request.question, top_k=3)
    result = generate_answer(ask_request.question, chunks)

    verification_results = verify_citations(result.citations, chunks)
    unverified_count = sum(1 for v in verification_results if not v["verified"])

    if unverified_count > 0:
        result.confidence = "low"
        logger.info(f"Downgraded confidence: {unverified_count} unverified citation(s)")

    latency_ms = (time.perf_counter() - start) * 1000
    record_request(
        question_length=len(ask_request.question),
        cache_hit=False,
        confidence=result.confidence,
        latency_ms=latency_ms,
    )

    set_cached_response(ask_request.question, result)
    return result
