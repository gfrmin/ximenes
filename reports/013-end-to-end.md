# Report — brief 013 (end-to-end grid solver on post-cutoff grids)

Status: **complete (2026-10-22).** Built by `opus`. Spend **$37.77** of the
$80 cap:
- fit: $14.79, of which $2.58 went on a sequential run I stopped and
  restarted in parallel (its calls replayed);
- evaluation: smoke $0.75 plus $17.28;
- frontier baseline: $4.95.

fable approved it (the author deferred to fable). Cumulative across briefs
000–013: **$160.64**.

The data is brief 012's Fifteensquared grids dated 2026-08-02 to 10-22:
after every model's knowledge cutoff plus a month, so these are clean
numbers. Puzzles with linked clues are excluded by construction (012), which
biases the set toward puzzles without them.

## Headline numbers

20 evaluation grids (seed 20261027; FT 8, Independent 7, Guardian 5), each
read once. The tables were refitted on 8 disjoint fit grids and committed
(`3fffd7b`) before the first evaluation run (`20261022T103224Z`).

| solver (same 20 grids) | **fully correct** | clues | letters | $ per grid (mean) |
|---|---|---|---|---|
| **full solver** (Opus proposals + verifier + posterior + BP + VOC, $5 budget) | **10 / 20** | **0.974** | **0.981** | **$0.90** |
| frontier-only (Opus proposals + crossing letters + BP; no verifier, no posterior) | 7 / 20 | 0.931 | 0.946 | $0.59 |

**Stop rule (≥ 10% fully correct at ≤ $5 per grid): passed by a wide
margin.**

- **Fully-correct rate:** 10/20. The pre-registered Beta(1,1) posterior is
  Beta(11,11), mean 0.50, and **P(rate ≥ 0.10 | data) > 0.999.** Per
  013's decision rule (continue if ≥ 0.5): **continue to 014+.**
- **Per-slot accuracy:** 0.974 (592 of 608), grid-clustered 95% bootstrap
  interval [0.959, 0.987].
- **Implied full-grid rate:** the mean over grids of acc^n is 0.445 at the
  pooled accuracy. With each grid's own accuracy it is 0.618: the grid's
  own share right, raised to its slot count, averaged. The observed 0.50
  lies between.
- **Committed slots:** 495 (3 proven, 492 quarantined), of which 491 are right (**0.992**).
- **Slot classes:**

| class | slots | right |
|---|---|---|
| proven | 3 | 3 |
| quarantined | 492 | 488 |
| guessed | 113 | 101 |

### By publisher

| publisher | grids | fully correct | clues | $ / grid |
|---|---|---|---|---|
| FT | 8 | 4 | 0.976 | 0.74 |
| Independent | 7 | 3 | 0.977 | 1.14 |
| Guardian | 5 | 3 | 0.966 | 0.84 |

### Score against spend (from the per-move checkpoints)

| budget per grid | $0.25 | $0.50 | $0.75 | $1.00 | $1.50 | $2.50 |
|---|---|---|---|---|---|---|
| clues | 0.806 | 0.844 | 0.920 | 0.946 | 0.969 | 0.974 |
| fully correct | 0 | 2 | 6 | 8 | 8 | 10 |

VOC's pre-registered ρ came out negative: no fit grid reached the $5
target. So every grid ran until it had no moves left, which happened well
below the budget: the dearest grid cost $2.43 and the median $0.74.

## The frontier-only baseline (paired)

Opus proposes, re-proposes with patterns, and BP resolves the crossings,
with the proposer's own shares as priors. The target was the full solver's
median spend ($0.74). It ran out of moves first, at a mean of $0.59.

| | full solver | frontier-only |
|---|---|---|
| fully correct | 10 | 7 (5 of them also full for the solver) |
| clues, paired difference (frontier − full) | | **−0.043**, 95% CI [−0.079, −0.012] |

**Read with care:** the solver ahead overall, but not at equal spend. The
full solver's own checkpoint at $0.75 is 0.920 clues and 6 full grids,
level with the baseline's 0.931 and 7 at $0.59. The machinery's advantage
is that it **can turn more spend into accuracy**: formalising more
candidates, more re-proposals as commits accumulate. The baseline runs out
of moves.

## Ablations (free, by replaying the evaluation logs)

| decision rule over the full solver's final candidates | clues | letters | fully correct |
|---|---|---|---|
| (a) proposer's first candidate per slot, no verifier, no BP | 0.777 | 0.761 | 0 |
| (b) BP with the vote-only posterior (no verifier features) | **0.975** | 0.981 | 9 |
| (c) full solver (verifier-feature posterior) | 0.974 | 0.981 | 10 |

**Given the candidates, the verifier's features add nothing measurable at
decision time** (b ≈ c). Crossing letters and BP do the work: 0.78 → 0.97.
Where the verifier may matter is earlier: VOC's choice of which slot to
formalise or re-propose uses the verifier-feature posterior. These
ablations can't separate that from the extra moves. The baseline suggests
the extra moves are the main thing.

## Post-cutoff recall next to 011 (publisher-confounded)

Round-1 Opus `list/none`, first candidate right: **0.777** on these 608
post-cutoff Guardian/Independent/FT slots, against 0.793 on 011's 150
Cryptonite Times/Telegraph clues. The difference mixes date with publisher
(post-cutoff protocol), so it is **not** a contamination gap. It does
suggest Opus's Cryptonite numbers are not inflated much by memory.

## Spend by instrument (evaluation run)

propose_pattern $6.77 · formalise_clue $5.59 · propose_list $5.42 ·
judges $0.25. Opus proposals are two thirds of the cost; the formaliser is
a third.

## The largest remaining loss

The 10 grids that failed missed 1–3 slots each, 16 slots in all:
- **12 guessed slots:**
  - 7 whose candidates were all `Quarantine`;
  - 5 with no formalised candidate at all.

  In both cases the gold answer was usually never proposed: no
  re-proposal pattern was dense enough before the moves ran out.
- **4 committed wrong:** committed slots are right 99.2% of the time.

The next lever is to keep re-proposing the last few slots with their full
crossing patterns instead of stopping when VOC's moves run out. It is cheap,
since a grid's last slots have most of their letters.

## What was built

- **`eval.postcutoff_grids`** (permission-gated, dated per model).
- **`ximenes.e2e`:**
  - `row_ok` (fable's parser invariants; 2 of 122 daily-cryptic grids
    dropped);
  - the seeded, publisher-stratified `split` (20 / 8 / 92);
  - `refit` (logistic posterior and vote posterior with leave-one-grid-out
    CV, OTHER by band for both, the gain model and ρ; refuses evaluation
    grids);
  - `FrontierRun` (the baseline);
  - `ablate` (replay-based);
  - grids run side by side (`grid_workers`);
  - CLI steps `split`, `fit`, `refit`, `evaluate`, `frontier` and `ablate`.
- **`policy.GridRun(proposer=...)`:** round 1 from Opus `list` (position
  shares ∝ 1/(rank+1), since a list has no vote counts) and re-proposal
  from Opus `sample` k = 5. Both use structured output. Without it, brief
  005's behaviour is unchanged.
- **Tables:** `data/e2e-{posterior,posterior-vote,other-prior,other-prior-vote,gain-model}.json`,
  fitted on 238 solved slots of the 8 fit grids. One fact for later: OTHER
  in the top band is 0 (all 139 such slots had gold among the candidates).
- **Tests** (`tests/test_013_e2e.py`):
  - the invariants;
  - the split is deterministic, disjoint and stratified;
  - refit refuses evaluation grids;
  - the list proposer's shares;
  - VOC stays within budget plus one move;
  - the baseline calls no formaliser or judge and respects its budget;
  - the tables were committed before the first evaluation run (git
    history);
  - **replay reproduces a headline grid exactly**. The full 20-grid stub
    replay also matched every submission and dollar.

## Supersessions (D8)

- `tests/test_000_postcutoff.py::test_only_eval_mentions_postcutoff`: adds
  `e2e.py`, which calls `eval.postcutoff_grids(allow_postcutoff=True)`.

## Reproduce

```bash
uv run python -m ximenes.e2e split
uv run python -m ximenes.e2e fit --max-usd 25                    # run 20261022T101840Z
uv run python -m ximenes.e2e refit --run runs/<fit run>.json     # data/e2e-*.json
uv run python -m ximenes.e2e evaluate --max-usd 6                # run 20261022T104011Z
uv run python -m ximenes.e2e frontier --run runs/<evaluation run>.json --log <evaluation logs>
uv run python -m ximenes.e2e ablate --backend stub --run runs/<evaluation run>.json --log <evaluation logs>
```

## Appendix (2026-10-22): calibration of the final slot marginals

Asked for by brief 014 item 4 (free, from 013's logs). Per slot, the
confidence is the top candidate's BP marginal at the step it was committed
(read before that step's commits), else its final marginal. ECE uses brief
000's 10 bins (`eval.ece_of`). Two of the full solver's 608 slots never had
a candidate, so they carry no marginal.

| | slots | accuracy of top | **ECE** | committed | committed right | ECE (committed) |
|---|---|---|---|---|---|---|
| **full solver** | 606 | 0.977 | **0.064** | 495 | 0.992 | 0.013 |
| frontier-only | 608 | 0.933 | 0.177 | 341 | 1.000 | 0.059 |

Reliability (bins with slots; confidence → accuracy):

| bin | full solver: n, conf, acc | frontier-only: n, conf, acc |
|---|---|---|
| 0.0–0.1 | 7, 0.03, 0.57 | 25, 0.04, 0.24 |
| 0.1–0.3 | 11, 0.17, 0.55 | 29, 0.21, 0.62 |
| 0.3–0.5 | 6, 0.42, 0.83 | 42, 0.40, 0.83 |
| 0.5–0.7 | 21, 0.61, 0.95 | 97, 0.58, 0.97 |
| 0.7–0.9 | 66, 0.78, 1.00 | 74, 0.79, 0.99 |
| 0.9–1.0 | 495, 0.98, 0.99 | 341, 0.94, 1.00 |

**The frontier baseline is badly underconfident.** Its proposer shares
leave OTHER at a 5% floor, so slots that are 97–100% right sit at
marginals 0.5–0.9 and never reach the 0.9 commit bar. It commits 341 slots
against the full solver's 495. Fewer commits mean fewer crossing letters,
and so fewer re-proposals with dense patterns: one reason it runs out of
moves early. The full solver's fitted posterior is well calibrated (ECE
0.064, and 0.013 on committed slots). This difference stands apart from
the equal-spend accuracy result, and it is the reason the verifier and the
fitted posterior earn their place. It also suggests a cheap fix for the
baseline (calibrate its shares) that 014 should not make, because 014
compares the policies as specified.

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 25%]
........................................................................ [ 51%]
........................................................................ [ 77%]
................................................................         [100%]
280 passed in 18.59s
== kit: GREEN
```

## Open questions

See `QUESTIONS.md` § Brief 013.

## Probability complete

**0.8.** Every build item and test exists, the tables were committed
before evaluation, the run replays exactly, and the stop rule passes
clearly. Doubts:
- ρ was degenerate (negative), so "VOC" here is "every move until none is
  left".
- The frontier baseline didn't reach its matched spend, because it ran out
  of moves.
- The parser was blind. A mechanical leak check found no answer in any
  clue text (0 of 608 as a capitals run; 9 hidden-word clues contain it
  naturally).
