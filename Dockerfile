FROM python:3.12-slim

WORKDIR /app

# Install dependencies first — this layer gets cached, so code changes
# don't force a full reinstall of PyTorch/sentence-transformers every rebuild
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hugging Face Spaces expects the app to listen on port 7860
EXPOSE 7860

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}