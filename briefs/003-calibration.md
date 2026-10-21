# Brief 003 — Calibrated posteriors and selective answers

Headline number: on brief 002's 1,000-clue **test** run, with a posterior
fitted on **val** only, the **risk–coverage curve**, and at the pre-registered
operating point **P ≥ 0.9: coverage and accuracy**, against two baselines on
the same curve: vote share (brief 000) and the brief-002 rule (505 at 0.861).
Also the posterior's ECE on test. Spend cap: **$20** (one val solve of 600
clues; nothing else paid).

## Why val, and why only once on test
Brief 002's numbers are on test. Fitting anything on them would turn an
evaluation into a training set. So: a fresh solve on 600 Cryptonite **val**
clues (seed 20261021; proposer live, since brief 000's log covers test
only), fit there, then score the existing test run from its log. Test is
read once, at the end, after the fitted model is committed.

## Build, in this order

### 1. `judge_indicator` oracle (before the val run)
`judge_indicator(phrase, operator, clue_text) -> score` on Haiku 5.5, effort
low, fixed JSON reply, memoised (D6). The verifier is unchanged: it still
reports `Quarantine(indicator)`; the score is attached in `solve.judged`
like the other leaves. Score the test run's unlisted phrases offline from
its log (`--rescore`), so test and val carry the same features. Report the
20 most frequent unlisted phrases.

### 2. The val solve
`python -m ximenes.solve --set val --n 600 --seed 20261021` with the 002
loop **unchanged** (m=3, Sonnet formaliser, Haiku judges). Smoke test 20
first; cap $20.

### 3. Features (pre-registered here; no others)
Per clue, for the chosen answer and the runner-up:
`status` (Ok / Quarantine / none), `definition_score`, `min_leaf_score`
(over synonym, homophone, indicator judgements), `n_oracle_leaves`,
`unreviewed_table` (flag), `vote_share`, `is_vote_winner`,
`candidate_rank`, `margin` (chosen's min score − runner-up's). Missing
scores are a flag plus 0, never imputed.

### 4. Two models, both auditable
- **M1 binned**: accuracy by (`status`, `min_leaf_score` band,
  `definition_score` band), bands pre-registered as
  [0, .5), [.5, .8), [.8, .95), [.95, 1]; monotone-smoothed within status.
  Its table is committed as `data/posterior-binned.json` with counts.
- **M2 logistic** on the features above, L2 strength chosen by 5-fold CV on
  val; coefficients committed as `data/posterior-logistic.json`.
Pick the one with the better val log-loss, say which, and report both on
test.

### 5. Decision layer (`ximenes.decide`)
Acts, as `life-agent` defines them but with the game's scoring:
- **point**: the top candidate, when P ≥ τ;
- **set**: the shortest prefix of candidates ranked by P whose mass ≥ τ
  (prefix-optimal); report set sizes and how often the truth is inside;
- **abstain**: when no prefix reaches τ within m candidates.
τ is not tuned: report the curve over τ ∈ {0.5, 0.7, 0.8, 0.9, 0.95}. The
headline is the τ = 0.9 row.

### 6. The `Hyp` relation (naming, not building)
The per-candidate records already are the hypothesis relation of
`docs/GAME.md` §5. Give them a stable schema in `ximenes/hyp.py`
(`slot`, `answer`, `parse_src`, `status`, `reasons`, `prov` with token
multiplicities, table hits and oracle calls, `scores`, `posterior`), and
make `solve` and `decide` read and write it. No cells, no propagation; that
is 004.

## Tests (tests/test_003_*.py)
- Fitting never reads test: the fit function takes a split name and
  refuses `test`.
- Both models are deterministic given val's log; replay reproduces them.
- The binned table's rows sum to val's n; the logistic fit reproduces its
  committed coefficients.
- `decide` is a pure function of a record plus τ (table of cases: point,
  set of size 2, abstain).
- ECE and risk–coverage computed by one function shared with brief 000
  (same bins), tested against a synthetic perfectly calibrated run.

## Not in scope
Grids and crossers (004). Changing the loop or its models. Any fitting on
test. Learned thresholds beyond the τ grid.

## Report
Risk–coverage curve on test with three lines (posterior, vote share,
002 rule as a point); the τ table (coverage, accuracy, set size, truth-in-set
rate, abstain rate); ECE of M1 and M2 on test; val log-loss of both; the
unlisted-indicator list; spend; supersessions if any; kit output; open
questions; probability complete. One sentence on whether the posterior
beats vote share at every coverage, or only some.
