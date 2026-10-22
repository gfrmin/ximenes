# Brief 007 — Commit-time calibration, paired live

Headline number: on **10 fresh reconstructed grids** (seed 20261025), two
live VOC runs at $0.94 per grid that differ only in the commit rule:
**uncalibrated** (raw marginal ≥ 0.9, as in 004–005) and **commit-time
calibrated** (g(marginal) ≥ 0.9, g refitted below). Report, for each:
committed slots, **accuracy of committed slots (bar: ≥ 0.99)**, committed-only
grids, clues and letters correct. Spend: **~$18, two live runs; the author
approves before either starts.**

## Why
Brief 006's map was fitted on final-state marginals and applied mid-run,
where the same raw value is less reliable; it over-committed (0.895). The
specification was the error, not the idea. And 006 showed the uncalibrated
rule cannot be replayed offline, because the commits change the patterns
and so the re-proposals. Both rules therefore run live on the same grids.

## Build
1. **Refit (free).** From the 8 fit grids' logs (seed 20261023): one row
   per (slot, step) for every *uncommitted* slot at every checkpoint, label
   = whether its top candidate is right at the end. PAV on the raw
   marginal; reliability by bin with grouped (by grid) 4-fold CV error; the
   map and table committed as `data/marginal-calibration-steps.json`
   **before any evaluation grid is read**. Report the curve next to 006's.
2. **Two live runs** on seed 20261025, P4 VOC unchanged, budget $0.94,
   ρ as the stop rule, rule switched by a flag. Smoke one grid per rule
   first and report its cost.
3. **Commit-time reliability** on evaluation for both rules, by raw
   marginal band, as 006 reported it.

## Tests (tests/test_007_*.py)
- The refit reads only fit-seed logs and one row per uncommitted slot-step;
  grouped CV folds never split a grid.
- The map is monotone and committed before the first evaluation run id.
- Same grids, same seed, same budget for both runs (asserted from the run
  records).

## Not in scope
The synonym table (008). Any change to VOC, the posterior or BP.

## Report
The paired table; commit-time reliability for both rules; the refit
curve against 006's; one sentence on whether calibrated commitment clears
0.99 and, if it does, what it buys in clues correct at equal spend. If it
does not, say so plainly; 008 goes ahead either way.
