# Roadmap

Framing: `docs/GAME.md`. Results so far: `docs/RESULTS.md`.

**Goal (set 2026-10-22 by fable, under the author's delegation):** the best
cryptic crossword solver these foundations allow, measured as **the share
of fully correct grids at a stated cost per grid**, every answer carrying a
calibrated probability and the judgements it rests on. Speed is secondary.

## Targets and reference points
- **Darmok (2026):** frontier-model ensemble; solved the Times Championship
  final ~3 min faster than the human winner (10:05), i.e. fully correct on
  championship puzzles under time pressure. No paper, no accuracy over a
  puzzle set, no cost. Its disclosed method is "attempt every clue, then
  enter answers".
- **Published SOTA (single clue, Cryptonite):** Andrews & Witteveen, ICML
  2025: 32.5% top-1 (200 clues, 9B models plus a Python verifier that they
  show can be fooled); GPT-4o 27.6%. Older models; stale against 2026
  frontier models, and Cryptonite is likely in their training data.
- **Our targets on post-cutoff daily cryptics:** fully correct grids
  ≥ 10% at ≤ $5 (continue); ≥ 50% (strong-amateur level, competitive);
  ≥ 90% (Darmok-class on daily puzzles). Always against the paired
  frontier-only baseline at equal cost, and with calibrated per-answer
  probabilities (ECE) and named evidence.
- **What would be publishable:** (i) workshop level now: a verifier sound by
  grammar (0 false accepts) vs A&W's exploitable one, calibrated selective
  answering (P ≥ 0.9: 37.9% of clues at 0.968), and a post-cutoff,
  contamination-aware evaluation protocol; (ii) main-conference level if
  013/014 show either higher fully-correct rates than the frontier-only
  baseline at equal cost, or equal accuracy at much lower cost via VOC, with
  ablations attributing the gain. A result where the machinery adds nothing
  over the baseline is still reportable, but as calibration and audit, not
  accuracy.

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
| 011 | **Recall by proposer.** Haiku / Sonnet / Opus, sampled vs "list N candidates", with and without crossing-letter patterns, on a fresh Cryptonite test sample | gold-in-k and $ per clue for each proposer × prompt × pattern level | $40 (waits for the author's go) |
| 012 | **Post-cutoff harvest** from Fifteensquared (REST API, 20 s delay, local only): clues, answers, explanations from 2026-08-01; grids reconstructed; post-cutoff rule moved to knowledge cutoffs | puzzles, clues and unique grids by publisher | $0 |
| 013 | **End-to-end grid solver**: Opus `list` round 1, Opus `sample` re-proposal (011's picks), posterior / OTHER / gain model refitted on post-cutoff fit grids, VOC at $5/grid; 20 post-cutoff evaluation grids (`briefs/013-end-to-end.md`) | fully correct grids, clues, letters, $ per grid; stop rule below | $80 |
| 014 | **Close the last slots**: persistent re-proposal for two paired policies (full solver; frontier + fitted vote posterior; raw frontier smoke only), 20 fresh post-cutoff grids (seed 20261028) | fully correct grids per policy at $1/$2/$3; pooled 40-grid rate; what the verifier adds over calibration | $90 |
| 015 | **Depth or enumeration on the residual** (`briefs/015-depth-on-the-residual.md`): Stage A0 ($0), word-list coverage, pattern matches and DSL generators on 013's and 014's stuck slots (gold never proposed), now dev data; Stage D ($25), the model given the whole puzzle (Opus high, Fable 5.1), paired against our solver on 013's and 014's 40 grids; Stage A, Opus at low / high / max effort, Fable 5.1, and Opus choosing from the pattern-matched list; Stage B, only if the best arm's gold-in-5 lower bound is ≥ 0.25: escalation on 20 never-read grids, paired against 014's calibrated frontier | D: fully correct grids, direct vs solver, paired; A: gold-in-5 per arm, $ per slot; B: fully correct grids, paired | $60 (Phase 3, open) |
| 016 | **Recall across model families** (low priority): open-weight models on the author's `steel` box (GPU, Ollama), beside Opus, on 015's stuck slots; each family alone and their union | gold-in-5 per model and for the union | ≤ $10 |
| 017+ | The note (`docs/NOTE-draft.md`) finalised with 015's result | — | per brief |

**Stop rule, pre-registered for 013.** On post-cutoff grids: if fewer than **10%** of grids are fully
correct at ≤ **$5 per grid**, the project stops chasing full grids and the
product is the calibrated solving assistant (per-answer probability and
evidence; brief 003's result is its core). If ≥ 10%, 014+ follow.

**Post-cutoff data.** Fifteensquared blogs Guardian, Independent and FT
cryptics daily with every clue, its answer and a wordplay explanation;
grids are reconstructed from the numbering (brief 004). Its robots.txt
allows ordinary crawlers with a 20 s delay; brief 012 uses the REST API,
keeps everything local, and never commits or republishes content. The
newspapers' own sites stay off limits to the agents.

## How Phase 2 is chosen (informal value of information)
Each brief is the experiment with the most expected improvement in the
decision it informs, per dollar:
- **The decision that matters most** is the stop rule: is a fully correct
  grid reachable at ≤ $5? Prior, informally ~0.5: frontier ensembles solve
  championship grids (Darmok), but our per-slot accuracy is 0.74, far from
  the ~0.93 needed. A cheap experiment that moves this probability a lot is
  worth more than any refinement of the decision layer (006–010 each moved
  numbers by ≤ 2 points).
- **011 ($25) bounds 013 ($60)**: recall at `half` pattern caps per-slot
  accuracy, so 011 can stop 013 early (its own pre-registered threshold)
  and save most of 013's cost if the answer is no. It also picks the
  proposer, where the wrong choice costs either accuracy or ~3× spend.
- **Contamination** biases every Cryptonite number upward, more for strong
  models. It matters little for *ranking* proposers on the same clues, a
  lot for the final claim. So: a cheap year-of-clue probe in 011, and the
  real correction, post-cutoff grids from 012 ($0), in place before the
  expensive end-to-end run, so 013 is measured on clean data from the start.
- Numbers are reported with intervals; a result inside its interval of a
  threshold is "ambiguous", and the next cheapest experiment that resolves
  it is bought only if the decision would change.

## Phase 2 closed (2026-10-23)
013 passed its stop rule (≥ 10% fully correct at ≤ $5: 17/40 pooled) and
014 settled the paired comparison: a calibrated Opus + crossers + BP solver
matches the full machinery at ~$1 per grid. Phase 2 spent $141.96 of its
$150 envelope. What is left is the proposer's recall (answers never
proposed). 014's persistence was breadth at low effort and did not reach
them. 015 (drafted 2026-10-24) tests depth (higher effort, a stronger
model) and enumeration (a finite word list cut by the crossing letters,
the DSL as generator and checker) on those slots, then end to end only if the slot-level bar is met.
Phase 3's envelope is open (Spending, below). Other model
families on `steel` move to 016, still low priority.

## Spending
Standing envelope for Phase 2: **$150**, delegated by the author to `fable`
on 2026-10-22. Each brief states its cap; the builder may spend up to that
cap without asking, after a smoke test whose cost it reports. Anything
beyond a brief's cap or the envelope needs `fable`'s written approval in
`comms/`. The author can veto at any time by editing this section.
Cumulative before Phase 2: $103.18; after 013: $160.64 (Phase 2 $57.46 of $150).

**Phase 3 envelope: $60**, opened by the author on 2026-10-24 (his "You have
my OK" in the claude.ai thread, recorded by `fable`). It covers brief 015's
A0 ($0), D ($25) and A ($15). Stage B gets its own cap from the author if A
triggers it. From 015 on, the lead role passes from `fable` to `lead`
(`docs/LEAD.md`), with the same spending rules: anything beyond a brief's
cap or this envelope needs the lead's written approval in `comms/`, and
anything beyond the envelope needs the author's.

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
