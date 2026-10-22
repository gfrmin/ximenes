# Brief 010 — Soft evidence: does hard commitment cost grids?

Headline number: on the **round-1 records of all 40 logged grids** (004's 20,
005's 10 evaluation, 006's 10), with the candidates each slot had after
round 1 and **no re-proposal**, clues and letters correct and fully correct
grids under three BP regimes: **hard** (clamp a slot when its marginal
≥ 0.9, as 004–006), **soft** (never clamp; MAP of the final marginals), and
**soft-annealed** (never clamp; damping and the OTHER floor fixed as
pre-registered below). **Spend: $0** (offline over logged candidates).

## Why
Briefs 006 and 007 showed that calibrating a *hard* commit cannot raise
commitment and keep accuracy: a wrong commit clamps its letters and
misleads every crosser. Soft evidence lets a wrong high-marginal slot be
pulled back by its crossers. It is the standard choice in BP crossword
solvers (Berkeley Crossword Solver submits the BP/local-search result,
never clamps mid-run). Isolating clamping from re-proposal is possible
offline because without re-proposal the candidate sets are fixed.

## Build, in this order
1. **Licence refactor** (QUESTIONS § 009 item 2): Wikipedia entries in
   `data/lexicon/abbreviations.wikipedia.json` with its CC BY-SA header;
   merged at load time; `abbreviations.json` back to hand + Deits. Tests
   unchanged in outcome (assert the merged table equals 009's).
2. **Regimes** in `ximenes.bp`: `hard(tau)`, `soft()`, `soft_annealed()`.
   Pre-register in `data/eval.json` before any grid is read: τ = 0.9;
   damping and iteration cap as in 004; annealed = three passes with the
   OTHER floor at 0.05, 0.02, 0.01 and the MAP after the last.
3. **Offline evaluation** over the 40 grids' round-1 candidate sets and the
   committed posteriors (003 clue posterior, 005 OTHER tables). Per grid:
   clues, letters, fully correct; per slot class (would-have-committed,
   others). Paired by grid, so report mean differences with a paired
   bootstrap interval.

## Tests (tests/test_010_*.py)
- On the 3-slot toy from 004, `soft` equals exact enumeration's MAP and
  `hard` equals it when no clamp is wrong; a constructed wrong clamp makes
  `hard` lose a slot that `soft` keeps.
- Licence refactor: merged table equals the 009 table; headers present.
- The regimes are pure functions of (candidates, priors, constants).

## Not in scope
Live runs. Re-proposal under soft evidence (that needs a live brief, and
only if this one shows soft ≥ hard). Changing the clue loop or posterior.

## Report
Headline table (three regimes × clues / letters / fully-correct grids),
paired differences with intervals, breakdown by publisher and by grid set,
the slots hard gets wrong that soft gets right and the reverse; the
licence refactor; kit output; open questions; probability complete. One
sentence on whether a live soft-evidence brief is worth its spend.
