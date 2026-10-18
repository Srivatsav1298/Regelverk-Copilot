# Regelverk Copilot 2.0

> **Grounded Norwegian Employment & Labour Law Decision-Support Platform**
> Built for Norwegian employers, employees, and advisors to navigate complex workplace regulations with deterministic statutory accuracy, verified Lovdata citations, and complete privacy.

🔗 **Live Demo**: [regelverk-copilot.onrender.com](https://regelverk-copilot.onrender.com)
⚡ **Local First**: Runs fully locally with Ollama (`qwen3:4b` / `llama3.2`) or cloud providers via OpenRouter.

---

## 🌟 What is Regelverk Copilot 2.0?

Norwegian labour law (*Arbeidsmiljøloven* and *Ferieloven*) is strict, complex, and heavily rules-based. Small business owners, HR managers, and employees routinely struggle with questions about notice periods, dismissal protections, working time limits, and mandatory contract terms.

Regelverk Copilot transforms raw statutory text into **trustworthy, interactive decision-support**:
- **Zero Fabricated Citations**: Every claim is verified against genuine, un-summarized Norwegian statutory provisions from Lovdata.
- **Deterministic Legal Calculators**: Notice periods, contract checklists, working hours, and holiday entitlements are calculated with mathematical precision—never estimated or hallucinated.
- **Guest-First Privacy Architecture**: Ephemeral processing with zero server-side retention of user case descriptions or employment contracts.
- **Multi-Category Coverage**: Expanded far beyond initial termination prototypes into six fundamental areas of Norwegian workplace law.

---

## 🏛️ Statutory Domain Coverage

The knowledge engine indexes and verifies full official provisions directly from Lovdata:

| Domain | Statutory Reference | Core Provisions & Capabilities | Status |
|---|---|---|---|
| **Oppsigelse & Avskjed** (Termination & Dismissal) | Arbeidsmiljøloven Kapittel 15 | Drøftingsmøte (§ 15-1), saklig grunn (§ 15-7), formkrav (§ 15-4), oppsigelsesfrister (§ 15-3), avskjed (§ 15-14), suspensjon (§ 15-13), arbeidsattest (§ 15-15) | ✅ Supported |
| **Arbeidsavtaler & Ansettelse** (Contracts & Employment) | Arbeidsmiljøloven Kapittel 1 & 14 | Arbeidstakerbegrepet (§ 1-8), skriftlig avtale (§ 14-5), 14 obligatoriske minimumskrav (§ 14-6), endringer (§ 14-8), midlertidig ansettelse (§ 14-9) | ✅ Supported |
| **Arbeidstid & Overtid** (Working Time & Overtime) | Arbeidsmiljøloven Kapittel 10 | Alminnelig arbeidstid (§ 10-4), overtidsvilkår og 40% tillegg (§ 10-6), daglig/ukentlig hvile (§ 10-8), pauser (§ 10-9) | ✅ Supported |
| **Ferie & Feriepenger** (Annual Holidays) | Ferieloven (Lov 1988-04-29-21) | 25 virkedagers feriefritid (§ 5), ekstrauke for 60+ (§ 5), feriefastsetting og drøftingsplikt (§ 6), beregning av 10,2% / 12,5% feriepenger (§ 10) | ✅ Supported |
| **Sykefravær & Permisjon** (Sickness & Parental Protection) | Arbeidsmiljøloven Kapittel 15 | 12 måneders oppsigelsesvern ved sykdom (§ 15-8), særskilt oppsigelsesvern ved graviditet, fødsel og foreldrepermisjon (§ 15-9) | ✅ Supported |
| **Varsling & Arbeidsmiljø** (Whistleblowing & Rights) | Arbeidsmiljøloven Kapittel 2A & 4 | Lovfestet rett til å varsle (§ 2A-1), fremgangsmåte (§ 2A-2), forbud mot gjengjeldelse (§ 2A-4), vern mot trakassering og psykososialt arbeidsmiljø (§ 4-3) | ✅ Supported |
| **Konflikt & Søksmålsfrister** (Disputes & Court Deadlines) | Arbeidsmiljøloven Kapittel 17 | Krav om forhandlingsmøte innen 2 uker (§ 17-3), 8 ukers søksmålsfrist for ugyldighet, 6 måneders frist for erstatning, rett til å stå i stillingen (§ 17-4) | ✅ Supported |

---

## 🛠️ Interactive Decision-Support Tools

1. **Oppsigelsesfrist-kalkulator (§ 15-3)**:
   - Takes tenure, age, probation status, and notice date.
   - Accurately applies tenure thresholds (1, 2, 3 months) and senior age brackets (4 months at 50, 5 months at 55, 6 months at 60).
   - Computes statutory month-boundary rules (*løper fra og med første dag i måneden etter at oppsigelsen fant sted*).
2. **Arbeidsavtale-revisor (§ 14-6)**:
   - Automated contract checklist auditing whether an agreement contains all 14 mandatory statutory clauses (parties, place of work, trial period, notice, vacation, pay terms, working hours).
3. **Arbeidstid & Overtidskontroll (§ 10-4 / § 10-6)**:
   - Evaluates weekly hour thresholds, consecutive workday limits, and automatically computes mandatory 40% statutory overtime supplements.
4. **Feriepengekalkulator (Ferieloven § 5 / § 10)**:
   - Calculates exact vacation days and statutory holiday pay rates (10.2% baseline, 12.5% for employees aged 60+).
5. **Formfeilkontroll ved Oppsigelse (§ 15-4 / § 15-5)**:
   - Verifies mandatory statutory written contents and informs about legal consequences of formal defects (invalidation and statutory damages).

---

## 📐 Architecture & Technology Stack

```
                              ┌─────────────────────────────────────────┐
                              │         Modern Web Frontend             │
                              │    React 19 + TypeScript + Vite         │
                              │    Dark/Light theme · WCAG 2.2 AA       │
                              └────────────────────┬────────────────────┘
                                                   │  REST API / JSON
                                                   ▼
                              ┌─────────────────────────────────────────┐
                              │          FastAPI Application            │
                              │    Security headers · Rate limiting     │
                              │    In-memory cache · Metrics collector  │
                              └───────┬─────────────────────────┬───────┘
                                      │                         │
            ┌─────────────────────────┴──────────┐   ┌──────────┴─────────────────────────┐
            ▼                                    ▼   ▼                                    ▼
┌───────────────────────────┐   ┌──────────────────────────┐   ┌──────────────────────────┐
│   Intent Classifier &     │   │   Deterministic Tools    │   │  LLM Provider Adapter    │
│   Query Expansion         │   │  Notice, Contract, Form, │   │  Local Ollama (Qwen/     │
│  Norwegian legal stems    │   │  Holiday & Working Time  │   │  Llama) or OpenRouter    │
└───────────┬───────────────┘   └──────────────────────────┘   └──────────┬───────────────┘
            │                                                             │
            ▼                                                             ▼
┌──────────────────────────────────────────────────────────┐   ┌──────────────────────────┐
│   Resilient Local Hybrid Engine (SQLite)                 │   │  Citation Verification   │
│  - FTS5 BM25 search with Norwegian decompounding         │   │  Strict verbatim chunk   │
│  - Dense vector cosine similarity (Cohere 1024-dim)      │   │  substring validation    │
│  - Reciprocal Rank Fusion (RRF) ranking                  │   └──────────────────────────┘
└──────────────────────────────────────────────────────────┘
```

- **Backend**: FastAPI 0.115+, Python 3.12, Pydantic v2 schemas.
- **Knowledge Engine**: Local embedded SQLite database (`data/legal_corpus.db`) with FTS5 virtual tables and numpy dense vector search. Zero external cloud database dependencies.
- **Embeddings**: Cohere `embed-multilingual-v3.0` (1024 dimensions).
- **LLM Runtime**: Local Ollama auto-detection (`qwen3:4b` / `llama3.2`) with deterministic fallback safety layer and OpenRouter cloud adapter.
- **Frontend**: React 19, TypeScript 5.7, Vite 6, Vanilla CSS design tokens.
- **Quality Assurance**: 47 unit tests in `pytest`, 41 bilingual questions in `eval_questions.jsonl`.

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12+
- Node.js 20+ (for frontend)
- [Ollama](https://ollama.ai) (optional, for local LLM runtime)

### 2. Setup
```bash
git clone https://github.com/yourusername/regelverk-copilot.git
cd regelverk-copilot

# Create virtual environment and install dependencies
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Set COHERE_API_KEY in .env
```

### 3. Build Frontend & Run Backend
```bash
# Install frontend dependencies
npm --prefix frontend install

# Start the frontend from the repository root
npm run dev
```

In a second terminal, launch the backend:

```bash

./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **`http://localhost:5173`** during development. The Vite frontend connects
to the API on port 8000; set `VITE_API_BASE` if the API runs elsewhere. For the
production bundle, run `npm run build` from the repository root.

---

## 🧪 Testing & Evaluation

### Official-source freshness gate

The weekly source review checks the official Lovdata pages and hashes their
normalised content. If a page changes, CI creates a review-only artifact under
`data/source_candidates/` and blocks a fresh deployment. Maintainers must review
the candidate, update the curated `data/raw/` corpus, run ingestion and tests,
then acknowledge the reviewed baseline with:

```bash
./venv/bin/python scripts/acknowledge_source_update.py --reviewed
```

This prevents a legal answer from silently changing without a human-reviewed
corpus update.

### Run Automated Unit Test Suite
```bash
./venv/bin/pytest -v
```
*Current test suite: **47 passed in ~12s**.*

### Run End-to-End Evaluation Benchmark
```bash
EVAL_API_URL=http://localhost:8000/ask ./venv/bin/python eval/run_eval.py eval/eval_questions.jsonl
```

### Run Frontend Typecheck and Build
```bash
cd frontend
npm run typecheck
npm run build
```

---

## 🔒 Security, Compliance & Privacy

- **Guest-First Ephemeral Design**: No user account required. Case details remain strictly in browser storage and are never stored in server databases.
- **Statutory Source Integrity**: All citations include direct deep-links to official legislation on [Lovdata.no](https://lovdata.no).
- **Security Headers**: Standard CSP, HSTS, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`.
- **Statutory Legal Disclaimer**: Transparent notification distinguishing general legal information from formal advocate assistance.

---

## 📄 License
MIT License. Statutory legal texts are governed by Lovdata and Norwegian public sector copyright rules.
