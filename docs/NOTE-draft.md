# ximenes: a frontier model solves most cryptic crosswords when simply asked (draft note)

*Draft, 2026-10-25, rewritten by `lead` after briefs 015–018. Numbers
from `reports/` 013–018. Every number replays bit for bit from its logs.
Publishing it is the author's decision.*

## Result

**Claude Opus 5.5, given the whole puzzle in one call at high effort,
filled 93 of 116 post-cutoff cryptic grids fully correctly (80%; Beta
posterior 95% interval about 72–86%), at about $0.27 a grid.** Its
answers were 99.2–99.6% of clues right.

| set (post-cutoff, Aug–Oct 2026) | fully correct | 90% interval | $ / grid | brief |
|---|---|---|---|---|
| Guardian, Independent, FT dailies (grids our solver had read; the model had not) | 30 / 40 | | 0.28 | 015 |
| Guardian, Independent, FT dailies, never read | 35 / 40 | | 0.26 | 016 |
| Times dailies | 16 / 20 | [0.62, 0.90] | | 017 |
| Telegraph Toughies | 12 / 16 | [0.54, 0.88] | | 017 |
| **hard pooled (Times + Toughie)** | **28 / 36** | [0.64, 0.87] | 0.27 | 017 |

- **Hard puzzles cost it little:** 78% on Times and Toughie grids against
  75% and 88% on the two daily sets.
- **It does not need to be told the grid.** Given the clues alone, with
  nothing about which squares cross, it filled 25 of 30 dev grids
  against 24 of 30 with the grid (paired: 4 only without, 3 only with;
  P = 0.36, no claim). Its clue-by-clue answers disagreed on a shared
  letter in 1 grid of 30. What the grid buys is thinking time: $0.28 a
  grid with it, $0.47 without (018).
- **When it fails, it fails by one slot.** Each of its 23 imperfect
  grids had exactly one wrong answer. Its stated confidence on those
  answers was mostly below 0.9 (20 of 23), so its own confidence flags
  most of its errors.
- **The bespoke solver we built first did worse.** Over five briefs it
  grew to a sound wordplay verifier, crossing letters, belief propagation,
  a fitted posterior and value-of-computation search. It solved 17 of
  the same first 40 grids (43%) at $0.90–2.22 a grid. Paired, the direct call
  was fully correct on 15 grids the solver missed, and the solver on 2
  the direct call missed (P(direct better) = 0.998).

## What the machinery adds on top of asking directly

The hybrid feeds the direct call's answers, with calibrated
probabilities, into crossing letters, belief propagation and
high-effort re-proposal of uncertain slots. It costs under a cent a grid
more.

| | accuracy | calibration (ECE) | evidence |
|---|---|---|---|
| direct call, stated confidence | 35/40 dailies, 28/36 hard | 0.067–0.071 | 016, 017 |
| hybrid | 36/40, 29/36 (one grid more each time, never one fewer) | **0.002–0.003** | 016, 017 |

- **Accuracy:** each pre-registered paired test landed in its middle
  band (P = 0.75 each). By the rules written beforehand, the direct call
  stays the default and the hybrid is not claimed as an accuracy gain.
- **Calibration** is the measured contribution: the hybrid's
  probabilities are close to exact.
- **Its limit** is known: a steep calibration map commits the direct
  call's confident mistakes before the crossing letters can test them
  (6 of 8 misses in 017).
- **One grid in forty is inside the noise.** Two near-identical
  conditions in 018 (the same call with and without the grid) disagreed
  on 7 of 30 grids for a net difference of one. A one-grid edge,
  however consistent, is not evidence of an effect at this n.

## What we learned on the way (briefs 000–014)
- **Crossing letters and belief propagation** took the same candidates
  from 0.78 to 0.97 of clues right (013) when the proposer worked clue
  by clue at low effort. Given the whole puzzle at high effort, the
  model needs neither: it reaches 0.992 of clues with the grid and
  without it (018).
- **Calibration, not verification,** was what a model proposing clue by
  clue lacked: raw shares were underconfident (ECE 0.177), and a fitted
  posterior fixed it (014).
- **The sound-by-grammar verifier** admits none of ~3,000 mutant parses
  and names what each verified answer rests on, but added no accuracy
  over a calibrated frontier (014: 7 vs 8 of 20, P = 0.375). Its value
  is audit.
- **Depth beats breadth.** On slots the solver never cracked, one
  high-effort call put gold in its top 5 on 12 of 17; five low-effort
  samples managed 6 (015).
- **The lesson for method** (`docs/METHOD.md`): measure the strongest
  simple baseline (the model given the whole problem, allowed to think)
  before building. We measured it at brief 015, and it outperformed
  everything built before it.

## How this compares
- **Darmok** (2026) solved the Times Crossword Championship final faster
  than its human winner with an ensemble of frontier models. It
  published no accuracy over a puzzle set and no cost. Our numbers suggest
  most of that capability is the frontier model itself: one call solves
  about four Times dailies in five. We have not measured championship
  puzzles or time.
- **Published single-clue work** (Andrews & Witteveen, ICML 2025: 32.5%
  top-1 on Cryptonite, small open models, a verifier its authors show can
  be fooled) predates today's models and uses a dataset they have likely
  seen.

## What is distinctive
1. **Clean, priced, pre-registered numbers.** Post-cutoff puzzles
   defined by each model's knowledge cutoff plus a month, harvested
   without reading their content; evaluation grids read once; decision
   rules, splits and tables committed before the data (checked from git
   history); every denominator, the prompts
   (`src/ximenes/prompts.py`) and the cost of each run.
2. **A negative result about bespoke machinery,** measured paired: the
   model asked directly beats the solver built around it, and the
   machinery's lasting value is calibration and audit.
3. **A verifier that cannot be fooled,** whose value is explanation,
   not accuracy.

## Caveats
- **n = 116 grids** for the headline, 76 of them never read before (016,
  017); 018's 30 are dev grids re-read for a paired secondary.
  Intervals are given.
- **Selection.** Only puzzles blogged (Fifteensquared, Times for the
  Times, Big Dave's), parsed completely and reconstructed uniquely;
  linked-clue puzzles and barred grids are excluded, which biases toward
  simpler grids.
- **Blind parser.** Rows were checked by mechanical invariants, not read.
- **One model family.** Only Anthropic models; Fable 5.1 was smoke-tested
  only (its cutoff left too few grids).
- **No time limit,** and no championship puzzles.
- **Costs** are API list prices for evaluation runs; development across
  all briefs was $300.24.
- **Data** cannot be shared (newspaper puzzles and blog content); the
  code, the protocol and every result's replay log can.
