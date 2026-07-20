# Development Notes — Regelverk Copilot

A running log of real bugs found, fixes applied, and deliberate design tradeoffs made during development.

---

## Known limitation: cross-lingual retrieval ranking

English queries are translated to Norwegian before embedding, since our
corpus is Norwegian and embedding models perform best in-language. Domain-
constrained translation (glossary of legal terms) improved top-1 accuracy
significantly, but ranking wasn't always perfect with the original local
embedding model — the correct provision sometimes landed 2nd rather than 1st
among semantically related sections.

Mitigation: retrieve top-3 chunks (not top-1) and let the generation step
reason over all candidates, citing only what genuinely supports the answer.

This limitation was substantially resolved after migrating to Cohere's
hosted embeddings (see entry below) — retrieval ranking improved measurably.

---

## Known limitation (fixed): citation verification false negatives

Citation verification initially failed on every request — the model
sometimes truncates source_name (dropping the "| Title" suffix), causing
an exact-match dictionary lookup to always miss and mark all citations as
unverified, silently downgrading confidence on fully correct answers.
Fixed by matching source_name via prefix instead of exact equality.

This bug is now covered by a permanent regression test:
`tests/test_verification.py::test_verified_with_truncated_source_name`.

---

## Known limitation (fixed): numeric drift in generated answers

Initial testing found the model correctly cited relevant source excerpts but
paraphrased a specific number incorrectly in prose (stated "three months"
where the cited excerpt actually said "four/five/six months" by age bracket).
Fixed by adding an explicit instruction requiring numbers to be copied
verbatim from excerpts rather than summarized.

This shows citation-correctness and answer-correctness are not the same
guarantee — worth verifying separately, not assuming one implies the other.

---

## Known limitation (fixed): verbatim excerpt leaking into answer field

A later prompt iteration (aimed at fixing numeric drift) was over-applied by
the model, which sometimes copied an entire raw Norwegian excerpt into the
"answer" field instead of writing a natural-language explanation. Fixed by
explicitly instructing the model to always write the answer as its own
sentence, in the question's language, while still requiring numbers within
that sentence to match excerpts exactly.

---

## Model comparison: llama-3.1-8b-instant vs llama-3.3-70b-versatile on grounding safety

To conserve daily token quota during development, generation was temporarily
run on the smaller 8b model. This surfaced a meaningful safety difference:
on two out-of-scope questions (employee suspension, verbal notice validity),
the 8b model produced confident, plausible-sounding answers with citations
that did not actually support the claim — a hallucinated-grounding failure.
The 70b model, tested on the same two questions, correctly identified both
as out-of-scope with low confidence and no citations.

Conclusion: model capability meaningfully affects the reliability of the
confidence-flagging and citation-grounding safety mechanisms, not just
answer fluency. This confirms llama-3.3-70b-versatile as the correct choice
for the production system, despite its added cost/latency relative to 8b.

---

## Known limitation: free-tier rate limits

Groq's free tier caps daily tokens per model. Heavy same-day testing/eval
runs can exhaust this. Mitigated by catching RateLimitError explicitly and
returning an honest low-confidence message instead of a raw 500 error —
the API degrades gracefully rather than crashing when its LLM provider is
temporarily unavailable.

---

## Known limitation: eval run invalidated by rate limit

One eval run coincided with the daily Groq free-tier token limit being hit.
All 12 questions returned the graceful fallback message rather than real
answers — including the 4 out-of-scope questions, which "passed" by
coincidence rather than by correctly recognizing out-of-scope content. This
run was discarded; a valid run requires confirming API availability first
with a single test call before running the full suite, to avoid wasting
quota on repeated rate-limited calls.

---

## Final evaluation result (local)

12/12 (100%) on the hand-built 12-question evaluation set, using the
production model (llama-3.3-70b-versatile), run once on a fresh daily
quota, tested locally.

This result reflects a series of real fixes made during development:
- Cross-lingual retrieval gap (English queries vs Norwegian corpus),
  fixed via domain-constrained query translation
- Numeric drift in generated answers vs cited source text, fixed via
  explicit verbatim-number instruction
- Verbatim excerpt text leaking into the answer field instead of a
  natural-language explanation, fixed via prompt correction
- Citation verification false negatives caused by exact-match string
  comparison on truncated source names, fixed via prefix matching
- Two eval-set expectations that were themselves incorrect (a mislabeled
  provision title, an underestimated scope for one provision), caught by
  inspecting full model output rather than trusting pass/fail labels alone

See model-comparison notes above for why llama-3.3-70b-versatile was
selected over the smaller llama-3.1-8b-instant despite added cost/latency.

---

## Embedding provider migration: local model → Cohere API

Switched from a locally-loaded sentence-transformers model
(paraphrase-multilingual-MiniLM-L12-v2) to Cohere's hosted
embed-multilingual-v3.0 API. Originally forced by Render free-tier memory
limits — loading PyTorch plus the model locally exceeded the 512MB cap,
causing silent OOM kills on the deployed container in production.

This had an unexpected additional benefit: retrieval ranking improved
noticeably — the correct provision (§ 15-3) now returns first with a
clearer separation from unrelated provisions than the local model achieved,
even after the earlier cross-lingual translation fix. A constraint forced
by infrastructure turned into a genuine quality improvement.

Side note: an earlier attempt used Hugging Face's Inference API
(api-inference.huggingface.co) as the fix, but that endpoint has been
deprecated/restructured as part of HF's move to "Inference Providers" —
confirmed via DNS resolution failure in production. Cohere was chosen
instead for a stable, well-documented free-tier embeddings endpoint.

---

## Known limitation: occasional citation-verification flakiness in production

One eval run against the deployed (Render) endpoint showed the notice-period
question failing on "confidence was not high," while the same question
passed on every other run (local and live) before and after. Manual re-testing
confirmed the question consistently returns confidence: "high" with correct
citations. Root cause: llama-3.3-70b-versatile runs at temperature=0.2 (not
fully deterministic), so citation excerpt wording occasionally varies enough
to momentarily fail the exact-substring verification check, correctly
downgrading confidence as a safety measure rather than silently passing a
possibly-mismatched citation. This is the verification system behaving as
designed on a genuine edge case, not a functional bug — no fix applied, since
failing safe (understating confidence) is the correct behavior when in doubt.

---

## Final evaluation result (live production deployment)

11/12 (92%) on the same 12-question suite, run once against the live
Render deployment. The single discrepancy is the citation-verification
flakiness documented above — investigated and explained, not a functional
defect. See "Result" section of README.md for how both numbers (local
12/12, live 11/12) are reported together, honestly, rather than reporting
only the more favorable number.

---

## Test suite and CI added

Added a pytest suite (chunking parser, citation verification, schema
validation — 16 tests total, all pure logic, no external API calls or live
DB required) plus a GitHub Actions workflow that runs these tests
automatically on every push to main.

Deliberately kept the existing evaluation suite (eval/run_eval.py, which
calls real Groq and Cohere APIs and is rate-limited) OUT of the automatic
push-triggered workflow — it's wired into a separate, manually-triggered
workflow instead (workflow_dispatch), so evaluation can be run on demand
against the live deployment without burning API quota on every commit,
including trivial changes.

One test (`test_verified_with_truncated_source_name`) is a direct
regression test for the citation-verification bug found on Day 3 — turning
a real, previously-live bug into a permanent safeguard against it recurring.

---

## Forward-looking improvements (not yet implemented)

- **Multi-provider LLM fallback**: currently generation depends solely on
  Groq's free tier. If quota is exhausted during a live demo, the system
  degrades gracefully (honest low-confidence message) rather than crashing
  — but a further improvement would be automatic failover to a second free
  provider (e.g. Gemini free tier) when RateLimitError is raised, to
  maximize demo uptime without cost.
- **Hybrid search (BM25 + vector)**: would likely further improve retrieval
  ranking, since exact legal terms like "§ 15-3" or "oppsigelsesfrist"
  would match on keyword overlap even in cases where embedding similarity
  alone ranks the correct provision 2nd rather than 1st.
- **Expanded legal domain coverage**: currently limited to 6 provisions of
  Arbeidsmiljøloven Chapter 15 (termination). Deliberately scoped narrow
  for the MVP; broader coverage (leave, tax/reporting obligations) was
  explicitly deferred rather than attempted shallowly across more domains.

---

## Production hardening for real users (rate limiting, caching, logging)

Before opening this project to real anonymous traffic, added: per-IP rate
limiting (5/min) on /ask to protect shared free-tier LLM/embedding quota from
exhaustion by a single user; a 500-character input length cap; an in-memory
response cache for repeated questions (accepted limitation: resets on restart);
and structured logging in place of ad hoc print statements, deliberately
excluding full question text from logs to avoid storing user input in plaintext.

Frontend: added mobile-responsive input layout, example-question chips (since
real users won't know the assistant's scope is limited to 6 provisions), a
visible scope disclaimer, a live character counter, and distinct handling of
the 429 rate-limit response so rate-limited users see a clear message instead
of a generic error.