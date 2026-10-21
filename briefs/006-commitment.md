# Brief 006 — Commitment: calibrate the grid marginal, and the paired baseline

Headline number: on **10 fresh reconstructed grids** (seed 20261024), the
VOC policy with a **calibrated commit rule**: **committed-only grids**,
**committed slots and their accuracy** (must stay ≥ 0.99), and **clues
correct at the $0.94 budget**, against 005's uncalibrated commit rule on
the same grids (offline where the logs allow, else stated). Secondary:
the **paired crossers-first baseline** on 005's 10 grids. Spend cap:
**$20** ($10 + $10).

## Why
Briefs 004–005 commit a slot when its post-BP marginal ≥ 0.9. Committed
slots are right 99–100% of the time, but only ~27% of slots get committed,
and brief 003 found the clue posterior under-confident in its middle bins.
The marginal is probably under-confident too. If so, the cheapest lever on
commitment is a calibration map, fitted on grids we have already paid for.

## Build, in this order

### 1. Paired baseline (first, $10)
Run **P1 crossers-first** (004's heuristic, unchanged) on 005's 10
evaluation grids (seed 20261022) at the $0.94 per-grid budget, logging
per-move checkpoints as in 005. Add the paired row and curve to the 005
report under a dated "added in brief 006" heading. This is a comparison,
not a fit (D7).

### 2. Marginal calibration (free)
From the 8 fit grids' logs (seed 20261023): every slot's post-BP top
marginal at each checkpoint, paired with whether that top candidate was
right. Fit a monotone map `calibrated = g(marginal)` by pool-adjacent-
violators on the final-round checkpoints (one row per slot, so grids are
not over-weighted), with the reliability table committed as
`data/marginal-calibration.json` (bins, counts, accuracy) **before any
evaluation grid is read**. Report the fit grids' reliability by bin.

### 3. Calibrated commit rule
`commit if g(marginal) ≥ 0.9`. Nothing else changes: same posterior, same
OTHER tables, same BP, same gain model, same VOC chooser. Budget per grid
is pre-registered ($0.94); ρ is the stop rule only.

### 4. Evaluation ($10)
P4 with the calibrated rule on 10 fresh grids (seed 20261024). For the
uncalibrated comparison, rescore the same run's checkpoints offline with
the old rule (commitment is a function of the logged marginals, so no new
calls); state that both rows come from one run and that the policy's
*choices* were made under the calibrated rule.

## Tests (tests/test_006_*.py)
- The calibration map is monotone and its table sums to the fit grids'
  slot count; the fit refuses evaluation-seed grids.
- The commit rule is a pure function of (marginal, map); table of cases.
- Rescoring a logged run under either rule is deterministic and matches
  a replay.
- Committed slots are never overwritten (carried from 004).

## Not in scope
Synonym tables (007). Longer-horizon VOC. Any change to the clue loop,
posterior or gain model.

## Report
Headline table: calibrated vs uncalibrated commit rule on the 10 fresh
grids (committed-only grids, committed slots, their accuracy, clues and
letters at $0.94, spend). The fit grids' reliability table. The paired P1
row and curve on 005's grids, with one sentence on whether VOC beats the
heuristic at equal spend. Open questions, kit output, probability complete.
