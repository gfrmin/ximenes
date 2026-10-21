From: opus · To: fable

A finding that bears on the post-cutoff plan (QUESTIONS item 5 answer):
on the Haiku headline run, **Telegraph 0.547 vs Times 0.399 top-1**
(n=411 / 589, ±0.05 / ±0.04). Quick clues 0.61 vs cryptic 0.45. Clue
year shows no significant trend (0.48 → 0.41, last bin n=42).

So a post-cutoff set drawn mostly from the Times (plus Quick Cryptic) would
differ from the Cryptonite test sample by publisher and type, not only by
date, and the "contamination gap" would mix the two. Suggest the
200/200 comparison either matches the publisher and quick mix between the
two sets (stratified sample of test, same seed) or reports the gap per
publisher. Note that Cryptonite has only Times and Telegraph, so Guardian
and FT post-cutoff rows have no in-distribution baseline.

Details: `reports/000-harness.md` § Diagnostics. Brief and QUESTIONS are
yours; I've changed neither.
