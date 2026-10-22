# Brief 014 — Close the last slots, paired against the frontier baseline

Headline number: on **20 fresh post-cutoff evaluation grids** (reserve,
seed **20261028**, stratified by publisher, disjoint from 013's 20 and fit
8), **fully correct grids** for three policies, **all with persistent
re-proposal**: the full solver, the frontier-only baseline, and the
frontier baseline **with the fitted vote-only posterior** (calibrated, no
verifier), at matched spend, with the
Beta posterior for each rate and for their difference. Pooled with 013 for
a 40-grid estimate of the full solver's rate. Cap **$72** for all of 014 (amended 2026-10-23 after the smokes: raw
`frontier` dropped from the paid run, since an underconfident arm burns its
budget under persistence and its calibration effect is already measured in
013's appendix; its grid-#1 smoke is reported as the illustration; fable).

## Why
013: 10/20 fully correct at $0.90 per grid. Every failed grid missed 1–3
slots whose gold was usually never proposed: VOC ran out of moves before
those slots had dense patterns. The baseline ran out of moves even sooner.
So the next lever is the same for both: keep working the last uncommitted
slots. Running it paired answers 013's open question at the same time:
once neither policy runs out of moves, does the full machinery beat
"Opus + crossing letters + BP" at equal spend?

## Build
1. **Persistent re-proposal** (both policies): when the policy has no move
   left and spend < budget, re-propose the uncommitted slot with the most
   known letters, with its full current pattern, escalating k (5 → 10 → 20)
   on repeats; then the Opus `list` prompt with the pattern as a fallback.
   Stop when every slot is committed, the budget is spent, or two passes
   over all uncommitted slots add no new candidate. All parameters in
   `data/eval.json` before any evaluation grid is read.
1b. **Third arm, `frontier+calibrated`:** the frontier baseline, but slot
   priors from `data/e2e-posterior-vote.json` and `e2e-other-prior-vote.json`
   (already fitted on the fit grids, no verifier features), so its marginals
   are calibrated and it commits like the full solver. No formaliser, no
   judges. 013's appendix showed the raw baseline is underconfident (ECE
   0.177) because proposer shares leave OTHER at a floor, and ablation (b)
   showed the vote-only posterior matches the full solver's accuracy on
   fixed candidates. This arm separates the two contributions: calibration
   (raw → calibrated) and the verifier (calibrated → full).
2. **Budget:** $3 per grid for every policy (013's dearest grid was
   $2.43). Report score at $1, $2 and $3 from the per-move checkpoints, so
   spend-matched comparisons are read from the curves, not one point.
3. **Tables:** unchanged from 013 (no refit; they were fitted on the fit
   grids, so a fresh evaluation sample is legitimate under D7).
4. **Done (013 appendix, `96f689b`):**
   calibration of the final slot marginals, full solver vs baseline: ECE
   (10 bins) and reliability tables over the 608 slots, and the same for
   committed-at-0.9 under each. If accuracy turns out level, calibration
   is the difference worth reporting, so it needs measuring either way.

## Tests (tests/test_014_*.py)
- Persistent re-proposal stops under each of its three conditions (table
  of cases); never re-proposes a committed slot.
- All three policies share the same budget and stopping parameters
  (asserted from the run records); `frontier+calibrated` calls no
  formaliser or judge.
- The reserve split for seed 20261028 is disjoint from 013's evaluation and
  fit grids.

## Not in scope
New models or prompts. Changing the verifier, posterior or gain model.
Linked clues.

## Report
Headline table (three policies × fully correct, clues, letters, ECE,
$/grid at $1/$2/$3); Beta(1,1) posteriors and the paired probabilities
P(full > calibrated) and P(calibrated > raw);
pooled 40-grid estimate for the full solver; by publisher; which slots
still fail and why; the 013 calibration appendix; spend; kit output; open
questions; probability complete.
