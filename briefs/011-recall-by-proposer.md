# Brief 011 — Recall by proposer

Headline number: for each **proposer × prompt × pattern level**, on 150
fresh Cryptonite test clues, **gold-in-k** for k = 1, 3, 5, 10, all, and
**$ per clue**; plus the pre-registered pick for brief 012. Cap: **$40**
(estimate ~$25). Smoke test 10 clues per cell first and report its cost.

## Why
Brief 010's appendix: the gold answer is never among Haiku's 20 samples
for 33–39% of clues, and nothing downstream can recover it. Grids also give
the proposer crossing letters, which should raise recall sharply. Which
proposer, which prompt, and how much crossing letters help decide whether
full grids are reachable.

## Sample
150 clues from Cryptonite **test**, seed **20261026**, excluding the 1,000
clues of seed 20261021 (read in 000–003). Stratify by publisher as in the
post-cutoff protocol (Times/Telegraph proportional). Record clue year.

## Conditions (all `effort: low`, through `ximenes.instruments`, logged)
- **Proposers:** `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`.
- **Prompts:**
  - `sample`: the existing answer-only prompt, k independent samples
    (Haiku k = 20, Sonnet k = 10, Opus k = 5);
  - `list`: one call, "give up to 10 candidate answers that fit, best
    first, one per line" (new prompt `list-v1`); parse, normalise,
    enumeration-filter, de-duplicate in order.
- **Pattern levels:** `none`; `half`: about half the letters revealed, at
  the positions a grid's crossers would give (alternate cells of the
  answer, starting at a seeded offset), via the existing pattern prompt
  (and its `list` variant).
That is 3 × 2 × 2 = 12 cells. Ranking within `sample` is by vote share;
within `list`, by the model's order.

## Also report
- **Accuracy by clue year** (2000–04 … 2015–20) per proposer at pattern
  `none`, top-1: a contamination probe. A strong model that is much better
  on older clues is remembering, not solving.
- Enumeration-fail share and refusals per cell.
- Mean output tokens per call per cell (prices come from the logs).

## Pre-registered pick for brief 012
The cell that **maximises gold-in-5 at pattern `half`**, subject to
**≤ $0.06 per clue** for the proposal (so a 30-slot grid's proposals stay
under ~$2 and the $5/grid stop rule is reachable); ties within 2 points go
to the cheaper cell. Also report the best cell at pattern `none` for the
round-1 proposal, if different (012 may use one proposer for round 1 and
another for pattern re-proposal).

## The decision this brief informs, and an early stop
011 is the cheapest experiment that can settle the Phase 2 stop rule. A
30-slot grid is fully correct ≥ 10% of the time only if per-slot accuracy is
≥ ~0.93 (0.93³⁰ ≈ 0.11), and per-slot accuracy cannot exceed recall. Grid
slots see about half their letters by the time they are re-proposed, so
gold-in-5 at pattern `half` is an upper bound on what 012 can reach.
**Pre-registered:** if the picked cell's gold-in-5 at `half` is **< 0.85**
(95% interval from a clue-level bootstrap, reported), 012 runs **3 grids
only** as a confirmation and the project moves to the calibrated-assistant
product; if ≥ 0.85, 012 runs in full. Report the interval either way:
with n = 150 it is about ±4 points, so a result near 0.85 is reported as
ambiguous, and fable decides whether to buy 150 more clues.

## Tests (tests/test_011_*.py)
- Sample excludes seed 20261021's clues; stratification as stated.
- Pattern generation is deterministic and never reveals more than half.
- `list` parser: table of cases (numbering, blanks, duplicates, wrong
  length, extra text).
- Replay of the logged run reproduces every number.

## Not in scope
Formalising or verifying the candidates. Grids. Any change to the
posterior. Temperature (current models reject it).

## Report
The 12-cell table (gold-in-1/3/5/10/all, $ per clue); gold-in-k curves;
the pick, with the rule applied; year probe; enum-fail and refusals;
spend; kit output; open questions; probability complete.
