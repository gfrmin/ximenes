# Roadmap

Framing: `docs/GAME.md`. Results so far: `docs/RESULTS.md`.

**Goal (set 2026-10-22 by fable, under the author's delegation):** the best
cryptic crossword solver these foundations allow, measured as **the share
of fully correct grids at a stated cost per grid**, every answer carrying a
calibrated probability and the judgements it rests on. Speed is secondary.

## Where the limit is (briefs 000–010)
The decision layer works: verifier sound (0 false accepts), posterior
calibrated (ECE 0.027), committed slots ~99% right, VOC beats attempt-all.
What limits grids is **candidate generation**: the gold answer is among a
slot's round-1 candidates in 57% of slots, and among all 20 Haiku samples
in only 64–70% of clues. A 30-slot grid needs ~98% per slot to be fully
correct half the time. So the next phase is the proposer, then the
end-to-end grid, then a clean number.

## Phase 2 (from 2026-10-22)

| # | Brief | Headline number | Cap |
|---|---|---|---|
| 011 | **Recall by proposer.** Haiku / Sonnet / Opus, sampled vs "list N candidates", with and without crossing-letter patterns, on a fresh Cryptonite test sample | gold-in-k and $ per clue for each proposer × prompt × pattern level | $40 |
| 012 | **End-to-end grid solver** with the proposer 011 picks: VOC, pattern re-proposal, posterior refitted on val for the new proposer | fully correct grids, clues, letters, $ per grid on 20 fresh reconstructed grids; stop rule below | $60 |
| 013 | **Clean number:** 012's solver, frozen, on post-cutoff grids | fully correct grids on post-cutoff puzzles; gap to 012 | ≤ $40 |
| 014+ | Whatever 012/013 show is the limit (ensemble proposers, a second formaliser, a stronger judge, cheaper routing by VOC) | — | per brief |

**Stop rule, pre-registered for 012.** On reconstructed Cryptonite grids
(an upper bound, mixed splits): if fewer than **10%** of grids are fully
correct at ≤ **$5 per grid**, the project stops chasing full grids and the
product is the calibrated solving assistant (per-answer probability and
evidence; brief 003's result is its core). If ≥ 10%, 013 and 014+ follow.

**Post-cutoff data (013's blocker).** Cryptonite ends in 2020; strong
models have likely seen it. The tools available to the agents decline
newspaper crossword sites, so the agents will not scrape them. Post-cutoff
puzzles need a source the author is entitled to use (e.g. puzzles from his
own subscription, saved as `.puz` / ipuz / PDF into `data/postcutoff/`,
never committed); a converter is part of 013. Until then, 012's number is
labelled an upper bound, and 011 reports accuracy by clue year per model as
a contamination probe.

## How Phase 2 is chosen (informal value of information)
Each brief is the experiment with the most expected improvement in the
decision it informs, per dollar:
- **The decision that matters most** is the stop rule: is a fully correct
  grid reachable at ≤ $5? Prior, informally ~0.5: frontier ensembles solve
  championship grids (Darmok), but our per-slot accuracy is 0.74, far from
  the ~0.93 needed. A cheap experiment that moves this probability a lot is
  worth more than any refinement of the decision layer (006–010 each moved
  numbers by ≤ 2 points).
- **011 ($25) bounds 012 ($60)**: recall at `half` pattern caps per-slot
  accuracy, so 011 can stop 012 early (its own pre-registered threshold)
  and save most of 012's cost if the answer is no. It also picks the
  proposer, where the wrong choice costs either accuracy or ~3× spend.
- **Contamination** biases every Cryptonite number upward, more for strong
  models. It matters little for *ranking* proposers on the same clues, a
  lot for the final claim. So: a cheap year-of-clue probe in 011, the real
  correction (post-cutoff grids) in 013, which is the single input only the
  author can supply.
- Numbers are reported with intervals; a result inside its interval of a
  threshold is "ambiguous", and the next cheapest experiment that resolves
  it is bought only if the decision would change.

## Spending
Standing envelope for Phase 2: **$150**, delegated by the author to `fable`
on 2026-10-22. Each brief states its cap; the builder may spend up to that
cap without asking, after a smoke test whose cost it reports. Anything
beyond a brief's cap or the envelope needs `fable`'s written approval in
`comms/`. The author can veto at any time by editing this section.
Cumulative before Phase 2: $103.18.

## Phase 1 (done)

| # | Brief | Result |
|---|---|---|
| 000 | Harness, splits, logged instruments, vote baseline | Haiku vote top-1 0.460, ECE 0.159 |
| 001 | Typed DSL, non-executing verifier, coverage law | coverage 0.850; 0 false accepts |
| 002 | Propose → verify → decide | top-1 0.552; verified set 505 at 0.861 |
| 003 | Calibrated posterior on val, read once on test | P ≥ 0.9: 37.9% at 0.968; ECE 0.027 |
| 004 | Grids: reconstruction, BP, commit, re-propose | clues 0.712 vs 0.513 alone; 0/20 fully correct |
| 005 | Metacomputation (VOC) | beats attempt-all from $0.45/grid |
| 006 | Final-state calibration of commit | negative: committed accuracy 0.895 |
| 007 | Commit-time calibration | closed on a free refit; bar and τ incompatible |
| 008 | Thesaurus attestation | nearly redundant with the judge |
| 009 | Wikipedia abbreviations | Ok +0.5–1.4 points |
| 010 | Soft vs hard evidence; gold-in-k | identical; the limit is candidate generation |

Deferred: distil a small proposer from proven parses (needs volume first).

## Protocols carried forward
Post-cutoff protocol (2026-10-21): compare like with like by publisher and
quick/cryptic; report gaps per publisher; Guardian/FT rows carry no
Cryptonite baseline. D7: fit on val, read a held-out sample once, refit
with a fresh seed.
