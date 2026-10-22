# Report — brief 006 (commitment: calibrate the grid marginal, and the paired baseline)

Status: **complete (2026-10-22), with a negative headline.** Built by
`opus`, same session as 000–005. Spend **$9.15** of the $20 cap (approved by
the author): P1 baseline $0.57, calibrated evaluation $8.58. Cumulative
across briefs 000–006: **$103.18**.

## Headline numbers

10 fresh reconstructed grids (seed 20261024; first 10 unique with ≥ 28
clues; disjoint from every earlier grid set; mixed Cryptonite splits, so an
upper bound). P4 VOC at $0.94 per grid, run 2026-10-22.

| commit rule (same run) | committed-only grids | committed slots | accuracy of committed | clues @ $0.94 | letters @ $0.94 | spend / grid |
|---|---|---|---|---|---|---|
| **calibrated** (commit if g(marginal) ≥ 0.9) | 0 / 10 | **162 / 290 (0.559)** | **0.895** | 0.658 | 0.707 | $0.878 |
| uncalibrated, offline replay of the same moves | 0 / 10 | 18 / 290 (0.062) | 0.944 | 0.517 | 0.523 | $0.645 |

**The calibrated rule fails the brief's constraint.** Commitment doubled
(about 27% of slots in 004–005 → 56% here), but accuracy of committed slots
fell to **0.895, below the required 0.99.** A wrong commit is hard evidence,
which then misleads its crossing slots, so clues correct (0.658) is below
005's uncalibrated VOC (0.706 at $0.94), though on different grids.

**The uncalibrated row is not a fair comparison,** and should not be read as
"calibration helped". The brief expected it to be rescored from logged
marginals with no new calls. That holds for commitment, but under the old
rule fewer slots commit, so the crossing-letter patterns differ, and the
re-proposals those patterns trigger were never made. The offline replay
gives such a call nothing back (no samples), which cripples the old rule
(18 commits). Brief 005's VOC on its own grids (80 commits at 100%, 0.706
clues) is the better reference for the uncalibrated rule.

### Why calibration over-committed

Reliability of commits on the evaluation grids, by the raw marginal at the
moment of commitment (from a replay of the run with corrected recording;
the replay matches the live run on all 10 grids):

| commit-time raw marginal | commits | right | map's calibrated value |
|---|---|---|---|
| 0.5–0.6 | 27 | 0.630 | 0.76–0.98 |
| 0.6–0.7 | 29 | 0.897 | 0.982 |
| 0.7–0.8 | 24 | 0.917 | 0.982 |
| 0.8–0.9 | 52 | 0.981 | 0.982 |
| ≥ 0.9 | 30 | 0.967 | 1.000 |

The map is right for 0.8–0.9 but over-estimates 0.51–0.80 by 7–35 points.
The cause is a distribution shift built into the design. **The map was
fitted on final-state marginals** (one row per slot at its grid's last
checkpoint, as the brief specified), when crossers have mostly settled, and
**applied mid-run**, where the same raw marginal is less reliable. On the fit
grids, reliability over *all steps* (uncommitted slots at every checkpoint)
is 0.81 for 0.5–0.6, 0.94 for 0.6–0.7, 0.98 for 0.7–0.8, and 0.97 for 0.8–0.9.
That curve would have committed from about 0.7, close to what the
evaluation grids show. The 0.51–0.90 block's 56/57 rested on 57 final-state
slots.

### The fit grids' reliability table (committed `c9f9694` before any evaluation grid was read)

| raw marginal block | slots | right | calibrated |
|---|---|---|---|
| 0.000–0.004 | 22 | 0 | 0.000 |
| 0.006–0.009 | 9 | 1 | 0.111 |
| 0.010–0.026 | 16 | 2 | 0.125 |
| 0.030–0.040 | 6 | 2 | 0.333 |
| 0.040–0.077 | 16 | 9 | 0.562 |
| 0.085–0.128 | 12 | 9 | 0.750 |
| 0.129–0.509 | 25 | 19 | 0.760 |
| 0.514–0.896 | 57 | 56 | 0.982 |
| 0.896–1.000 | 71 | 71 | 1.000 |

234 slots from the 8 fit grids (seed 20261023).

## Paired baseline (item 1): crossers-first on 005's 10 grids

Added to `reports/005-metacomputation.md` under a dated heading. At $0.94
per grid: **VOC 0.706, crossers-first 0.693, attempt-all 0.605.** VOC is
ahead of the heuristic at every budget, but only by 1–3 points; on 10 grids
that is within noise. So VOC matches the heuristic and beats attempt-all.
Crossers-first's committed slots were right 89/89.

## A recording bug found and fixed

Checkpoints recorded each slot's top marginal *after* that step's commits,
so for a slot committed at that step the stored marginal could belong to a
different candidate. That broke the first commit-time analysis (it didn't add
up: 121 of 162 commits). Fixed: tops are read before the step's commits. It
did **not** affect the committed calibration table (refitting with the fix
gives the same blocks), nor any score, commit or move.

## What was built

- `ximenes.voc`: `fit_marginal_calibration` (PAV, fit-seed only),
  `calibrated`, `commit_rule` (pure).
- `ximenes.policy`: the commit rule as a parameter (`--calibrated`);
  `crossers_first` (004's heuristic under a budget); `replay_moves`
  (re-apply a logged move sequence under another rule); `--offline`
  (missing calls produce nothing); per-slot tops in every checkpoint; the fit
  policy writes the gain model only on a live run (a replay had rewritten it
  with last-digit float differences from summation order; restored).
- Tests (`tests/test_006_*`): monotone table that counts the fit slots;
  refuses evaluation seeds; the commit rule and step function as tables;
  crossers-first respects its budget (this caught a budget check that a text
  edit had silently not applied); replaying moves under the same rule
  reproduces a run; calibrated commits are never overwritten.

## Supersessions

None.

## Reproduce

```bash
uv run python -m ximenes.grid reconstruct --n 45 --seed 20261024 --out runs/grids-006 \
    --exclude runs/grids runs/grids-fit runs/grids-eval
export ANTHROPIC_API_KEY=$(secret-tool lookup service env key ANTHROPIC_API_KEY)
uv run python -m ximenes.policy --policy crossers_first --budget-usd 0.94 --grids runs/grids-eval --n 10 --log <P0, P4 logs>
uv run python -m ximenes.policy --policy voc --calibrated --budget-usd 0.94 --grids runs/grids-006 --n 10
uv run python -m ximenes.policy --policy replay_moves --moves-from runs/<calibrated>.json \
    --grids runs/grids-006 --n 10 --backend stub --offline --log runs/<calibrated>.jsonl
```

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 33%]
........................................................................ [ 67%]
....................................................................     [100%]
212 passed in 9.11s
== kit: GREEN
```

## Open questions

See `QUESTIONS.md` § Brief 006.

## Probability complete

**0.8 that the brief is correctly complete** (as a negative result). Every
item ran: the paired baseline, the calibration fitted and committed before
evaluation, the calibrated rule, and the evaluation. The headline is reported
straight: commitment up, accuracy below the 0.99 bar. The uncalibrated
comparison is weaker than the brief intended (offline replay can't make the
re-proposals), and I explain why rather than report it as a win.
