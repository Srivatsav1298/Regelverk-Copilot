FROM node:22-alpine AS frontend-build
WORKDIR /web
COPY frontend/package.json frontend/tsconfig.json frontend/vite.config.ts ./
COPY frontend/index.html ./index.html
COPY frontend/src ./src
RUN npm install --no-audit --no-fund && npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend-build /web/dist ./frontend/dist
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT:-7860}/api/v1/health')"
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
