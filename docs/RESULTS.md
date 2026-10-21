# Results so far (2026-10-22)

One page, numbers only; each links to its report. All runs replay bit for
bit from their logs. Total spend across briefs 000–005: **$94.03**.

## The chain

| brief | question | headline | report |
|---|---|---|---|
| 000 | How good is "just ask the model"? | Haiku 5.5, 20 samples, majority vote, 1,000 Cryptonite test clues: **top-1 0.460, ECE 0.159**, over-confident in every bin. Telegraph 0.547 vs Times 0.399. | `reports/000-harness.md` |
| 001 | Can a sound-by-grammar verifier cover real clues? | Gold explanations written in the typed DSL: **coverage 0.850** (val 300), 0.840 (train 500); **0 false accepts / 1,119 mutants**. Wordplay fully mechanical for 7.7%; most parses rest on a synonym leaf. | `reports/001-dsl-verifier.md` |
| 002 | Does propose → verify → decide beat the vote? | Same 1,000 clues: **top-1 0.552 vs 0.460**. Pre-registered verified set **505 clues at 0.861** vs the vote's ≥0.9 band of 275 at 0.858 (1.8× coverage, same precision). | `reports/002-proposer-loop.md` |
| 003 | Can the uncertainty be calibrated and used? | Posterior fitted on a 600-clue val solve, read once on test: **P ≥ 0.9 answers 37.9% of clues at 0.968, ECE 0.027**; above vote share at every coverage; 0.933 at 002's coverage. All 31 of 002's right→wrong answers get P < 0.5. | `reports/003-calibration.md` |
| 004 | Do crossers help, and what is proven? | Grids reconstructed from Cryptonite clue lists (36/100 unique, 0 ambiguous). 20 grids: **clues 0.712 vs 0.513 solved alone**, letters 0.733, 0 fully correct. Committed slots right **99.1%**; guessed slots 54%. $0.94/grid. | `reports/004-grid.md` |
| 005 | Which computation next, under a price? | 10 fresh grids: **VOC beats attempt-all at every budget from $0.45**; 0.706 vs 0.605 clues at $0.94; 0.743 at $1.105 where attempt-all is flat; vote-only floor 0.574. Committed slots 100% right; the bottleneck is commitment. | `reports/005-metacomputation.md` |

## What the chain shows

1. A verifier whose soundness comes from its grammar covers 85% of real
   wordplay and admits no mutant; its verdicts are evidence a vote share is
   not (002, 003).
2. A posterior over that evidence is calibrated (ECE 0.027) and dominates
   vote share at every coverage (003).
3. Crossers add 20 points of clues, and committed slots are essentially
   always right (004, 005).
4. Choosing computations by expected gain per price beats attempting
   everything, from the point where re-proposals start (005).

## What it does not show yet

- A clean, contamination-free number: every clue so far is from Cryptonite
  (2000–2020). The post-cutoff set (author's) is the only fix.
- Any fully correct grid. Commitment (the share of slots that reach the
  threshold), not accuracy, is the bottleneck (006).
- "Proven" grids: wordplay is rarely fully mechanical while synonyms are
  oracle leaves. A reviewed synonym table is the lever (roadmap 007).
- Whether VOC beats the crossers-first heuristic in a paired comparison
  (006, item 1).
