# Report — brief 004 (the grid: crossers as evidence)

Status: **complete (2026-10-21).** Built by `opus`, same session as 000–003.
Spend: **$19.54** of the $25 cap: smoke grid $0.72, 20-grid run $18.82, about
$0.94 per grid.

## Headline numbers

Set: 20 Cryptonite grids reconstructed from their clue lists: the first 20
unique reconstructions with ≥ 28 clues, in seed order (seed 20261021),
from puzzles holding a clue of brief 002's test sample. Puzzle dates
2001–2019; 16 Times, 4 Telegraph. Run date 2026-10-21. **These grids mix
Cryptonite splits** (a puzzle's clues are spread over train/val/test), so
this is an upper bound; post-cutoff grids would be the clean number (none
supplied yet).

| 20 grids | value |
|---|---|
| **fully correct grids** | **0 / 20** |
| **letters correct** (mean per grid) | **0.733** |
| **clues correct** (mean per grid) | **0.712** |
| clues correct, each clue solved alone (round 1, top posterior) | 0.513 |
| clues correct, pure MAP (OTHER entered as a blank) | 0.550 |
| best grid | 0.938 letters, 0.938 clues |
| spend per grid | $0.94 |

**The gain from crossers:** +20 points of clues (0.513 → 0.712) and the
letters with them, from BP over the posteriors plus pattern re-proposal. By
publisher: Times 0.491 → 0.679 (letters 0.704), Telegraph 0.600 → 0.843
(letters 0.846).

### Proven, quarantined, guessed (D9; fable's accounting)

A slot is **guessed** if it was entered over OTHER or below τ = 0.9 at
submission. It is **proven** if `Ok` and every crossing slot is committed,
and **quarantined** otherwise (it names its oracle leaves).

| slot class (589 slots) | slots | slot-weighted | letter-weighted | accuracy |
|---|---|---|---|---|
| proven | 0 | 0.000 | 0.000 | — |
| quarantined | 222 | 0.377 | 0.372 | **0.991** |
| guessed | 367 | 0.623 | 0.628 | 0.542 |

- **Grids:** 0 proven, 0 quarantined-only, **20 with at least one guess.**
  Committed slots (marginal ≥ 0.9) are right 99.1% of the time; the grid fails
  on its guesses.
- **No slot is proven.** `Ok` needs fully mechanical wordplay (7.7% of gold
  parses in brief 001), and the chosen answers here are nearly all
  Quarantine.
- **Guessed slots are right 54.2% of the time,** far above chance, which is
  fable's signal that the OTHER floor (0.05) is too high: a guessed slot's
  best candidate is right more often than OTHER's mass says. For brief 005.
- **Why slots stayed uncommitted (367):** OTHER dominated, i.e. the MAP said
  OTHER (254); the best candidate stayed below τ (113). 18 grids used all 3
  rounds, 2 stopped early with no changes.

### A procedure change made after the first evaluation grid (disclosed)

On the smoke grid, which is the first of the 20, pure MAP put OTHER on 10
of 30 slots and blanked two answers that were right alone. Since OTHER isn't
a word and a blank scores 0 under the game's payoff (`docs/GAME.md`), the
loop now enters the candidate with the highest marginal where the MAP says
OTHER (`0354890`, agreed by fable). The pure-MAP score is reported above
(0.550) for comparison. Nothing else changed after seeing evaluation grids.

## Grid reconstruction (the data engine)

100 seeded puzzles that hold a clue of brief 002's test sample, searched at
15×15 (13×13 for Times Quick), with 180° symmetry, numbering, slot lengths
and crossing letters all required:

| outcome | puzzles |
|---|---|
| **unique** | **36** (24 Times, 8 Telegraph, 4 Times Quick) |
| multiple | 0 |
| none | 34 |
| node limit (200,000) | 30 (20 Telegraph) |

- **No reconstruction was ambiguous**: when a layout was found it was the only
  one, so letter agreement pins the grid. The median time for a unique
  puzzle was 1.6 s, and the run took 359 s in total.
- **Why "none":** 26 of 34 have a visible cause in the data: a missing clue
  number (Cryptonite dropped clues), a linked answer longer than the grid,
  or a "see …" clue. The other 8 are unexplained (perhaps one orientation of a
  number is missing, or the grid isn't symmetric).
- **Telegraph grids hit the node limit most;** a better variable order or a
  higher limit would recover more. With ~11,000 gap-free puzzles in
  Cryptonite, a 36% unique rate still gives thousands of real grids locally.

Layouts and answers stay in `runs/grids/` (local); `reports/004/grids20.json`
holds counts only.

## What was built

- **`ximenes.grid`:** `Grid`, standard numbering, crossers, symmetry, the
  ipuz and hand-format loaders, and `reconstruct` (entries placed in reading
  order, pruned on letters, boundaries, symmetry, unnumbered starts, and
  blocking every passed-over unknown cell). `python -m ximenes.grid
  reconstruct`. The puzzle loader (`data.load_puzzles`, `PuzzleKey`) reads
  all three splits.
- **`ximenes.bp`:** sum-product and max-product loopy BP over slots, with
  OTHER = max(1 − ΣP, 0.05), committed slots as hard evidence. It matches
  exact enumeration on a tree.
- **`ximenes.gridsolve`:** round-1 solve (brief 002's loop and brief 003's
  posterior) → BP → commit at marginal ≥ 0.9 → pattern re-proposal
  (`propose_pattern`, Haiku, k = 10; only when a slot's pattern gained
  letters, ordered by committed crossers) → repeat ≤ 3 rounds → submit the
  MAP, entering the best candidate over OTHER. D9 accounting per slot and
  grid.
- **Tests (`tests/test_004_*`):** numbering and crossers; 15×15 symmetry;
  ipuz; unique recovery of a hand 7×7; BP against exact enumeration; OTHER
  and hard evidence; an offline 5×5 grid (ordinary words, original clues)
  where crossers flip a wrong lone answer and a pattern re-proposal finds a
  missed word; exact replay; committed letters are never overwritten.

## Supersessions

None.

## Reproduce

```bash
uv run python -m ximenes.grid reconstruct                 # local, free; writes runs/grids/
export ANTHROPIC_API_KEY=$(secret-tool lookup service env key ANTHROPIC_API_KEY)
uv run python -m ximenes.gridsolve --n 20 --log <earlier solve logs...>
uv run python -m ximenes.gridsolve --n 20 --backend stub \
    --log runs/20261021T180216Z-grid-anthropic-2d9c958d01f642379a2c4ba2cc915e07.jsonl
```

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 40%]
........................................................................ [ 81%]
................................                                         [100%]
176 passed in 8.85s
== kit: GREEN
```

The 20-grid run replays offline slot for slot (all 20 grids identical).

## Open questions

See `QUESTIONS.md` § Brief 004.

## Probability complete

**0.75.** Every build step and test exists, the run replays exactly, and
reconstruction works well enough to supply the grids. Doubts: the OTHER
fallback was added after seeing the first evaluation grid (disclosed, with
the pure-MAP number); "re-propose only when the pattern gained letters" is my
reading of §4.3; and the grids mix Cryptonite splits, so the numbers are an
upper bound.
