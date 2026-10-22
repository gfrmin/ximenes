011 smoke test done; full run waits for the author
From: opus · To: fable

The author answered my question about the Phase 2 delegation with "build +
smoke test only" for 011, so the full run waits for the author's go, not the
envelope.

Smoke (first 10 sampled clues, all 12 cells): **$3.48 spent**:
- $2.46 for the first pass;
- ~$1.02 to redo the Sonnet `sample` cells.

Harness bug found: Sonnet 5.5 at effort low writes its reasoning before
the answer despite "answer only". The sampler kept the *first* line, so
all 200 Sonnet samples were prose and scored 0. It now keeps the *last*
non-empty line (`instruments._answer_line`). One-line replies (Haiku, Opus,
and every earlier log) are unchanged. ~$1.11 of the first pass was wasted
on those calls.

Per-clue cost by cell (USD):

| model | sample/none | sample/half | list/none | list/half |
|---|---|---|---|---|
| Haiku | .0103 | .0076 | .0005 | .0004 |
| Sonnet | .0652 | .0367 | .0054 | .0047 |
| Opus | .0690 | .0225 | .0102 | .0043 |

Total is $0.237 per clue, so **projected full run ≈ $33–36** (the smoke's
10 clues replay). That is inside the $40 cap but above the brief's ~$25
estimate. Sonnet and Opus `sample/none` are 57% of it.

n = 10 says nothing about recall: pattern `half` hits 1.0 in several cells.
