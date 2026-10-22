# Report — brief 007 (commit-time calibration)

Status: **closed on the free refit (2026-10-22); paid runs not made.** The
brief's 0.99 bar and its τ = 0.9 commit rule are incompatible (below). The
author chose to skip the two live runs (~$18), on opus's and fable's
recommendation (`comms/…0530Z…bar-vs-tau`, QUESTIONS.md § Brief 007).
**Spend: $0.** Cumulative across briefs 000–007: **$103.18**.

## Headline

The calibration refitted on **commit-time** marginals (13,929 uncommitted
slot-steps from the 8 fit grids, seed 20261023; grouped 4-fold CV by grid)
is well calibrated out of fold. It commits (calibrated ≥ 0.9) from **raw
marginal 0.576**, where 006's final-state map committed from 0.514.

**On commit-time data, calibration cannot raise commitment while keeping
committed slots at ≥ 0.99.** A slot committed at calibrated P ≥ 0.9 is right
about as often as its P, so ~0.92–0.97 across the band it opens up. To reach
0.99 the threshold must be 0.99 on the calibrated scale, and on this curve
that admits only raw ≥ ~0.9, which is the uncalibrated rule again.

## The refit against 006's map

Held-out (grouped CV) predicted vs observed, by raw marginal:

| raw marginal | slot-steps | CV predicted | observed | 006's final-state map |
|---|---|---|---|---|
| 0.0–0.1 | 6,168 | 0.154 | 0.151 | 0.00–0.75 |
| 0.1–0.2 | 1,687 | 0.618 | 0.622 | 0.75–0.76 |
| 0.2–0.3 | 812 | 0.651 | 0.745 | 0.76 |
| 0.3–0.4 | 368 | 0.672 | 0.457 | 0.76 |
| 0.4–0.5 | 309 | 0.705 | 0.579 | 0.76 |
| 0.5–0.6 | 346 | 0.866 | 0.812 | 0.76–0.98 |
| 0.6–0.7 | 380 | 0.900 | 0.939 | 0.982 |
| 0.7–0.8 | 880 | 0.972 | 0.981 | 0.982 |
| 0.8–0.9 | 2,979 | 0.975 | 0.969 | 0.982 |

CV Brier score 0.112. Above raw 0.5, predicted and observed agree within
0.01–0.05. Below 0.5 the curve is non-monotone in the raw data (0.2–0.3 is
right more often than 0.3–0.5); PAV pools it, and none of it reaches the
commit threshold either way.

Compared with brief 006's evaluation grids (commit-time reliability 0.63 /
0.90 / 0.92 / 0.98 for raw 0.5–0.6 / 0.6–0.7 / 0.7–0.8 / 0.8–0.9), the refit
is closer than 006's map (0.76–0.98 / 0.98 / 0.98 / 0.98), but still a little
optimistic in 0.5–0.8.

The map and table are committed as `data/marginal-calibration-steps.json`
(`d303d42`), before any evaluation grid of seed 20261025 was read (none
was).

## What the closed runs would have shown

Predictable from the refit, so not bought:
- **Calibrated rule:** committed accuracy ≈ 0.93–0.96, missing the 0.99
  bar, with commitment up about as much as in 006.
- **Uncalibrated rule:** ~100% committed accuracy at ~27% commitment, as in
  004–005.

Brief 006 already measured where that trade lands at roughly 0.9 accuracy:
wrong commits are hard evidence, so clues fell (0.658, against 0.706 for
005's uncalibrated VOC on other grids). The design lesson (fable's note in
QUESTIONS.md) is that the issue is **hard** commitment, not the threshold.
A later brief can test soft evidence (never clamp; re-propose on patterns
weighted by marginal) offline on logged grids.

## What was built

- `ximenes.voc.step_rows` (one row per uncommitted slot-step, fit seed only)
  and `fit_marginal_calibration_steps` (PAV with grouped k-fold CV;
  `voc.calibration_folds = 4` in `data/eval.json`).
- `tests/test_007_refit.py`: fit-seed rows only, one per uncommitted
  slot-step; CV bins cover every row and folds never split a grid; the
  committed map is monotone.

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 33%]
........................................................................ [ 66%]
.......................................................................  [100%]
215 passed in 9.15s
== kit: GREEN
```

## Probability complete

**0.85** that closing 007 on the refit is correct: the brief's question is
answered by free data, the author made the spend decision, and the test
items that need evaluation runs ("committed before the first evaluation run
id", "same grids/seed/budget for both runs") don't apply, since no
evaluation run exists.
