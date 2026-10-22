# ximenes: calibrated, auditable cryptic crossword solving (draft note)

*Draft, 2026-10-22. Numbers from `reports/` at commit 6c7f35b. Brief 014
will tighten the grid rate and settle the paired comparison; until then,
treat the comparison claims as provisional.*

## Result

On **20 Guardian, Independent and FT daily cryptics published 2 August to
22 October 2026** (after every model's knowledge cutoff plus a month), the
solver fills **10 grids fully correctly (50%; Beta posterior 95% interval
about 29–71%)**, gets **97.4% of clues** right (grid-clustered 95% interval
95.9–98.7%), at a mean **$0.90 per grid** in API calls. Answers it commits
to are right **99.2%** of the time (491 of 495).

## What the solver is
- **Propose:** Claude Opus 5.5 lists candidates for every clue, then
  re-proposes with the crossing letters it has (structured output only).
- **Verify:** each candidate's wordplay is written in a small typed DSL,
  parsed (never executed), and checked: string operations must hold and
  every clue word must be used exactly once. Steps that need judgement
  (synonyms, definitions, homophones) are named, not proved.
- **Decide:** a calibrated posterior per candidate (fitted on held-out
  data), belief propagation over the grid's crossings, and a
  value-of-computation policy that chooses which clue to work on next
  under a cost budget.

## How this compares
- **Darmok** (2026) solved the Times Crossword Championship final faster
  than its human winner with an ensemble of frontier models. No accuracy
  over a puzzle set or cost has been published, so there is no like-for-like
  number. Our result is on daily, not championship, puzzles, has no time
  limit, and is reported with its cost.
- **Published single-clue work** (Andrews & Witteveen, ICML 2025: 32.5%
  top-1 on Cryptonite with small open models and a Python verifier) uses
  older models and a dataset that today's models have likely seen.
- **A frontier-only baseline** on the same 20 grids (Opus + crossing letters
  + belief propagation, no verifier or posterior) gets 7/20 at $0.59 per
  grid. At equal spend the two are level (the full solver had 6/20 at
  $0.75); the full solver's advantage is that it keeps converting spend
  into accuracy after the baseline runs out of moves. Brief 014 tests this
  directly with both given the same persistent re-proposal.

## What is distinctive
1. **Soundness by grammar.** The verifier admits no mutant parse (0 false
   accepts over ~3,000 mutants), where the published verifier is shown by
   its authors to be exploitable.
2. **Calibration and audit.** Every committed answer carries a probability
   and the judgements it rests on. On the 20 grids, the solver's slot
   marginals have ECE 0.064 (0.013 on committed slots) against the
   frontier baseline's 0.177: the baseline is underconfident, commits 341
   slots to the solver's 495, and so runs out of crossing letters sooner. On single clues, answering only at
   P ≥ 0.9 covers 37.9% of clues at 96.8% accuracy (ECE 0.027).
3. **A contamination-aware protocol.** Post-cutoff puzzles defined by model
   knowledge cutoffs, a pre-registered fit/evaluation split, evaluation
   grids read once, and every table committed before evaluation.

## Caveats
- **n = 20 grids.** The rate's interval is wide; 014 adds 20 more.
- **Selection.** Only puzzles blogged on Fifteensquared, parsed completely
  and reconstructed uniquely; puzzles with linked clues are excluded
  (61 posts), which biases toward simpler grids. No Times puzzles.
- **Blind parser.** Rows were checked by mechanical invariants, not read.
- **The verifier adds little at decision time** once the proposer is strong
  (ablation: 0.975 vs 0.974 clues without its features). Its value here is
  audit and calibration, and possibly in choosing what to compute; not raw
  accuracy.
- **Costs** are API list prices for the evaluation runs only, not
  development (~$160 across all briefs).
- **Data** cannot be shared (newspaper puzzles and blog content); the code,
  the protocol and every result's replay log can.
