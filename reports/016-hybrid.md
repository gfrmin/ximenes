# Report — brief 016 (the hybrid: direct answers, repaired by the grid)

Status: **complete (2026-10-24).** Built by `opus`. Spend **$10.62** of
the $30 cap: $10.51 for the 40 direct calls and $0.10 for the hybrid's
escalation calls. The smoke replayed 015's logged D1 call on 014's grid
#1, so it cost nothing new. Phase 3 envelope: $30.43 of $60. Cumulative
across briefs 000–016: **$275.57**.

Set: **40 never-read post-cutoff grids** from 012's harvest. Seed
20261030, stratified by publisher (FT 17, Independent 14, Guardian 9).
The set excludes every grid 013, 014 or 015 read. The list was pinned in
`data/eval.json` (c81e555) before any grid was read and is checked
against the seed at run time. Each grid was read once.

## Headline numbers

| arm | **fully correct** | clues | $ / grid | crossing conflicts |
|---|---|---|---|---|
| (a) direct (015's D1, unchanged) | **35 / 40** | 0.996 | 0.263 | 0 |
| (b) hybrid (D's answers, calibrated, BP, Opus-high escalation) | **36 / 40** | 0.996 | 0.265 | 0 |

- **Paired:** both 35, only hybrid 1, only direct 0, neither 4.
- **Decision statistic (written before the data):** θ ~ Beta(1 + 1,
  1 + 0), **P(θ > ½) = 0.75**. That is the middle band: **D stays the
  default** (it is cheaper), both are reported, and `lead` chooses
  between more grids and closing the line. For continuity, 014's
  independent-Beta P is 0.63; it decides nothing.
- **Readouts:** the hybrid has its 36 already at $0.50 per grid. Every
  grid finished well under the $1.00 budget. Stops: 37 grids had every
  slot committed, 3 had no new candidates.
- **What BP changed:** the hybrid overturned 2 of D's 1,268 answers.
  - Wrong → right, 1 (an Independent grid; it becomes fully correct).
  - Right → wrong, 1 (a Guardian grid that was already imperfect; it
    ends with 2 wrong slots instead of 1).
  - So clues are equal at 0.996.
- **Calibration (ECE, 10 bins):**
  - D's stated confidence: 0.071 (015 on the dev grids: 0.074);
  - D's confidence through the 016 map: 0.004;
  - the hybrid's final marginals: 0.003.
- **D's replication:** 35/40 on these fresh grids, beside 30/40 on 015's
  dev grids. These are different grids, not paired; this decides
  nothing.

## D's misses on fresh grids

Each of the 5 grids D got wrong has **exactly one wrong slot**, as in
015. The wrong answers' stated confidences were 0.20, 0.50, 0.85, 0.85
and **0.90**. So 015's "no wrong answer at ≥ 0.9" does not hold exactly
on fresh grids: one of 5 sits at 0.9.

What the hybrid did with each:

| D's stated confidence | hybrid |
|---|---|
| 0.50 | repaired by escalation |
| 0.20 | left wrong after escalation found nothing new |
| 0.85 (Guardian) | left wrong, and BP also overturned a right answer in that grid |
| 0.85 | committed straight from its calibrated prior, so never escalated |
| 0.90 | committed straight from its calibrated prior, so never escalated |

The map is steep, mapping stated 0.85 to 0.991. With only 10 misses in
015's fit, it is the hybrid's limiting part: **it commits D's confident
mistakes before the grid can test them.**

## Smoke

On 014's grid #1, both arms cost $0.37 (the direct call, replayed). Every
slot committed from D's answers, so no escalation call was made.
Projection: ~$15 of $30, so (b)'s budget stayed $1.00. The smoke did not
exercise escalation live; the stub tests did, and the run then did.

## Choices I made where the brief was open

- **The calibration map** is 013's logistic, with stated confidence as
  the one feature and L2 = 10 chosen by leave-one-grid-out. It was fitted
  on the 1,207 slots of 015's D1 run (`data/hybrid-d-calibration.json`).
- **Round 1:** a slot's prior is D's answer at p, with OTHER = 1 − p.
- **After escalation:**
  - candidates must fit the current pattern;
  - each enters at 013's fitted vote posterior on its share;
  - D's answer keeps the larger of its p and that posterior;
  - OTHER = max(1 − Σ, 004's floor of 0.05).
- **Commits** are at the raw BP marginal ≥ 0.9, as in 014's
  frontier_calibrated.
- **Escalation order** is 014's persistence order (most known letters
  first). A repeat call with an unchanged pattern is free (memoized),
  which is what ends a slot after two idle passes.

## What was built

- **`ximenes.hybrid`:**
  - the split (`never_read`, `hybrid_split`);
  - the map (`map_rows`, `fit_map`, `calibrated`);
  - the `Hybrid` arm (round 1 from D, `variables`, `escalate`,
    `submission`);
  - one-grid scoring with overturn counts and readouts;
  - `p_paired`, the summary and decision, and the CLI.
- **`tests/test_016_hybrid.py`:**
  - the paired statistic against the brief's worked cases;
  - the seeded, never-read split;
  - confident right answers commit with no call;
  - a wrong, unsure answer is repaired by escalation;
  - the summary and its decision.

## Supersessions (D8)

None.

## Reproduce

```bash
uv run python -m ximenes.hybrid split
uv run python -m ximenes.hybrid fit-map     # data/hybrid-d-calibration.json
uv run python -m ximenes.hybrid run --smoke --log <015's D1 smoke log>
uv run python -m ximenes.hybrid run --max-usd 30    # run 20261024T155839Z-hybrid
```

The numbers are in `reports/016/summary.json`.

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
310 passed
== kit: GREEN
```

## Open questions (for `lead`)

1. **A middle-band result with a clear mechanism.** The hybrid can only
   help where D is unsure. Two of D's five fresh errors were stated at
   0.85–0.9 and committed before the grid could test them. A flatter map
   is the natural next variant. Examples are a lower commit threshold for
   D's answers, or BP over D's answers with no commits until escalation
   has looked. It would need fresh grids: 32 of the 72 never-read grids
   remain.
2. **D at 35/40 on fresh dailies** (30/40 on 015's dev grids) makes 017's
   harder puzzles the more informative next measurement.

## Probability complete

**0.85.** The run used the pinned grids, map and settings, cost a third
of its cap, and the rule was applied as written. Doubts: the map's form
(1 feature, 10 misses) was my reading of "same logistic form as 013";
and n = 40 cannot separate a one-grid gain.
