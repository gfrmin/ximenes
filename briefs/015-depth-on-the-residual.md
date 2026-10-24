# Brief 015: depth on the residual

**Status: drafted 2026-10-24 by fable. Waiting for the author's Phase 3
envelope (proposed $60). Do not start paid calls until ROADMAP's Spending
section shows it.**

Headline number: on the **stuck slots** of 013 and 014 (the slots where the
gold answer was never proposed), **gold-in-5 per proposer arm**, with
Beta posteriors and $ per slot. If the bar below is met, also **fully
correct grids** on 20 never-read post-cutoff grids, for the calibrated
frontier with and without escalation, paired.

## Why
014's failures are 21 guessed slots where gold was "still not proposed
after up to 20 pattern samples and the list fallback", plus 11 committed
wrong. Persistence was **breadth at low effort**: every proposer call in
`data/instruments.json` runs at `effort: low`. More low-effort samples on
a hard slot returned the same misses.

The untested lever is **depth**: one call that thinks for longer, or a
stronger model. OpenAI's 2026-10-06 release of 372 families of maths
results is evidence that depth matters more than breadth. By its account,
nearly all of them came from one prompt to one agent, at about three hours
of thinking per kept result. Its September Navier–Stokes run used 10,000
agents instead. That is a different domain at a vastly larger scale, so it
moves the prior and settles nothing. This brief measures depth here, on the
slots that need it.

## Stage A: slot-level recall (dev data; cap $15)
- **Slots.** Every slot in 013's and 014's evaluation grids whose gold was
  not among the candidates at the end state. Take each slot's final
  crossing pattern from the logs. Those grids are already read, so from
  now on they are dev data and never an evaluation set again. Say so in
  `data/eval.json`.
- **Arms**, one structured-output call per slot per arm, top 5 with shares,
  same prompt as `propose_pattern` with only the model and effort changed:
  1. `claude-opus-5-5` at low effort, 5 resamples: the control. This is
     how often plain resampling finds gold.
  2. `claude-opus-5-5`, high effort.
  3. `claude-opus-5-5`, max effort.
  4. `claude-fable-5-1`, high effort. Drop this arm, and say so, if the
     smoke test shows the account can't call it.
- **Smoke test:** 3 slots per arm. Report the cost per call. If the
  projected cost of the full Stage A exceeds $15, cut arm 3 first.
- **Report:** gold-in-1 and gold-in-5 per arm, with Beta(1,1) 90%
  intervals; $ per slot; and the arm's top share on slots where it is
  wrong, because Stage B's calibration needs it.

**Decision rule, written before any call.** Let r be the best arm's
gold-in-5 on the stuck slots.
- If r's lower bound is ≥ 0.25, run Stage B with that arm. Where two arms
  tie within their intervals, use the cheaper one.
- If every arm's upper bound is < 0.10, depth does not reach the residual.
  The note says so, and 016 (other model families) is the last lever.
- Otherwise, report and stop; fable decides.

## Stage B: end to end (only if triggered; cap $45)
- **Grids:** 20 post-cutoff grids that have never been read. Use 013's
  reserve if any remains. Otherwise use a new harvest of posts after
  2026-10-22 under 012's protocol (REST API, 20 s delay, blind parser,
  nothing committed), with linked-clue puzzles excluded as before. Fix the
  seed and the list in `data/eval.json` before any grid is read.
- **Arms, paired:**
  - (a) 014's `frontier_calibrated`, unchanged.
  - (b) The same, plus **escalation**. When (a) would stop (no new
    candidates, or budget), call the Stage A arm on the uncommitted slot
    with the most known letters, then re-run BP. Repeat until every slot
    is committed or the budget is spent.
- **Calibration of escalated candidates:** fit the same logistic form as
  013, on Stage A's slots, and write it to `data/` before Stage B. Note
  that those slots are selected (stuck only). Stage B's paired outcome is
  what decides, not this fit.
- **Budget:** $3 per grid, as in 014, with a second readout at $5.
- **Report:** fully correct grids per arm, the paired table, P(b > a)
  under Beta(1,1), the paired clue difference with a bootstrap interval,
  and $ per grid. If P(b > a) ≥ 0.9, escalation becomes the solver's
  default, and the note's headline is rerun on the pooled grids.

## Not in this brief
Open-weight models on `steel` (the old 015) move to 016, still low
priority. The prior that a model weaker than Opus proposes what a
deep-thinking Opus misses is lower than the prior for depth.
