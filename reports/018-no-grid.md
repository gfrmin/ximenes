# Report — brief 018 (what the grid is worth to the model asked directly)

Status: **complete (2026-10-25).** Built by `opus`.

Spend: **$14.65** of the $15 cap.

| part | $ |
|---|---|
| smoke | 0.44 |
| run | 14.21 |

The lead raised the cap from $12 to $15 (6641139) before any result was
read. Phase 3 envelope: $55.10 of $60. Cumulative across briefs
000–018: **$300.24**.

**The set:** 015's 40 dev grids, cut **before launch** to the first 30 in
015's order (013's 20, then 014's first 10). The smoke projected $17.4
for 40 against the then $12 cap, and the brief says to cut to 30 by seed
order. All 30 finished; none was dropped by finish time. The run's guard
was $11.50, but spend reached $14.21. The guard is checked before each
call, and 8 calls were in flight at once.

## Headline number

**Opus asked directly with the clues only (no grid): 25 / 30 grids fully
correct.** On the same 30 grids, 015's D1 with the grid scored 24 / 30.

| arm (same 30 grids) | fully correct | clues | $ / grid | ECE (stated) | crossing conflicts |
|---|---|---|---|---|---|
| **(c) clues only**, `direct-clues-v1` | **25 / 30** | 0.992 | 0.47 | 0.080 | 6 (all in one grid) |
| (a) with the grid, 015's D1 (stored) | 24 / 30 | | 0.28 | 0.074 (all 40) | 0.05 per grid over 40 |

- **Paired:** both 21, only with-grid 3, only clues-only 4, neither 2.
- **Decision statistic (written before the data):** θ ~ Beta(1 + 3,
  1 + 4), **P(θ > ½) = 0.36**, the middle band. **The note reports the
  paired numbers without a claim.**
- **What this says:** at this n, the grid does not measurably help Opus
  asked directly. Told nothing about which slots cross, it solves as many
  grids clue by clue as it does with the grid. Its answers almost never
  disagree on a shared letter: 6 conflicting cells in 1 of 30 grids.
  What the grid buys is cost. Without it, the model thinks longer
  ($0.47 per grid against $0.28).

## Wrong slots

| arm | imperfect grids | wrong slots per imperfect grid | stated confidence of the wrong answers |
|---|---|---|---|
| (c) clues only | 5 | 1, 1, 1, 2, 2 | 0.05, 0.08, 0.30, 0.40, 0.60, 0.60, 0.85 |
| (a) with the grid | 6 | 1 each (015) | |

- (a)'s pattern is one wrong slot per imperfect grid. (c) has two
  imperfect grids with 2 wrong slots each.
- The one grid with crossing conflicts is one of those: the grid would
  have shown the model that two of its answers clash. That grid is among
  D1's fully correct ones.
- (c)'s misses are mostly low-confidence: 4 of its 7 wrong answers were
  stated at ≤ 0.4.

## Choices I made where the brief was open

- **`direct-clues-v1`** is `direct-grid-v1` with the grid paragraph
  removed. That paragraph is the sentence explaining the grid lines, the
  "Grid" header and the lines themselves. Everything else is word for
  word, including "Take as long as you need". It was pinned (bd8ce11)
  before any call, after a check that D1's logged call still replays
  unchanged.
- **The 30-grid cut** follows 015's order as the brief says; the last 10
  of 014's grids are not in it.

## What was built

- **`instruments.solve_grid(..., grid=None, prompt=...)`.** The input
  omits `grid` for the clues-only arm, so D1's replay key is unchanged.
- **`direct` arm `C`, `direct.vs_d1` and `--n`.**
- **Test:** arm C sends no grid lines and the clues-only prompt, and D1's
  input keys are unchanged.

## Supersessions (D8)

None.

## Reproduce

```bash
uv run python -m ximenes.direct run --arm C --smoke
uv run python -m ximenes.direct run --arm C --n 30      # run 20261024T172804Z-direct-C
uv run python -m ximenes.direct vs-d1 --run runs/20261024T172804Z-direct-C-anthropic-c5fc8993b67e4ceb99cce820a5fbec97.json
```

The numbers are in `reports/018/vs-d1.json`.

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
311 passed
== kit: GREEN
```

## Open questions (for `lead`)

1. **The grid's value to the direct call is cost, not accuracy, at
   n = 30.** The model reconciles answers well enough without being told
   about the crossings: 1 conflicting grid in 30. This fits 016 and 017,
   where external crossing-letter machinery added one grid each. The note
   can say supplying the structure didn't measurably change accuracy, but
   it made the call cheaper. That is a fact about this model and task, not
   a general claim.

## Probability complete

**0.85.** The prompt was pinned before any call, the cut was made by seed
order before launch, all 30 finished, and the rule was applied as
written within the raised cap. Doubts: n = 30 (the cap forced the cut),
and the guard overshoot ($14.21 against $11.50) stayed inside the cap
only because the lead had raised it.
