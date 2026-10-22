# Results so far (2026-10-22)

One page, numbers only; each links to its report. All runs replay bit for
bit from their logs. Total spend across briefs 000–012: **$122.87**.

## The chain

| brief | question | headline | report |
|---|---|---|---|
| 000 | How good is "just ask the model"? | Haiku 5.5, 20 samples, majority vote, 1,000 Cryptonite test clues: **top-1 0.460, ECE 0.159**, over-confident in every bin. Telegraph 0.547 vs Times 0.399. | `reports/000-harness.md` |
| 001 | Can a sound-by-grammar verifier cover real clues? | Gold explanations written in the typed DSL: **coverage 0.850** (val 300), 0.840 (train 500); **0 false accepts / 1,119 mutants**. Wordplay fully mechanical for 7.7%; most parses rest on a synonym leaf. | `reports/001-dsl-verifier.md` |
| 002 | Does propose → verify → decide beat the vote? | Same 1,000 clues: **top-1 0.552 vs 0.460**. Pre-registered verified set **505 clues at 0.861** vs the vote's ≥0.9 band of 275 at 0.858 (1.8× coverage, same precision). | `reports/002-proposer-loop.md` |
| 003 | Can the uncertainty be calibrated and used? | Posterior fitted on a 600-clue val solve, read once on test: **P ≥ 0.9 answers 37.9% of clues at 0.968, ECE 0.027**; above vote share at every coverage; 0.933 at 002's coverage. All 31 of 002's right→wrong answers get P < 0.5. | `reports/003-calibration.md` |
| 004 | Do crossers help, and what is proven? | Grids reconstructed from Cryptonite clue lists (36/100 unique, 0 ambiguous). 20 grids: **clues 0.712 vs 0.513 solved alone**, letters 0.733, 0 fully correct. Committed slots right **99.1%**; guessed slots 54%. $0.94/grid. | `reports/004-grid.md` |
| 005 | Which computation next, under a price? | 10 fresh grids: **VOC beats attempt-all at every budget from $0.45**; 0.706 vs 0.605 clues at $0.94; 0.743 at $1.105 where attempt-all is flat; vote-only floor 0.574. Committed slots 100% right; the bottleneck is commitment. | `reports/005-metacomputation.md` |
| 006 | Can calibration raise commitment? | **No, as specified.** A map fitted on final-state marginals doubled commitment (56% of slots) but committed slots fell to **0.895**, below the 0.99 bar; clues 0.658. Cause: fitted where crossers had settled, applied mid-run. Paired baseline: crossers-first 0.693 vs VOC 0.706 at $0.94 on 005's grids (within noise). | `reports/006-commitment.md` |
| 007 | Can commit-time calibration raise commitment and keep 0.99? | **No, by construction**, answered without paid runs: the refit on 13,929 uncommitted slot-steps is calibrated out of fold and commits from raw 0.576, so P ≥ 0.9 commits are ~0.93–0.96 right. The 0.99 bar and τ = 0.9 were incompatible (drafting error, caught before spend). | `reports/007-commit-time-calibration.md` |
| 008 | Does a thesaurus add evidence for synonym leaves? | **Barely.** Moby + Open English WordNet attest 39–52% of synonym leaves, but on 176 held-out clues the posterior moves within noise (ECE 0.074 → 0.063; P ≥ 0.9 answers 23 → 25 clues). Nearly redundant with the Haiku judge. Half the commonest unattested "synonyms" in correct answers are missing abbreviations. $0. | `reports/008-synonym-attestation.md` |
| 009 | Do missing abbreviations explain the synonym leaves? | **A little.** Wikipedia's crossword abbreviations (whole list, pre-project revision) turn ~9% of synonym leaves into reviewed table hits; Ok rises 0.5–1.4 points (val 8.9 → 9.7%); proven slots on 006's grids stay 0. Mutants 0 / 2,926. $0. | `reports/009-abbreviations.md` |
| 010 | Does hard commitment cost grids? | **No, not on fixed candidates.** Round-1 records of all 40 logged grids: hard 0.557 / soft 0.557 / soft-annealed 0.558 clues; identical entries in all 1,176 slots. Gold is a candidate in only 57% of slots and every regime finds it in 97% of those: the ceiling is candidate generation. Clamping even at 006's raw threshold costs nothing offline, so 006's loss came through re-proposal after wrong commits. Appendix: gold is among the 20 vote samples for only 64–70% of clues; raising m from 3 to 5 adds 3–6 points. $0. | `reports/010-soft-evidence.md` |
| 011 | Which proposer, and how much do crossing letters help? | 150 fresh test clues, structured output: with half the letters, **Opus sampling has gold in its top 5 for 150/150** ($0.026/clue; Haiku 0.953 at $0.007); with no letters, Opus ~0.88–0.92 vs Haiku 0.67. Pick for 013: Opus sample at `half`; early stop not triggered. Haiku and Sonnet fall 20–30 points from old to new clues, Opus is flat (contamination or difficulty: 013 decides). $19.69 incl. smoke tests. | `reports/011-recall-by-proposer.md` |
| 012 | Can we get clean post-cutoff grids? | Fifteensquared (WordPress API, 6 requests, nothing read or committed): 356 posts since 2026-08-01, **136 uniquely reconstructed grids** (FT 49, Independent 42, Guardian 31, Everyman 9, Quiptic 5), 4,061 clues with answers and explanations. Post-cutoff rule now knowledge cutoff + 31 days (floor 2026-08-01). $0. | `reports/012-postcutoff-harvest.md` |

## What the chain shows

1. A verifier whose soundness comes from its grammar covers 85% of real
   wordplay and admits no mutant; its verdicts are evidence a vote share is
   not (002, 003).
2. A posterior over that evidence is calibrated (ECE 0.027) and dominates
   vote share at every coverage (003).
3. Crossers add 20 points of clues, and committed slots are essentially
   always right (004, 005).
4. Choosing computations by expected gain per price beats attempting
   everything, from the point where re-proposals start (005); paired, it is
   level with the crossers-first heuristic (006).

## What it does not show yet

- A clean, contamination-free number: every clue so far is from Cryptonite
  (2000–2020). The post-cutoff set (author's) is the only fix.
- Any fully correct grid. Commitment (the share of slots that reach the
  threshold), not accuracy, is the bottleneck (006).
- "Proven" grids: wordplay is rarely fully mechanical while synonyms are
  oracle leaves. Thesauri don't help (008) and abbreviation lists help a
  little (009); most synonym leaves are genuine synonyms. The product is the
  committed-and-quarantined grid.
- That VOC beats a good heuristic: paired, it doesn't measurably (006).
- More commitment at ≥ 0.99: not reachable by calibrating a hard commit
  (006, 007). Soft evidence changes nothing on fixed candidates (010); the
  cost of wrong commits runs through re-proposal, and the ceiling is
  candidate generation (gold is a round-1 candidate in 57% of slots).
