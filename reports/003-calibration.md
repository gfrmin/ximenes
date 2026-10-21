# Report — brief 003 (calibrated posteriors and selective answers)

Status: **complete (2026-10-21).** Built by `opus`, same session as 000–002.
Spend: **$16.21** of the $20 cap: val smoke test $0.53, val solve $15.59,
test indicator rescoring $0.09.

## Headline numbers

The posterior was fitted on a fresh **val** solve (600 Cryptonite val clues,
seed 20261021, brief 002's loop unchanged) and committed (`87cbf74`) before
the **test** run was scored once. Test = brief 002's 1,000 clues (seed
20261021, clue dates 2000-10-18 – 2020-10-30), rescored only to add
`judge_indicator` scores. Run date 2026-10-21. Chosen model: **M2 logistic**.

| on test | coverage | accuracy |
|---|---|---|
| **posterior, P ≥ 0.9 (pre-registered operating point)** | **0.379** (379) | **0.968** |
| brief 002 rule (Ok, or Quarantine with every oracle score ≥ 0.5) | 0.505 (505) | 0.861 |
| posterior at the 002 rule's coverage | 0.505 | 0.933 |
| vote share ≥ 0.9 (brief 000) | 0.275 (275) | 0.858 |
| posterior at the vote band's coverage | 0.275 | 0.989 |
| everything (top-1 by highest posterior) | 1.000 | 0.562 |

- **ECE on test (10 bins, brief 000's function):** M2 logistic **0.027**,
  M1 binned 0.092. Val out-of-fold log-loss: M2 0.205, M1 0.342 (L2 chosen
  by 5-fold CV grouped by clue: 0.01).
- **The posterior beats vote share at every coverage:** its accuracy is ≥ the
  vote's at all 1,000 coverage levels. It ties on the 17 most confident clues
  (both 100% right) and is strictly higher from the 18th on.

### Risk–coverage on test (three lines)

| coverage | posterior (M2) | vote share | 002 rule |
|---|---|---|---|
| 0.10 | 1.000 | 0.930 | |
| 0.20 | 0.995 | 0.910 | |
| 0.275 | 0.989 | 0.858 | |
| 0.30 | 0.990 | 0.827 | |
| 0.40 | 0.958 | 0.740 | |
| 0.505 | 0.933 | 0.683 | **0.861** (its one point) |
| 0.60 | 0.853 | 0.628 | |
| 0.80 | 0.689 | 0.537 | |
| 1.00 | 0.562 | 0.460 | 0.552 (002's top-1) |

Full curves (all 1,000 points): `reports/003/test1000-posterior-eval.json`.

### τ table (M2 on test; τ not tuned)

| τ | point coverage | point accuracy | set rate | mean set size | truth in set | abstain |
|---|---|---|---|---|---|---|
| 0.5 | 0.516 | 0.922 | 0.026 | 2.23 | 0.654 | 0.458 |
| 0.7 | 0.460 | 0.950 | 0.015 | 2.07 | 0.733 | 0.525 |
| 0.8 | 0.434 | 0.954 | 0.012 | 2.25 | 0.833 | 0.554 |
| **0.9** | **0.379** | **0.968** | 0.020 | 2.15 | 0.850 | 0.601 |
| 0.95 | 0.327 | 0.982 | 0.026 | 2.08 | 0.885 | 0.647 |

Calibration by bin: slightly *over*-confident in the top bin (P ≥ 0.9: mean
0.979, accuracy 0.968) and *under*-confident in the middle (bins 0.2–0.8 are
right 0.06–0.13 more often than their mean confidence). Sets are rare,
because candidates' posteriors seldom split mass between two answers.

### M1 (binned) did badly at the top, and why

At τ = 0.9, M1 answers 2.9% of clues. Its cells were ordered by the weakest
judgement band, then the strongest, and smoothed with pool-adjacent-violators
along that order, a choice fixed before seeing val. That order pools
heterogeneous cells: e.g. a Quarantine with leaf band 3 and definition band 0
(406 val candidates, 9.6% right) is pooled up to 0.146 with five other cells.
Monotone smoothing in two dimensions needs a partial order, not a total one.
Not changed after seeing test; M2 was chosen on val anyway.

## The 31 answers brief 002 turned from right to wrong

(fable's question.) All 31 of brief 002's wrong choices get a posterior
**below 0.5** (range 0.02–0.49), so none would be answered at any τ in the
grid. On 18 of the 31, the posterior's own top candidate is the right one.
By brief 002's minimum-score bands, 20 of the 31 were < 0.5 and 11 were ≥ 0.5.
The posterior's other features (vote share, margin, definition score)
catch those 11.

## Unlisted indicators (`judge_indicator`)

625 uses of 487 distinct unlisted (operator, phrase) pairs across the val and
test solves. The 20 most frequent, each with how many times it was used:
insert: into (6) · reverse: bowled over (6) · delete_last: briefly (5) ·
insert: embraced by (5) · homophone: said (5) · remove: in (5) · initials:
originally (5) · homophone: listen to (4) · insert: consuming (4) ·
homophone: did you say (4) · half: not half (3) · first_letters: first (3) ·
insert: put in (3) · insert: interrupted by (3) · insert: welcoming (3) ·
insert: keep (3) · insert: visiting (3) · remove: having no (3) · anagram:
organised (3) · first_letters: beginning to (3).

These are candidates for the hand table, but only with a published source
(fable's rule); nothing was added.

## What was built

- **`judge_indicator`** (Haiku 5.5, memoised). The verifier now emits an
  `OracleLeaf` for an unlisted indicator (status unchanged). Indicator scores
  are kept out of brief 002's decision rule (`scores.indicator_min`), so the
  rescored test run chooses exactly what brief 002 chose.
- **`ximenes/hyp.py`:** the hypothesis relation's schema (slot, answer,
  parse_src, status, reasons, prov with token multiplicities, table hits
  and oracle calls, scores, posterior). `solve` writes it; `posterior` and
  `decide` read it.
- **`ximenes/posterior.py`:**
  - The pre-registered features, with missing scores as a flag plus 0.
    Labels are per candidate; the runner-up enters via `margin`.
  - M1 binned + PAV, and M2 L2 logistic fitted by Newton's method, pure
    Python.
  - CV grouped by clue; the model is chosen by out-of-fold log-loss.
  - `fit` raises `FitOnTest` for the test split.
- **`ximenes/decide.py`:** `act(posteriors, τ)`, a pure point/set/abstain
  function; `evaluate` (τ table, risk–coverage, ECE); a `fit` /
  `evaluate` CLI.
- **`ximenes.eval.ece_of` / `risk_coverage`:** one ECE function shared
  with brief 000 (same bins).
- **Tables:** `data/posterior-logistic.json` and
  `data/posterior-binned.json`, with counts and the val run id. A test
  refits them from the val log and checks equality (local).

## Supersessions (D8)

- `tests/test_002_solve.py`: the record helper builds Hyp-schema records
  (`scores.min_score`); both brief-002 replays pass
  `score_indicators=False` (their logs predate `judge_indicator`). Cases
  and expectations unchanged.

## Reproduce

```bash
export ANTHROPIC_API_KEY=$(secret-tool lookup service env key ANTHROPIC_API_KEY)
uv run python -m ximenes.solve --set val --n 600 --seed 20261021        # val solve
uv run python -m ximenes.solve --set test --n 1000 --on-conflict first \
    --log runs/20261021T165753Z-solve-anthropic-d3af91634788448084b4f4ca07a7a090.jsonl  # rescore
uv run python -m ximenes.decide fit --val runs/<val-solve>.json         # writes data/posterior-*.json
uv run python -m ximenes.decide evaluate --test runs/<test-rescored>.json
```

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 43%]
........................................................................ [ 87%]
....................                                                     [100%]
164 passed in 8.89s
== kit: GREEN
```

(In CI the tests that need local runs/ logs are skipped.)

## Open questions

See `QUESTIONS.md` § Brief 003.

## Probability complete

**0.8.** Every build step and test exists. The fit/test separation is
enforced in code and visible in the commit order (tables in `87cbf74`, test
scored after). The headline replays from committed tables and local logs.
Doubts: M1's smoothing choice; candidate-level modelling as a reading of the
brief (QUESTIONS.md); and the tables are still LLM-reviewed pending the
author's spot-check.
