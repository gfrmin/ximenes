# Report — brief 010 (soft evidence: does hard commitment cost grids?)

Status: **complete (2026-10-22).** Built by `opus`. **Spend: $0** (offline
over logged candidates; no call was made). Cumulative across briefs 000–010:
**$103.18**.

## Headline numbers

Round-1 records of all 40 logged grids (004's 20, 005's 10 evaluation, 006's
10). Candidate sets are fixed (no re-proposal); priors are 003's committed
posterior with 005's OTHER tables; regimes and constants as pre-registered
in `data/eval.json` (`e453c2a`, before any grid was read).

| regime (40 grids) | clues | letters | fully correct grids |
|---|---|---|---|
| **hard** (clamp at marginal ≥ 0.9, repeat, decode) | **0.557** | **0.554** | 0 |
| **soft** (never clamp, decode final marginals) | **0.557** | **0.553** | 0 |
| **soft-annealed** (OTHER floor 0.05 → 0.02 → 0.01, messages carried) | **0.558** | **0.555** | 0 |

Paired by grid, mean difference with a 95% bootstrap interval (2,000 reps,
seed 20261022):

| difference | clues | letters |
|---|---|---|
| soft − hard | 0.000 [0.000, 0.000] | −0.0003 [−0.0011, +0.0003] |
| annealed − hard | +0.0008 [0.000, +0.0025] | +0.0009 [0.000, +0.0026] |

**On fixed candidates, hard commitment costs nothing.** Soft and hard enter
the same word in every one of the 1,176 slots. The letter differences come
from soft's per-slot decode, which can disagree at a crossing, and that
cell then counts as wrong. Annealing gains one slot, on one 006 grid.

## Why: decoding is not the bottleneck

| set | slots | solved in the log | gold among candidates | hard clamps (right) |
|---|---|---|---|---|
| 004 | 589 | 583 | 329 | 143 (141) |
| 005 | 292 | 290 | 179 | 83 (83) |
| 006 | 295 | 176 | 164 | 15 (14) |
| **all** | 1,176 | 1,049 | **672** | **241 (238)** |

Gold is among the round-1 candidates in 672 slots. All three regimes enter
it in 655–656 of them. The ceiling is candidate generation (57% of slots
have gold among the candidates), not how BP uses the evidence. At τ = 0.9,
round-1 clamps are right 238 of 241 times. The 3 wrong clamps didn't change
any other slot's entry: the crossers had either independent support or no
gold candidate to lose.

By slot class:

| class | slots | hard | soft | annealed |
|---|---|---|---|---|
| would-have-committed (hard clamps) | 241 | 238 | 238 | 238 |
| others | 935 | 417 | 417 | 418 |

Slots hard gets wrong that soft gets right: **0**; the reverse: **0**.
Annealed against hard: 1 and 0.

### Breakdown

| subset | grids | hard clues | soft clues | annealed clues | hard / soft / annealed letters |
|---|---|---|---|---|---|
| set 004 | 20 | 0.555 | 0.555 | 0.555 | 0.548 / 0.547 / 0.548 |
| set 005 | 10 | 0.605 | 0.605 | 0.605 | 0.597 / 0.597 / 0.597 |
| set 006 | 10 | 0.514 | 0.514 | 0.517 | 0.521 / 0.521 / 0.524 |
| Times | 28 | 0.512 | 0.512 | 0.513 | 0.515 / 0.514 / 0.516 |
| Telegraph | 12 | 0.663 | 0.663 | 0.663 | 0.643 / 0.644 / 0.643 |

No subset shows a difference larger than one slot per grid.

### Exploratory (not pre-registered): hard at lower thresholds

So where did brief 006's loss come from? On the same 40 round-1 records,
I clamped at the lower raw thresholds that 006's and 007's calibration
maps implied:

| clamp threshold (raw marginal) | clues | letters | clamps (right) |
|---|---|---|---|
| soft (no clamp) | 0.5573 | 0.5533 | — |
| 0.9 (pre-registered) | 0.5573 | 0.5536 | 241 (238) |
| 0.7 | 0.5590 | 0.5555 | 477 (466) |
| 0.576 (007's map) | 0.5599 | 0.5571 | 513 (497) |
| 0.514 (006's map) | 0.5599 | 0.5573 | 523 (504) |
| 0.4 | 0.5607 | 0.5582 | 534 (510) |

Even at 006's threshold, clamping on fixed candidates is at least as good
as soft: 19 wrong clamps, and no net loss. So brief 006's fall in clues
(0.658, against 005's 0.706) was not caused by clamped letters misleading BP.
It came from what a live run does after a wrong commit: it re-proposes
crossers under a wrong letter pattern (their new candidates are drawn to
fit it), and it stops spending moves on the committed slot. Neither happens
offline. The brief's question only covered clamping, and clamping is not
the cost.

## What was built

1. **Licence refactor** (QUESTIONS § 009 item 2): Wikipedia's entries are in
   `data/lexicon/abbreviations.wikipedia.json` with its CC BY-SA 4.0
   header, merged at load time (`data.abbreviation_origins`).
   `abbreviations.json` is back to hand + Deits + review (MIT). The merged
   table equals brief 009's (`tests/test_010_licence.py`).
2. **Regimes** in `ximenes.bp`:
   - `hard(variables, edges, tau)` clamps, repeats, then decodes, and also
     returns the clamped slots.
   - `soft(variables, edges)` never clamps.
   - `soft_annealed(priors, edges, floors)` runs one pass per OTHER floor,
     warm-starting each from the last pass's messages
     (`propagate_messages(init=...)`).
   - Helpers: `with_floor` and `decode` (per-slot argmax of the
     marginals; the best candidate stands in for OTHER, as in 004).

   All are pure.
3. **Offline evaluation** `python -m ximenes.regimes`.
   - It rebuilds each grid's round-1 state by replaying its run's log.
   - A slot whose solve calls are missing from the log (006's VOC solved
     176 of 295) keeps its vote candidates under the vote posterior and
     vote OTHER table, as 005's policies do.
   - It decodes under the three regimes and scores clues, letters and
     fully correct grids, with paired bootstraps by set and by publisher.
   - Output: `runs/010-regimes.json` (not committed: `runs/` is local).
4. **Tests** (`tests/test_010_*`):
   - The licence split.
   - On the 004 toy: soft = exact marginal decode = exact joint MAP; hard
     equals soft when no clamp is wrong; a constructed wrong clamp (B's
     marginal on OAK passes 0.9) makes hard lose A (OAT), which soft keeps
     (CAT).
   - The regimes are pure, and `with_floor` touches only OTHER.
   - Cell scoring counts a cell only when every entry through it agrees.

Pre-registration: the regimes, τ, floors, bootstrap reps and seed were
committed in `e453c2a` before any grid was read. The interval level (95%)
was added to `data/eval.json` in the working tree before the first
evaluation run and is committed with the evaluation.

## Supersessions (D8)

- `tests/test_001_lexicon.py::test_built_file_matches_build_script`: the
  build script now returns two tables (main, Wikipedia), and the test
  compares each with its file.
- `tests/test_009_abbreviations.py::_origin` (helper): reads origins merged
  over both files. This went in as `0395049`, after `cc03c6d` was pushed red;
  the commit pipeline took `tail`'s exit status instead of the kit's.
  Commits are now gated on the kit's own exit status.

## Reproduce

```bash
uv run python -m ximenes.regimes \
  --set 004 runs/grids 20 runs/20261021T180216Z-grid-anthropic-2d9c958d01f642379a2c4ba2cc915e07.jsonl \
                          runs/20261021T175538Z-grid-anthropic-02b66515005f419b9e7417abd939edc5.jsonl \
  --set 005 runs/grids-eval 10 runs/20261021T222245Z-attempt_all-anthropic-5023b624ac824ecf8cd3fc0737d778c2.jsonl \
  --set 006 runs/grids-006 10 runs/20261022T004857Z-voc-anthropic-44398809c32847f0bd528a67b6123cca.jsonl
```

## Appendix (2026-10-22): gold-in-k from logged vote samples

This was suggested by fable (QUESTIONS § 010 item 2) and costs $0. For each
clue, I ranked the distinct, enumeration-valid answers in its 20 logged
samples by vote count, breaking ties by first appearance as the solvers
do. gold-in-k is the share of clues whose gold answer is in the top k.
Grids use each slot's round-1 proposals.

| set | clues | k=1 | k=2 | **k=3 (m now)** | k=5 | k=10 | k=20 (all sampled) |
|---|---|---|---|---|---|---|---|
| 002 test | 1,000 | 0.471 | 0.573 | **0.616** | 0.655 | 0.671 | 0.671 |
| 003 val | 600 | 0.458 | 0.568 | **0.613** | 0.640 | 0.648 | 0.648 |
| grids 004 | 589 | 0.411 | 0.513 | **0.559** | 0.616 | 0.628 | 0.628 |
| grids 005 | 292 | 0.479 | 0.568 | **0.613** | 0.671 | 0.695 | 0.695 |
| grids 006 | 295 | 0.437 | 0.529 | **0.556** | 0.590 | 0.610 | 0.610 |
| grids, all 40 | 1,176 | 0.435 | 0.531 | **0.571** | 0.623 | 0.640 | 0.640 |

**Raising m buys little.** Going from 3 to 5 formalised candidates adds 3–6
points of recall, and formalising every distinct sample adds 4–8 points. For
a third to a half of all clues (33–39%), the gold answer is never among
the 20 samples. That is the gap, and only the proposer can close it, with a
different prompt, model, temperature or more samples. Formalising more of
the same samples won't. The grids' k=3 value (0.571) matches the
round-1 candidate count above (672 / 1,176), which checks the replay.

Built: `ximenes.recall` (pure `ranked`, `rank_of` and `curve`, plus a CLI
that replays the logs; output `runs/010-recall.json`, local) and
`tests/test_010_recall.py`.

```bash
uv run python -m ximenes.recall \
  --clues test runs/20261021T172614Z-solve-anthropic-9ca8198903824c5fa126b43805226321.json \
  --clues val runs/20261021T172307Z-solve-anthropic-3b6375173487443c80dd87654be574d0.json \
  --grids 004 runs/grids 20 <004 logs as above> --grids 005 ... --grids 006 ...
```

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 30%]
........................................................................ [ 60%]
........................................................................ [ 90%]
........................                                                 [100%]
240 passed in 17.78s
== kit: GREEN
```

## Open questions

See `QUESTIONS.md` § Brief 010.

## Is a live soft-evidence brief worth its spend?

**No, not as specified.** On fixed candidates soft and hard enter the same
words. Any live difference would come through re-proposal, so a live brief
should test re-proposal patterns (e.g. only letters from slots above a
higher bar, or patterns weighted by marginal), not clamping.

## Probability complete

**0.85.** Every build item and test exists, nothing was called, and the
constants were committed before any grid was read. Doubts:
- 6 of 004's slots and 119 of 006's fall back to vote candidates, because
  their solve calls aren't in the logs.
- "MAP of the final marginals" is read as the per-slot argmax of the
  sum-product marginals. On the toy that equals the exact joint MAP; on
  loopy grids it may not.
- The interval level was set after the pre-registration commit (though
  before any grid was read).
