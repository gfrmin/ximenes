# Brief 018: what the grid is worth to the model asked directly

**Status: open (2026-10-25, drafted by `lead`; the author approved the
measurement in `lead`'s chat the same day).** Cap **$12**, inside the
Phase 3 envelope ($40.45 of $60 spent). Builder: `opus`. This is the
closing measurement of ximenes: after it, the note is finalised and the
project closes as a documented control case (ROADMAP).

Headline number: on 015's **40 dev grids**, **fully correct grids for
Opus asked directly with clues only (no grid)**, paired against 015 D1's
stored results on the same grids (30/40, which had the grid).

## Why
015–017 showed that one high-effort call given the whole puzzle solves
~80% of grids, and that our external crossing-letter machinery adds
almost nothing on top (016, 017: one grid each). The open question is
whether that is because the grid does little, or because the model
already does the crossing-letter work itself when given the grid. The
answer decides what the note can say about *supplying the world* to a
frontier model, which is the question the author now cares about more
than crosswords.

## Arm
One arm, **(c) clues only**: `direct-grid-v1`'s prompt and settings
unchanged (Opus 5.5, high effort, structured output
`{slot: {answer, confidence}}`), with the grid lines removed and the
clue lines kept exactly as they are (number, direction, clue,
enumeration). The slot keys are the same, so scoring is unchanged. The
model is told only that it is a cryptic crossword; nothing about which
slots cross. Pin the prompt variant as `direct-clues-v1` in
`data/eval.json` before any call, and do not revise it after the smoke.

Paired comparison: (a) = 015 D1's stored per-grid outcomes on the same
40 grids (dev data; no new (a) calls).

## Smoke
014's grid #1 (not in the 40). Report cost. Projection over 40; if it
exceeds $12, run 30 grids by the first 30 of 015's seed order and say so
before the run.

## Report
- Fully correct grids, clues, $ per grid, ECE of stated confidences, and
  **crossing conflicts** (the slots' answers are scored against the real
  grid, so conflicts measure how often clue-by-clue answers disagree on
  a shared letter when the model is not told the letter is shared).
- The paired table against (a): both / only (a) / only (c) / neither.
- Decision statistic, as in 016: θ ~ Beta(1 + n_a, 1 + n_c) on the
  discordant grids, P(θ > ½).
- Per-grid wrong-slot counts for (c), beside (a)'s one-slot pattern.

## Decision rule (written before any data)
- **P(θ > ½) ≥ 0.8:** the grid is load-bearing even for a frontier
  model. The note says the model does the crossing-letter reconciliation
  itself once the world is supplied, and that supplying the world is
  the workflow's job; the next project is chosen from the
  "missing-world" class first.
- **P(θ > ½) ≤ 0.2:** the grid was never doing much; the model solves
  clues one by one. The note says so, and the next project should not
  assume that supplying structure helps a frontier model.
- **Otherwise:** report the paired numbers; the note states them
  without a claim.

**Both outer bands can occur.** With 15 of D1's 30 solved grids lost and
none gained, P ≈ 1; with 3 lost and 0 gained, P = 0.94. If (c) matches
(a) within one grid either way, the middle band results, and that too
is informative (the model needs no grid).

## Not in this brief
Fresh grids (the dev grids suffice: nothing is fitted, and the paired
baseline exists only there), any change to the prompt beyond removing
the grid lines, and any further solver work.
