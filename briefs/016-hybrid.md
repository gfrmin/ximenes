# Brief 016: the hybrid — direct answers, repaired by the grid

**Status: open (2026-10-24, drafted by `lead`).** Cap **$30**, inside the
Phase 3 envelope ($60; $19.81 spent by 015, so $40.19 left). Builder:
`opus`. Lead: `lead`.

Headline number: on **40 never-read post-cutoff grids**, **fully correct
grids for the hybrid against Opus asked directly**, paired, with $ per
grid.

## Why
015 D decided: Opus 5.5 given the whole puzzle at high effort got 30/40
grids fully correct at $0.28 a grid, against the full solver's 17/40
(P = 0.998). Its decision rule names the next brief: feed D's answers in
as the calibrated solver's first-round proposals. Two other 015 results
shape the design:
- **Depth reaches the residual.** On 015's 17 stuck slots, one Opus call
  at high effort found gold in its top 5 on 12, against 6 for five
  low-effort samples, and cost less ($0.023 against $0.041 a slot).
  That is Stage B's escalation step, folded in here (opus's question 1
  on the 015 report); Stage B does not run separately.
- **Wrong commits poison crossers.** Over 013 + 014's 48 wrong slots,
  the final pattern excluded gold in 23. So the hybrid must not clamp
  D's answers: it treats them as evidence with a calibrated probability,
  and BP decides.

What the hybrid can add over D: it repairs D's wrong slots from the
crossing letters, and it resolves D's crossing conflicts (2 of 40 grids
in 015). What it can lose: BP can talk D out of a right answer. The
paired comparison measures both.

## Grids (fixed in `data/eval.json` before any grid is read)
- 012's harvest, daily cryptics with unique grids, **excluding every grid
  read by 013, 014 or 015** (their evaluation, fit and smoke grids).
- Seed **20261030**; 40 grids stratified by publisher as in 013. If fewer
  than 40 remain, take all of them and report n. If more are needed
  later, a fresh harvest under 012's protocol is a separate brief.
- Post-cutoff for Opus 5.5 under 012's rule. Evaluation is read once.

## Arms, paired on the same grids
- **(a) Direct:** 015's D1 exactly (`direct-grid-v1`, Opus 5.5 high,
  pinned settings). One call per grid.
- **(b) Hybrid:** the *same* call's answers (no second direct call, so
  the pairing is exact and (b) costs only its extra moves), then:
  1. **Round 1 = D's answers.** Each slot's candidate is D's answer with
     probability from a calibration map of D's stated confidence. The map
     is fitted on the 1,207 slots of 015's D1 run on the 40 dev grids
     (same logistic form as 013), and committed to `data/` before any
     016 grid is read. OTHER for the slot is 1 minus that probability.
  2. **BP** as in 014's `frontier_calibrated`: sum-product, commit at
     calibrated marginal ≥ 0.9, never clamp D's answer by itself.
  3. **Escalation:** while budget remains, take the uncommitted slot with
     the most known letters and ask **Opus high** (`answer-pattern-top-v1`,
     015 Stage A arm 2) with its current pattern; candidates enter with
     014's fitted vote posterior on their shares; re-run BP. Stop when
     every slot is committed, no new candidate appears in two passes, or
     the budget is spent.
  4. Submit the MAP assignment.
- **Budget for (b):** **$1.00 per grid including the direct call**,
  with a readout at $0.50.
- Persistence (014) stays off.

## Smoke test (before the paid run)
On 014's grid #1 only (already a smoke grid, not an evaluation grid):
both arms end to end. Report the cost. Project the full run; if it
exceeds $30, lower (b)'s budget to $0.75 and say so before the run.

## Report
- Fully correct grids per arm, clues per arm, $ per grid; the paired
  table (both / only a / only b / neither).
- **Decision statistic (paired, written now):** with n_b = grids only (b)
  gets fully correct and n_a = grids only (a) does,
  θ ~ Beta(1 + n_b, 1 + n_a); report P(θ > 0.5). Also report 014's
  independent-Beta P for continuity; it decides nothing.
- Per arm: ECE of the final slot probabilities; crossing conflicts; and,
  for (b), how many of D's answers BP overturned, split by right → wrong
  and wrong → right.
- D's rate on fresh grids beside its 30/40 on dev grids (a replication;
  it decides nothing).

## Decision rule (written before any data)
- **P(θ > 0.5) ≥ 0.8:** the hybrid is the solver. The note's headline is
  the hybrid against D on these grids, and the next brief measures it on
  more grids (n = 100).
- **P(θ > 0.5) ≤ 0.2:** our machinery makes asking directly worse. D is
  the solver; the note says so with the paired numbers, and the
  machinery's claim is calibration and audit only.
- **Otherwise:** D is the default (it is cheaper); report both; `lead`
  chooses between more grids and closing the line.

**The success case can occur.** With no grid lost by (b), 3 grids gained
give P = 0.94 and 2 give 0.875. With one lost, 3 gained give 0.81. D
left 10 of 40 grids not fully correct in 015, so 2–3 repairs are
plausible, not assured.

## Not in this brief
Fable 5.1 (its cutoff leaves too few grids), open-weight models on
`steel` (017, low priority), and any change to D's prompt.
