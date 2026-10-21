# Report — brief 005 (which computation next: value of computation under a price)

Status: **complete (2026-10-22).** Built by `opus`, same session as 000–004.
Spend: **$18.49** of the $25 cap: smoke fit grid $1.17, 8 fit grids $7.61,
P0 on 10 evaluation grids $7.60, P4 VOC $2.11 (P4 replays P0's calls; a
policy's *accounted* spend counts every call it made, whoever paid first).
Cumulative across briefs 000–005: **$94.03**.

## Headline numbers

10 fresh reconstructed grids (seed 20261022; the first 10 unique with ≥ 28
clues, disjoint from 004's grids and the fit grids). Puzzle dates 2001–2019,
mixed Cryptonite splits (an upper bound, as in 004). Run 2026-10-22.

| clues correct (mean per grid) | at $0.50 | at $0.94 | at $1.105 (fit-set median spend) |
|---|---|---|---|
| **P4 value of computation** | **0.602** | **0.706** | **0.743** |
| P0 attempt-all-then-fill | 0.592 | 0.605 | 0.605 |
| vote-only floor (all proposals, $0.31) | 0.574 | 0.574 | 0.574 |

| letters correct | at $0.50 | at $0.94 | at $1.105 |
|---|---|---|---|
| P4 VOC | 0.599 | 0.701 | 0.749 |
| P0 attempt-all | 0.590 | 0.597 | 0.597 |
| vote-only | 0.585 | 0.585 | 0.585 |

**Did VOC beat the heuristic and the floor?** P4 beat P0 at every budget
from $0.45 up. The curves are level (within a point, P4 slightly behind at
$0.35–0.40) until P4's first re-proposals land, and then separate. P0
plateaus at 0.605 once it has solved every slot (~$0.79) and has nothing
left to buy; P4 keeps buying re-proposals and reaches 0.743 at $1.105. Both
clear the vote-only floor (0.574). The crossers-first heuristic (P1) was not
re-run on these grids (the optional $10 extra); 004 reported 0.712 clues at
$0.94 per grid on *different* grids, so P4's 0.706 at $0.94 is comparable
in level but not a paired comparison.

### Score-vs-spend (mean over the 10 grids, read from the per-move checkpoints)

| $ / grid | 0.30 | 0.40 | 0.50 | 0.60 | 0.70 | 0.80 | 0.90 | 0.94 | 1.00 | 1.105 | 1.20 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P4 clues | 0.578 | 0.581 | 0.602 | 0.619 | 0.637 | 0.657 | 0.692 | 0.706 | 0.723 | 0.743 | 0.747 |
| P0 clues | 0.574 | 0.589 | 0.592 | 0.599 | 0.605 | 0.609 | 0.605 | 0.605 | 0.605 | 0.605 | 0.605 |
| P4 letters | 0.587 | 0.588 | 0.599 | 0.607 | 0.631 | 0.650 | 0.689 | 0.701 | 0.724 | 0.749 | 0.752 |
| P0 letters | 0.585 | 0.593 | 0.590 | 0.593 | 0.598 | 0.600 | 0.597 | 0.597 | 0.597 | 0.597 | 0.597 |

Full curves, per grid and per move: `reports/005/policies.json`.

### Secondary

- **Committed-only grids (D9's practical target): 0 of 10 for both
  policies.** Committed slots were right **100%**: P0 83/83, P4 80/80.
  Grids fail on what they leave uncommitted.
- **Spend per grid:** P0 mean $0.79 (it stops when every slot is solved);
  P4 mean $0.98, median $1.05 (ρ was pre-registered for a $0.94 median on
  the fit grids; the evaluation grids ran ~10% over).
- **Seconds per grid** (sum of per-call wall seconds, i.e. sequential-
  equivalent): P0 991 s, P4 1,287 s.
- **P4's moves:** 265 solve, 127 repropose, 33 formalise_more. It solved
  265 of the 292 slots. The other 27 were committed through crossers, had no
  enumeration-valid vote, or weren't worth solving by the gain model (not
  separated here).

## The models (fitted on the 8 fit grids, seed 20261023, before any evaluation grid was read)

| move | events | mean Δ max marginal | price | seconds | L2 (grouped CV) |
|---|---|---|---|---|---|
| solve | 234 | +0.146 | $0.0145 | 22.5 | 0.1 |
| repropose | 113 | +0.153 | $0.0141 | 22.4 | 10 |
| formalise_more | 239 | −0.004 | $0.0061 | 9.1 | 10 |

- **Formalising the 4th and later vote candidates is worth nothing on
  average.** The gain model learns this and VOC rarely buys it.
- **ρ = 2.11:** the median fit grid, taking moves in order of predicted
  gain/price, reaches $0.94 at that ratio. The fit grids' own median spend
  under the fit loop was $1.105, which is the third reporting budget.
- **Vote-only posterior** (for slots not yet formalised; needed once
  `solve` became a move, fable `0aa84b7`): logistic on vote share, rank and
  winner, fitted on brief 003's val solve, with its own OTHER table.
  Committed `d149200`.

## Slot prior: OTHER from val (step 1)

P(gold outside the candidates | top-posterior band), from brief 003's val
solve, committed (`ef7f12a`) before any grid was read:

| band of top posterior | < 0.5 | 0.5–0.8 | 0.8–0.95 | ≥ 0.95 |
|---|---|---|---|---|
| clues (val) | 274 | 66 | 69 | 191 |
| P(OTHER) | 0.777 | 0.167 | 0.101 | 0.005 |

**Effect on 004's grids (offline, for the record):** clues 0.712 → 0.669,
letters 0.733 → 0.683; committed slots 222 → 174 (accuracy 0.991 → 0.989);
guessed 367 → 415 (0.542 → 0.535). **This comparison is confounded:**
offline rescoring can't make re-proposals the original run didn't make,
and the new prior commits less, which changes the patterns. So it measures
"new prior without its re-proposals", not the prior. The fresh-grid
headline above uses the new prior throughout.

## What was built

- **`ximenes.voc`:** OTHER prior fit (val only), `slot_prior`; per-kind
  ridge gain model (L2 by CV grouped by grid; `FitOnEvaluation` refuses
  evaluation-seed grids); `choose`, the myopic rule (Hay et al. 2012):
  largest predicted gain/price, submit below ρ or when nothing affordable is
  left; `preregister_rho`.
- **`ximenes.policy`:** proposals first (the floor); moves `solve`,
  `formalise_more`, `repropose`; BP, commits at τ = 0.9, and a checkpoint
  after every move (cumulative $ and seconds, and what would be submitted,
  so score at any budget is read from the log). Policies `vote`,
  `attempt_all`, `voc`, `fit`.
- **Speed without changing results:** a policy's solve calls are warmed
  concurrently through the in-run memo; spend is metered move by move, once
  per distinct call. Per-call seconds are now logged beside `cost`, and
  replays keep the original's seconds.
- **`ximenes.posterior.fit_vote`** (vote-only posterior);
  `gridsolve.solve_grid(prior=…)`; `gridsolve.offline()` for rescoring.
- **Tests (`tests/test_005_*`):** the OTHER table sums to 1 per band, is
  fitted on val and refuses test; the chooser as a table of cases (stop
  rule, budget, unmodelled kind); prices reproduced from events; the gain
  model refuses evaluation seeds; score-at-budget; the policy loop offline
  on the 5×5 fixture; both tables committed before the first evaluation run
  (git).
- **Replay:** two evaluation grids replayed offline under VOC give
  identical moves, spend and scores at every checkpoint.

## Supersessions

None. Brief 004's `solve_grid` default prior is unchanged, and its replay is
unaffected.

## Reproduce

```bash
uv run python -m ximenes.grid reconstruct --n 40 --seed 20261023 --out runs/grids-fit --exclude runs/grids
uv run python -m ximenes.grid reconstruct --n 45 --seed 20261022 --out runs/grids-eval --exclude runs/grids runs/grids-fit
export ANTHROPIC_API_KEY=$(secret-tool lookup service env key ANTHROPIC_API_KEY)
uv run python -m ximenes.policy --policy fit --grids runs/grids-fit --n 8          # writes data/gain-model.json
uv run python -m ximenes.policy --policy attempt_all --grids runs/grids-eval --n 10
uv run python -m ximenes.policy --policy voc --budget-usd 1.105 --grids runs/grids-eval --n 10 --log runs/<P0>.jsonl
```

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 36%]
........................................................................ [ 73%]
....................................................                     [100%]
196 passed in 8.97s
== kit: GREEN
```

## Open questions

See `QUESTIONS.md` § Brief 005.

## Probability complete

**0.75.** Every build step and test exists. The fitted tables were
committed before evaluation (checked by a test against git history), and
VOC replays exactly. Doubts: the vote-only posterior is a component the
brief didn't name (needed once `solve` became a move); P1 wasn't paired on
these grids; the OTHER-prior effect on 004 is confounded (stated); and ρ
overshot the target spend on evaluation.
