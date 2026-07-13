# pyrefly: ignore [missing-import]
from fastapi import FastAPI

app = FastAPI(title="Regelverk Copilot")

@app.get("/health")
def health_check():
    return {"status": "ok"}