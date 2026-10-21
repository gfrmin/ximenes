# Brief 005 — Which computation next: value of computation under a price

Headline number: on **10 fresh reconstructed grids** (seed 20261022, first
10 unique with ≥ 28 clues), **clues correct at equal spend** for a
value-of-computation policy against attempt-all-then-fill, with the full
**score-vs-spend curve** for each, and the vote-only line (no verifier) as
the floor. Secondary: committed-only grids (D9), seconds per grid. Spend
cap: **$25** ($8 fit set + ~$17 evaluation).

## Why this is the `wald` question
Every observation in a grid comes from the agent's own computations
(`docs/GAME.md` §4). The decision is not *what* to answer but *what to
compute next*, and when to stop. Brief 004 chose "most committed crossers
first", a heuristic. This brief prices the moves and chooses by expected
gain per price, myopically (Hay et al. 2012), and measures what that buys.

## Build, in this order

### 1. Slot prior: OTHER from val (free)
From the 003 val solve: P(OTHER | max-P band) = rate at which the gold
answer is outside the m candidates, by band of the top posterior (bands
pre-registered as in 003). A slot's distribution: candidates share
1 − P(OTHER) in proportion to their posteriors. Commit the table as
`data/other-prior.json` before any grid is read. Rescore the 004 grids
offline with it and report the change (for the record; not the headline).

### 2. Price every move
From the logs: dollars (tokens × price table) and wall seconds per
instrument call. Moves, each with its price:
- `repropose(slot)`: pattern proposal (Haiku, k = 10) + formalise/verify/
  judge the new candidates (Sonnet + Haiku).
- `formalise_more(slot)`: formalise the next unformalised vote candidate
  (4th, 5th…) of a slot.
- `propagate`: BP, free.
- `submit`: terminal.

### 3. The gain model (fitted on 8 fit grids, seed 20261023)
Solve 8 fresh grids with 004's loop, logging every `repropose` and
`formalise_more` as an event with pre-state features (`max_marginal`,
`other_mass`, `committed_crossers / length`, `pattern_density`, `round`,
`n_candidates`) and the outcome Δ(max marginal of the slot). Fit a small
model of E[Δ max marginal | features] per move kind (linear or logistic on
the pre-registered features; choose by grouped CV, commit as
`data/gain-model.json`). Expected utility is Σ_slots max marginal
(expected clues correct under independence); the myopic value of a move is
its predicted Δ on that sum, propagation ignored.

### 4. Policies (same move set, same loop, same τ = 0.9)
- **P0 attempt-all-then-fill**: round-1 solve, propagate, submit. No
  re-proposal (Darmok's disclosed shape).
- **P1 crossers-first** (004's heuristic): numbers taken from the 004 run,
  on 004's grids, stated as such; a paired run on the 10 fresh grids is an
  optional extra ($10) if the author wants it.
- **P4 VOC**: at each step, the move with the largest predicted gain /
  price; stop when the best ratio falls below ρ or the grid budget is
  spent. Pre-register ρ from the fit grids so that median spend ≈ 004's
  $0.94 per grid; also run at a $0.50 budget.
- **vote-only** (free, from round-1 logs): the vote winner in every slot,
  no verifier, no propagation. The floor and the "price of the floor"
  comparison in `wald` terms.
Every policy logs cumulative $ and seconds after each move, so score at
any budget below the run's cap is read from the log.

### 5. CLI and runs
`python -m ximenes.gridsolve --policy {attempt_all,crossers_first,voc,vote}
--budget-usd … --grids runs/grids/ --n 10 --seed 20261022`. Smoke test one
grid per policy first. Fit grids and evaluation grids are disjoint seeds.

## Tests (tests/test_005_*.py)
- OTHER prior table sums to 1 per band and is committed before grid reads
  (a test checks the commit precedes the first evaluation run id in the
  report).
- Prices are reproduced from a log fixture.
- The gain model refuses evaluation-seed grids by construction.
- The VOC chooser is a pure function of (state, prices, model); table of
  cases, including the stop rule.
- Score-at-budget is read from the log and matches a replay.

## Not in scope
Changing the clue loop, the posterior or τ. Non-myopic planning. A
synonym table (next brief). Post-cutoff grids unless files appear.

## Report
Headline: clues correct at $0.94 and at $0.50 per grid for P0 and P4;
score-vs-spend curves (clues and letters) for P0, P4, vote-only; P1 from
004 for reference; committed-only grids per policy; seconds per grid;
spend per grid; the OTHER-prior effect on the 004 grids (offline). One
paragraph on whether VOC beat the heuristic and the floor, and at what
budget the curves cross if they do. Open questions, kit output,
probability complete.
