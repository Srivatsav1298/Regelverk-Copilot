# Controlled release runbook

The release gate is conservative. Local unit tests do not prove provider, source, hosting, backup, or legal-review readiness.

## 1. Repository checks

```bash
./venv/bin/pytest -q
./venv/bin/python -m compileall -q app data eval tests scripts
cd frontend && pnpm -s typecheck && pnpm -s build
```

## 2. Provider verification

The deployment must use exactly one configured provider.

For Ollama:

```bash
ollama serve
ollama pull llama3.2:latest
curl -sS https://YOUR_HOST/api/v1/ready
```

For OpenRouter, configure `LLM_PROVIDER=openrouter`, `OPENROUTER_API_KEY`, and `REMOTE_MODEL` in the server secret store. Never put these in frontend variables or Git.

## 3. Lovdata freshness

Run from a network that is permitted to access the official URLs:

```bash
./venv/bin/python scripts/check_source_registry.py
./venv/bin/python scripts/check_source_freshness.py
```

If the result is `changed`, review `data/source_candidates/`, update the curated corpus, ingest, run all tests, and acknowledge the reviewed baseline. Do not acknowledge `unavailable`.

## 4. Backup and restore

Run a backup outside the application container:

```bash
CORPUS_BACKUP_DIR=/secure/off-host/regelverk \
  ./venv/bin/python scripts/backup_legal_corpus.py
```

During a restore drill, restore to a separate target first:

```bash
./venv/bin/python scripts/restore_legal_corpus.py \
  /secure/off-host/regelverk/legal_corpus-YYYYMMDDTHHMMSSZ.db \
  --target /tmp/legal_corpus.restore.db
```

Verify `PRAGMA integrity_check` and record the drill in the deployment change log. Configure encrypted storage, least-privilege access, retention, and failure alerts with the hosting provider. Set `BACKUP_VERIFIED=true` only after the drill succeeds.

## 5. Deployment smoke test

No production URL is assumed by the repository:

```bash
./venv/bin/python scripts/smoke_test.py --base-url https://YOUR_HOST
```

The script checks HTTPS, health, readiness, source freshness, security headers, API structure, generation provenance, and unauthenticated metrics protection. It never prints response bodies or secrets.

## 6. Release gate

```bash
./venv/bin/python scripts/release_readiness.py \
  --production-url https://YOUR_HOST \
  --output release-readiness.json
```

Release is `GO` only when every check is `PASS`. A provider, official-source, off-host-backup, CORS, admin-secret, hosting, or legal-review `BLOCKED` result is a `NO-GO`.
