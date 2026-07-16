## Known limitation: cross-lingual retrieval ranking

English queries are translated to Norwegian before embedding, since our
corpus is Norwegian and embedding models perform best in-language. Domain-
constrained translation (glossary of legal terms) improved top-1 accuracy
significantly, but ranking isn't always perfect — the correct provision
sometimes lands 2nd rather than 1st among semantically related sections.

Mitigation: retrieve top-3 chunks (not top-1) and let the generation step
reason over all candidates, citing only what genuinely supports the answer.

Future improvement (post-MVP): hybrid search (BM25 + vector) would likely
fix this directly, since exact legal terms like "§ 15-3" or "oppsigelsesfrist"
would match on keyword overlap even when embedding similarity ranks it 2nd.



## Known limitation: numeric drift in generated answers

Initial testing found the model correctly cited relevant source excerpts but
paraphrased a specific number incorrectly in prose (stated "three months"
where the cited excerpt actually said "four/five/six months" by age bracket).
Fixed by adding an explicit instruction requiring numbers to be copied
verbatim from excerpts rather than summarized. This shows citation-correctness
and answer-correctness are not the same guarantee — worth verifying separately.

## Known limitation: free-tier rate limits

Groq's free tier caps daily tokens per model. Heavy same-day testing/eval
runs can exhaust this. Mitigated by catching RateLimitError explicitly and
returning an honest low-confidence message instead of a raw 500 error —
the API degrades gracefully rather than crashing when its LLM provider is
temporarily unavailable.

## Known limitation: free-tier rate limits (validated)

Groq's free tier caps daily tokens per model (100,000 TPD for
llama-3.3-70b-versatile). Confirmed in testing: when this limit is hit,
the API returns a clean, honest low-confidence fallback message instead
of crashing — validated across 6 consecutive requests during an

## Known limitation: daily free-tier token quota (per model)

Groq's free tier enforces a 100,000 token/day cap per model. A full 12-question
eval run (~24 API calls: translation + generation per question) can exhaust
this after a day of iterative testing. Mitigation: use the smaller
llama-3.1-8b-instant model for iterative debugging, and run the final,
reported evaluation number once, fresh, on llama-3.3-70b-versatial after
the daily quota resets — ensuring the reported accuracy reflects the actual
production model, not the lighter debugging model.

## Model comparison: llama-3.1-8b-instant vs llama-3.3-70b-versatile on grounding safety

To conserve daily token quota during development, generation was temporarily
run on the smaller 8b model. This surfaced a meaningful safety difference:
on two out-of-scope questions (employee suspension, verbal notice validity),
the 8b model produced confident, plausible-sounding answers with citations
that did not actually support the claim — a hallucinated-grounding failure.
The 70b model, tested on the same two questions earlier, correctly identified
both as out-of-scope with low confidence and no citations.

Conclusion: model capability meaningfully affects the reliability of the
confidence-flagging and citation-grounding safety mechanisms, not just
answer fluency. This confirms llama-3.3-70b-versatile as the correct choice
for the production system, despite its added cost/latency relative to 8b.

## Final evaluation result

12/12 (100%) on the hand-built 12-question evaluation set, using the
production model (llama-3.3-70b-versatile), run once on a fresh daily
quota on [today's date].

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