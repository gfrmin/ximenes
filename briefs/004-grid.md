# Brief 004 — The grid: crossers as evidence

Headline number: on a seeded set of **20 reconstructed Cryptonite grids**
(see §2), the **fully-correct grid rate**, **letters correct**, and the share
of each solved grid that is *proven* vs *quarantined* (D4, D9); plus **spend
per grid**. The same CLI runs on post-cutoff grids when the author supplies
them, reported separately. Spend cap: **$25**.

## Why this brief is the first real test of D9
Until now every clue was solved alone. In a grid the agent's own hypotheses
constrain one another through shared cells: crossers are the third
confirmation (`docs/GAME.md` §3), and they come from the agent's own
computations, not from the environment. The posterior from brief 003 is
the prior each slot starts with.

## Build, in this order

### 1. `ximenes.grid`: the grid type and crossers
- `Grid(width, height, blocked: frozenset[cell])`, with slot numbering
  derived by the standard rule (a cell starts an across/down slot when it
  is open and the cell before it is blocked or off-grid, and the run is
  ≥ 2). Slots carry `(number, orientation, cells)`.
- Loader for **ipuz** (open JSON standard) and a tiny hand format for
  tests (rows of `#`/`.`). Crossers: for each slot, the list of
  `(cell_index, other_slot, other_index)`.
- Tests on a hand-made 5×5 and a 15×15 with 180° symmetry.

### 2. Grid reconstruction for Cryptonite puzzles (the data engine)
Cryptonite gives, per `(publisher, date)`, every clue's number, orientation,
enumeration and answer, but no layout. Reconstruct it: search 15×15
blocked grids with 180° rotational symmetry whose numbering and slot
lengths match the clue list **and whose crossing letters agree when the
known answers are filled in**. The letter check makes the search tight.
- Implementation: fill slots in numbering order; prune on length and on
  letter agreement; stop at the first two solutions (report unique /
  multiple / none).
- Run on a seeded 100 puzzles from the test-sample dates; report how many
  reconstruct uniquely, and the time. Layouts and answers stay local
  (`runs/grids/`), never committed; the report carries counts only.
- The 20 evaluation grids are the first 20 unique reconstructions in
  seed order, with ≥ 28 clues each. Note in the report that these mix
  Cryptonite splits (a puzzle's clues are spread over train/val/test), so
  the result is an upper bound; post-cutoff grids are the clean number.

### 3. Belief propagation over the `Hyp` relation
- Variables: one per slot, with domain = its candidate rows plus `OTHER`.
  Prior: the brief-003 posterior per candidate, and
  `P(OTHER) = max(1 − ΣP, floor_other)` with `floor_other` in `data/eval.json`
  (pre-register 0.05).
- Factors: one per crossing cell; two candidates agree if their letters at
  that cell match; `OTHER` is compatible with any letter (it is "a word we
  haven't proposed").
- Sum-product loopy BP for marginals (BCS-style; damping and iteration cap
  in `data/eval.json`), max-product for the MAP. Pure Python; tests on a
  3-slot toy where the exact answer is known.

### 4. The grid loop (`ximenes.gridsolve`)
1. Solve every slot independently with the brief-002 loop (m = 3, Sonnet
   formaliser, Haiku judges), replaying logs where a clue was already
   solved; score candidates with the committed posterior.
2. BP → marginals. **Commit** any slot whose top candidate's marginal
   ≥ τ = 0.9 (fixed; same τ as 003). Committed letters become hard
   evidence.
3. For each uncommitted slot where `OTHER` or an uncommitted candidate
   dominates, **re-propose with the pattern** (Haiku, k = 10, the pattern
   of committed letters in the prompt), then formalise/verify/judge the new
   candidates as in 002, and rescore. Order: the slot with the most
   committed crossers first (a stand-in for value of information; 005
   replaces it).
4. Repeat 2–3 until no slot changes, or three rounds, or the budget.
5. **Submit** the MAP. Record, per slot: committed at which round, status,
   reasons, marginal at submission; per grid: proven (every slot `Ok` and
   crossed) vs quarantined (names the oracle leaves it rests on), letters
   correct, clues correct, spend.

### 5. CLI
`python -m ximenes.gridsolve --grids runs/grids/ --n 20 --seed 20261021
[--backend stub --log …]`; per-grid summaries without clue text or answers
to `reports/004/`.

## Tests (tests/test_004_*.py)
- Numbering and crossers on the hand grids.
- Reconstruction recovers a hand-made 7×7 symmetric grid from its clue
  list and answers, uniquely.
- BP on the 3-slot toy matches exact enumeration; OTHER mass behaves.
- The loop is deterministic on replay; a stub fixture runs one small grid
  offline end to end.
- Committed letters are never overwritten in later rounds.

## Not in scope
Value-of-computation ordering and the time price (005). Any refit of the
posterior (needs a fresh held-out sample, D7). Changing the clue loop.

## Report
Headline table (20 grids): fully correct, letters correct, clues correct,
proven vs quarantined, rounds, spend per grid. Reconstruction stats
(unique / multiple / none over 100). The gain from crossers: top-1 on the
same clues solved alone (round 1) vs after BP and re-proposal. Which slots
stayed uncommitted and why. Supersessions, kit output, open questions,
probability complete.
