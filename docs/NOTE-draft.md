# ximenes: what it takes to solve cryptic crosswords, measured on clean puzzles (draft note)

*Draft, 2026-10-23. Numbers from `reports/` 013 and 014. Every number
replays bit for bit from its logs.*

## Result

On **40 Guardian, Independent and FT daily cryptics published 2 August to
22 October 2026** (after every model's knowledge cutoff plus a month; two
disjoint samples of 20, each read once), the full solver fills **17 grids
fully correctly (43%; Beta posterior 95% interval 29–58%)**. It gets 95–97%
of clues right, and its committed answers are right 97.7–99.2% of the time
(465/476 and 491/495).

A much simpler solver does as well. **Claude Opus 5.5 proposing answers, the
grid's crossing letters, belief propagation, and a posterior fitted on
held-out grids** fills **8 of 20** of the second sample's grids fully
correctly (95% interval 22–62%), level with the full solver's 7 on the same
grids. It reaches its 8 by **$1 per grid**.

## What each part contributes (paired, on post-cutoff grids)

| step | effect | evidence |
|---|---|---|
| Opus as proposer, not a small model | the right answer is a candidate for most clues; with half the letters known, in the top 5 for 150 of 150 test clues | brief 011 |
| crossing letters + belief propagation | clues right 0.78 → 0.97 from the same candidates | 013 ablation |
| **calibration** (a posterior fitted on held-out grids) | raw proposer shares are underconfident (ECE 0.177 against the fitted posterior's 0.064; 341 committed slots against 495 in 013); with the fitted posterior and no verifier, 430 committed, 425 right; uncalibrated, the solver under-commits and runs out of crossing letters | 013 appendix (raw vs full solver), 014's calibrated arm; attributed to calibration because 014 shows the verifier adds nothing on top of it |
| the sound-by-grammar wordplay verifier, on top of calibration | **no measurable gain**: fully correct 7 vs 8 of 20, P(full better) = 0.375; clue difference −0.004 (95% −0.035 to +0.029) | 014 |
| choosing computations by value per dollar | beats attempting every clue, but level with a simple heuristic | 005, 006 |
| persistent re-proposal of the last slots | no gain: the slots it works on stay hard | 014 |

## How this compares
- **Darmok** (2026) solved the Times Crossword Championship final faster
  than its human winner, with an ensemble of frontier models. It has
  published no accuracy over a puzzle set and no cost, so there is no
  like-for-like number. Ours is on daily puzzles, with no time limit, and is
  reported with its cost and an interval.
- **Published single-clue work** (Andrews & Witteveen, ICML 2025: 32.5%
  top-1 on Cryptonite, with small open models and a Python verifier its
  authors show can be fooled) predates today's models, and uses a dataset
  those models have likely seen.

## What is distinctive
1. **The decomposition itself.** On contamination-free grids, calibration,
   not verification, is what a strong proposer was missing; crossing
   letters do most of the work. A cheap configuration matches the full
   machinery.
2. **A verifier that cannot be fooled, whose value is audit.** It admits
   none of ~3,000 mutant parses. It adds no accuracy here, but each answer
   it verifies names the judgements it rests on (a synonym, a definition)
   and the string operations that hold.
3. **Calibrated, selective answers.** On clean grids, committed answers
   are right 97.7–99.2% of the time. On single clues (Cryptonite, 2000–2020,
   so possibly seen by the models), answering only at P ≥ 0.9 covers 37.9%
   of clues at 96.8% accuracy (ECE 0.027).
4. **A contamination-aware protocol.** Post-cutoff puzzles defined by each
   model's knowledge cutoff, harvested without reading their content,
   grids reconstructed from clue lists, pre-registered fit/evaluation
   splits and decision rules, tables committed before evaluation (checked
   from git history), and evaluation grids read once.

## Caveats
- **n = 40 grids, and 20 for the simple solver.** Intervals are wide. The
  two samples differ (the full solver 10/20 then 7/20), which is within
  sampling noise for rates near 0.4.
- **Selection.** Only puzzles blogged on Fifteensquared, parsed completely
  and reconstructed uniquely; 61 posts were incomplete (a clue number with
  no row), mostly linked clues, which biases toward simpler grids. No Times puzzles.
- **Blind parser.** Rows were checked by mechanical invariants, not read.
- **One proposer family.** Only Anthropic models were tested; the
  remaining failures are answers never proposed, which other families may
  propose (planned, brief 015).
- **Costs** are API list prices for evaluation runs only, not development
  (~$245 across all briefs).
- **Data** cannot be shared (newspaper puzzles and blog content); the code,
  the protocol and every result's replay log can.
