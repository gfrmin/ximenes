# Brief 013 — End-to-end grid solver on post-cutoff grids

Headline number: on **20 post-cutoff grids** (from 012's unique
reconstructions; evaluation seed **20261027**, stratified by publisher),
the **share fully correct**, clues and letters correct, proven /
quarantined / guessed slots, and **$ per grid**, against the
pre-registered stop rule: **≥ 10% fully correct at ≤ $5 per grid**.
Cap **$80** (raised from $60 on 2026-10-22 after the fit smoke, within the
Phase 2 envelope; fable).

## The solver (everything from Phase 1, with 011's proposer)
- **Round 1:** Opus 5.5 `list/none` (structured output) for every slot.
- **Re-proposal:** Opus 5.5 `sample/half` style (k = 5, structured output)
  with the slot's current letter pattern, whatever its density.
- **Verify / judge:** brief 002's formaliser (Sonnet 5.5) and Haiku judges,
  unchanged; abbreviation and indicator tables as of 010.
- **Beliefs:** a slot posterior and OTHER table **refitted for the new
  proposer** (features as 003), BP as 004, commit at marginal ≥ 0.9.
- **Policy:** brief 005's VOC with a gain model **refitted for the new
  proposer**, budget **$5 per grid**, ρ as the stop rule below budget.

## Data split (DESIGN D7, as amended)
012's unique post-cutoff grids are split by seed **20261027**: 20
evaluation grids (stratified by publisher), up to 8 **fit** grids, the rest
reserved. Fit grids are used only to refit the posterior, OTHER table and
gain model; those tables are committed before any evaluation grid is read.
The evaluation grids are read once.

## Build, in this order
1. Proposer swap in `ximenes.gridsolve` / `policy` (cell names from 011).
2. **Fit run** on the fit grids under the fit policy (all moves logged, as
   005), then refit: slot posterior (logistic, grouped CV by grid), OTHER
   by band, gain model per move kind. Commit all three.
3. **Smoke** one evaluation grid; report its cost. Then the 20.
4. **Free ablations from the same logs** (no new calls): (a) vote-only /
   list-order decisions without the verifier; (b) the same with BP but no
   verifier features. They answer whether the verifier still earns its cost
   now that the proposer is strong.
5. **The frontier-only baseline (the Darmok shape), paired, same 20 grids:**
   Opus proposes every slot, re-proposes with patterns, crossers resolve by
   BP, no formaliser, no judges, no posterior refit; spend matched to the
   full solver's median per grid. This is the comparison a reviewer will ask
   for first: does the machinery beat "a strong model plus crossing
   letters" at equal cost? Report it in the headline table. Its calls are
   mostly in the logs already; budget the rest inside the cap.

## Reading the stop rule with 20 grids (pre-registered)
Twenty grids give a coarse rate, so report, besides the observed share:
- the posterior for the fully-correct rate under a uniform Beta(1, 1)
  prior, and **P(rate ≥ 0.10 | data)**;
- per-slot accuracy with a grid-clustered bootstrap interval, and the
  full-grid rate it implies (mean over grids of the product of per-slot
  accuracies, using each grid's slot count).
**Decision:** continue to 014+ if P(rate ≥ 0.10) ≥ 0.5; stop chasing full
grids if it is < 0.2; in between, run 20 more evaluation grids from the
reserve (seed 20261028) before deciding, if spend allows.

## Tests (tests/test_013_*.py)
- Split is deterministic; fit and evaluation sets are disjoint; the refits
  refuse evaluation grids and are committed before the first evaluation
  run id (git-history check as in 005).
- The policy never exceeds the per-grid budget (from checkpoints).
- Replay reproduces the headline.

## Not in scope
New prompts or models beyond 011's cells. Any change to the verifier.
Further harvesting beyond 012's set.

## Report
Headline table and the stop-rule verdict; per publisher; score-vs-spend
curves; slot classes; the two ablations; post-cutoff recall of the round-1
and re-proposal cells next to 011's Cryptonite figures (labelled
publisher-confounded); spend by instrument; kit output; open questions;
probability complete. If the stop rule passes, one paragraph naming the
largest remaining loss (which slots fail, and at which step).
