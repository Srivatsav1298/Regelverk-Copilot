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