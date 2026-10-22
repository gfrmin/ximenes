# Report — brief 014 (close the last slots, paired)

Status: **complete (2026-10-22).** Built by `opus`. Spend **$84.50** of the
$90 cap: smoke tests $6.86 (three arms on grid #1), the first run $31.80 up
to the account limit, the resumed run $45.84. Cumulative across briefs
000–014: **$245.14**.

The data is 20 fresh post-cutoff grids from 013's reserve (seed 20261028;
FT 8, Independent 7, Guardian 5), disjoint from 013's 20 evaluation and 8
fit grids. As in 013, puzzles with linked clues are excluded (012).

## Headline numbers

Both arms use persistent re-proposal and a $3 per-grid budget. The pairs
are on the same 20 grids.

| arm | **fully correct** | clues | letters | $ / grid (mean, max) |
|---|---|---|---|---|
| **full solver** (verifier + fitted posterior + VOC, then persistence) | **7 / 20** | 0.946 | 0.952 | 2.22 (3.46) |
| **frontier + calibrated** (Opus + crossers + BP with 013's fitted vote posterior; no verifier, formaliser or judges) | **8 / 20** | 0.950 | 0.956 | 2.07 (4.41) |

Read from the per-move checkpoints, at equal spend:

| budget per grid | full solver: clues / fully correct | frontier + calibrated: clues / fully correct |
|---|---|---|
| $1 | 0.893 / 5 | **0.938 / 8** |
| $2 | 0.948 / 8 | 0.950 / 8 |
| $3 | 0.946 / 7 | 0.952 / 8 |

**Once confidence is calibrated, the verifier adds nothing to accuracy at
any spend.**
- **Paired fully-correct outcomes:** both 4, neither 9; only the full
  solver 3, only the calibrated frontier 4. Under Beta(1,1),
  P(full solver's rate > calibrated frontier's) = **0.375**.
- **Paired clue difference (full − calibrated):** −0.004, 95% bootstrap
  [−0.035, +0.029].
- **Cost:** the calibrated frontier reaches its 8 fully correct grids **by
  $1 per grid**; the full solver needs $2 for the same count.

**Pooled full-solver rate over 013 + 014: 17 / 40 = 0.43**, Beta(18, 24),
P(rate ≥ 0.10) > 0.999.

## What decomposes into what

Three steps, each measured on post-cutoff grids:
1. **Crossing letters + BP** carry the bulk. 013's ablation took the first
   candidate's 0.78 to 0.97 of clues.
2. **Calibration** is what the raw frontier lacks. 013's appendix measured
   ECE 0.177 against 0.064, with 341 commits against 495. On 014's grid
   #1 the raw frontier, with persistence, spent its whole $3.49 working
   slots it never committed, and finished no better: 0.969 clues, not fully
   correct. That is why fable dropped it from the paid run.
3. **The verifier**, on top of calibration, gives no measurable gain here.

## Persistence did not lift the full solver

013's full solver was 10/20 on its own grids at a mean of $0.90. 014's
grids look harder: the calibrated frontier also got only 8/20. With
persistence and $3 the full solver gets 7/20, and **8 at its $2
checkpoint**. In one grid, a late re-proposal's new candidates changed the
BP solution, so a fully correct grid at $2 became 1 slot wrong at $3. Nine
grids stopped on the budget and 11 on "no new candidates". The failures:
- **21 guessed slots wrong:** gold still not proposed after up to 20
  pattern samples and the list fallback;
- **11 committed wrong** (465/476 = 0.977, below 013's 0.992).

Persistence buys re-proposals on hard slots, and those slots stay hard.

**Budget overshoot:** the budget is checked before each move, so a grid
can end one move past $3. Two did: one persistence call cost $1.97 by
itself (Opus sampling 20 answers on a near-complete pattern), and another
$0.49.

## By publisher (fully correct)

| publisher | grids | full solver | frontier + calibrated |
|---|---|---|---|
| FT | 8 | 3 | 5 |
| Independent | 7 | 3 | 2 |
| Guardian | 5 | 1 | 1 |

## The stop and the resume

The first paired run stopped at 11:50 UTC when the Anthropic account
reached its usage limit (HTTP 400), at 014 spend $38.66. Two problems:
- The run JSON was written only after all grids, so the stop discarded
  every grid's result. Fixed (`e897e61`): a failing grid is now recorded
  as unfinished and the others are kept.
- The finished grids were recovered by stub replay (2 and 12).

The author raised the limit, and both arms resumed at 12:08 under the same
pinned parameters, replaying every logged call at no cost. fable raised the
cap from $72 to $90 during the resumed run, so that the full arm could
finish all 20 grids and the comparison stay paired. A guard would otherwise
have stopped it at $72.

## Amendments, in order (all before the paired run unless noted)

1. `2bd84ee`: parameters pinned: two arms, cap $50.
2. Smoke tests of `full` and raw `frontier` on grid #1 (started before the
   amendment landed; parameters unchanged by it; fable kept grid #1).
3. `0169955`: third arm `frontier_calibrated`, cap $65.
4. `2789d81`: arms reduced to `full` and `frontier_calibrated` (raw
   frontier smoke only), cap $72.
5. `8b7af4f` (during the resumed run): cap $90.

## What was built

- **`ximenes.last_slots`:**
  - `reserve_split` (seed 20261028, stratified, disjoint from 013);
  - the `Persistent` mixin: the uncommitted slot with the most known
    letters first, k 5 → 10 → 20, then the `list` prompt with the
    pattern; stops on all committed, budget, or 2 idle passes;
  - `PersistentSolver` (formalises new candidates);
  - `PersistentFrontier` (merges proposer shares);
  - `CalibratedFrontier` (013's fitted vote posterior and OTHER table,
    brief 005's top-m vote domain);
  - per-grid failure capture;
  - CLI.
- **`tests/test_014_last_slots.py`:** persistence stops under each
  condition and never re-proposes a committed slot; the arms share their
  budget and stopping parameters (from the run records); the reserve is
  disjoint.

## Supersessions (D8)

None.

## Reproduce

```bash
uv run python -m ximenes.last_slots split
uv run python -m ximenes.last_slots evaluate --policy full --max-usd 4 --log <earlier full logs>
uv run python -m ximenes.last_slots evaluate --policy frontier_calibrated --max-usd 4 --log <earlier logs>
# runs 20261022T120832Z-last-slots-{full,frontier_calibrated}-anthropic-*
```

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 25%]
........................................................................ [ 50%]
........................................................................ [ 75%]
......................................................................   [100%]
286 passed in 18.83s
== kit: GREEN
```

## Open questions

See `QUESTIONS.md` § Brief 014.

## Probability complete

**0.8.** Both paired arms ran on all 20 grids under pinned parameters, and
the result is reported straight even though it goes against the
machinery. Doubts:
- the arms were amended four times before the run, all recorded;
- a mid-run stop and resume, by replay, with unchanged parameters;
- overshoot past the budget by one move on two grids;
- a 20-grid comparison can't separate the two rates (P = 0.375).
