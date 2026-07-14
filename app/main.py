# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
from app.schemas import AskRequest, AskResponse
from app.retrieval import retrieve_chunks
from app.llm import generate_answer
from app.verification import verify_citations
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse

app = FastAPI(title="Regelverk Copilot")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    chunks = retrieve_chunks(request.question, top_k=3)
    result = generate_answer(request.question, chunks)

    verification_results = verify_citations(result.citations, chunks)
    unverified_count = sum(1 for v in verification_results if not v["verified"])

    if unverified_count > 0:
        # Don't silently trust an unverifiable citation — downgrade confidence
        # so the UI can visibly flag it rather than presenting it as reliable.
        result.confidence = "low"
        print(f"Downgraded confidence: {unverified_count} unverified citation(s)")

    return result

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def serve_ui():
    return FileResponse("app/static/index.html")