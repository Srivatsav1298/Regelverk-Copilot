# Regelverk Copilot

An AI assistant that answers Norwegian employment-termination law questions with grounded, cited answers — built for small business owners who currently guess or overpay a lawyer for simple questions.

🔗 **Live demo**: https://regelverk-copilot.onrender.com

> Note: this runs on free-tier hosting and may take 30–60 seconds to wake up if it hasn't been used recently. Once warm, responses are fast.

---

## Result

**12/12 (100%)** on a hand-built 12-question evaluation set, tested locally.
**11/12 (92%)** on the same suite run once against the live production deployment.

The single production discrepancy was investigated, not ignored: it traced to expected LLM temperature variance (the model isn't fully deterministic) occasionally producing citation wording that didn't exact-match its source text, correctly triggering the citation-verification safety check to downgrade confidence rather than risk presenting an unverified citation as reliable. Manual re-testing confirmed the underlying answer is consistently correct. Full details in [`NOTES.md`](./NOTES.md).

---

## The problem

Small Norwegian businesses without in-house HR or legal staff regularly need fast answers to employment-law questions — notice periods, probation rules, protected dismissal (sick leave, pregnancy). Today they either guess, or pay a lawyer for questions that don't need one. This assistant gives grounded, citable answers with an explicit "not legal advice" disclaimer, covering six core provisions of Arbeidsmiljøloven, Chapter 15 (termination of employment).

---

## Architecture

```
                     ┌──────────────────┐
   User (web UI) ──► │   FastAPI backend │
                     └──────┬───────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        Query translation  Retrieval   Citation
        (EN → NO, legal    (Cohere      verification
        glossary-guided)   embeddings   (substring match
                            + pgvector)  against source)
                            │
                            ▼
                   ┌─────────────────┐
                   │  LLM generation  │ ── Groq (Llama 3.3 70B)
                   │  structured JSON │    grounded, cited answer
                   └─────────────────┘
```

- **Retrieval**: Norwegian legal text (6 provisions of Arbeidsmiljøloven, Chapter 15) chunked and embedded via **Cohere's `embed-multilingual-v3.0`** API, stored in Postgres with `pgvector`.
- **Cross-lingual handling**: English questions are translated into Norwegian using domain-specific legal terminology (a glossary of exact legal terms) before embedding, since the corpus is Norwegian-only. This closes a real, measured retrieval gap found during development — see `NOTES.md`.
- **Generation**: Groq-hosted **Llama 3.3 70B** produces structured JSON answers (Pydantic-validated) with per-claim citations and a confidence flag.
- **Verification**: every citation is checked as an actual substring of its source chunk before being trusted — not just assumed correct from the model's own output.
- **Cost**: entirely free-tier. Cohere free-tier embeddings, Supabase free Postgres, Groq free inference, Render free web hosting.

---

## Key design decisions

- **No agent framework** (LangChain/LangGraph/CrewAI). The retrieval → generation flow is plain, explicit Python, deliberately — every step is explainable rather than abstracted behind a framework.
- **Domain-constrained translation over generic translation.** Generic Norwegian translation missed exact legal vocabulary (e.g. "oppsigelsesfrist," "avskjed"); fixed with a glossary-guided prompt that forces precise legal terms.
- **Citation verification as a real safety layer, not decoration.** An earlier version silently marked *every* citation "unverified" due to an exact-match lookup failing on a truncated source name — a real bug, found by testing deliberately rather than trusting output that looked plausible. Fixed via prefix matching. See `NOTES.md` for the full account.
- **Hosted embeddings over a locally-loaded model.** The original design loaded a local multilingual embedding model — this worked locally but exceeded Render's free-tier 512MB memory limit in production, causing silent OOM kills. Migrated to Cohere's hosted embeddings API, which removed PyTorch from the deployed container entirely and, as a side effect, measurably improved retrieval ranking quality.
- **Graceful degradation over crashing.** If the LLM provider hits a rate limit, the API returns an honest low-confidence message instead of a raw 500 error — verified under an actual production rate-limit event during development, not just in theory.
- **Numeric accuracy enforced explicitly.** An early version correctly cited source text but paraphrased a specific number incorrectly in prose. Fixed by requiring numbers to be copied verbatim from source excerpts rather than summarized.
- **Production hardening for real users.** Per-IP rate limiting (5/min) on `/ask` to protect shared free-tier LLM/embedding quota; 500-character input cap; in-memory response cache for repeated questions; structured logging without full question text in logs.

---

## Production hardening for real user traffic

Since this assistant runs entirely on shared free-tier infrastructure, the
following protections were added before opening it to real (non-developer)
users:

- **Rate limiting**: 5 requests/minute per IP on `/ask`, returning a clear
  message rather than a raw 429 error, to protect the shared daily Groq/Cohere
  quota from being exhausted by a single user or abusive traffic.
- **Input validation**: 500-character question limit, to prevent unnecessarily
  expensive translation/generation calls from oversized input.
- **In-memory response caching**: identical questions (case/whitespace-insensitive)
  asked within the same hour are served from cache instead of re-calling the LLM,
  reducing cost on genuinely repeated questions (a likely pattern in real usage,
  since many small business owners ask similar things). Resets on container
  restart — an accepted tradeoff at this scale, not a bug.
- **Structured logging**: replaced ad hoc print statements with proper log
  levels, without logging full user question text (only length), to avoid
  storing potentially sensitive input in plaintext logs.

---

## Known limitations

Full, honest log in [`NOTES.md`](./NOTES.md), including:
- A documented model comparison (`llama-3.1-8b-instant` vs `llama-3.3-70b-versatile`) showing the smaller model produced confidently *ungrounded* answers on out-of-scope questions — a real finding that shaped the final production model choice.
- Cross-lingual retrieval ranking isn't always perfect for English queries (mitigated by retrieving top-3 candidates and letting the generation step reason over all of them, citing only what genuinely supports the answer).
- Free-tier hosting (Render) may cold-start after inactivity.
- Groq's free-tier daily token quota can be exhausted under heavy same-day testing; the API degrades gracefully rather than crashing when this happens.

---

## Running locally

```bash
git clone https://github.com/yourusername/regelverk-copilot.git
cd regelverk-copilot
cp .env.example .env   # fill in your own DATABASE_URL, GROQ_API_KEY, COHERE_API_KEY
docker build -t regelverk-copilot .
docker run -p 7860:7860 --env-file .env regelverk-copilot
```

Visit `http://localhost:7860`.

### Ingesting source data / running the evaluation suite

```bash
python data/ingest.py       # chunk, embed, and store the source legal text
python data/test_retrieval.py
python eval/run_eval.py     # runs the 12-question evaluation suite
```

---

## Tech stack

| Layer | Technology | Cost |
|---|---|---|
| Backend | FastAPI | Free |
| Embeddings | Cohere `embed-multilingual-v3.0` | Free tier |
| Vector + relational store | Postgres + `pgvector` (Supabase) | Free tier |
| LLM generation | Groq (Llama 3.3 70B) | Free tier |
| Hosting | Render (Docker) | Free tier |
| Frontend | Vanilla JS + Tailwind (CDN) | Free |

---

## Disclaimer

This tool provides general information based on Arbeidsmiljøloven (Norwegian Working Environment Act) and is **not legal advice**. Consult a qualified professional for your specific situation.
