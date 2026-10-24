# Report — brief 015 (depth or enumeration on the residual)

Status: **complete through Stage A (2026-10-24); Stage B is triggered but
needs the author's cap.** Built by `opus`. Spend **$19.81**: D $13.28
(smokes $1.94, D1 $11.34), A $6.53 (smokes included), A0 $0. Caps: D $25,
A $15. Cumulative across briefs 000–015: **$264.95**.

Sets: the 40 evaluation grids of 013 (20) and 014 (20), post-cutoff for
Opus 5.5 under 012's rule (FT, Independent, Guardian, dated 2026-08 to
2026-10). From this brief on, they are **dev data**, never an evaluation
set again (`data/eval.json`, `residual`).

## Headline numbers

**Stage D: the model given the whole puzzle (one call per grid, Opus 5.5
at high effort, structured output).** Prompt and settings were pinned
before any call (241338e). The decision reads D1 on all 40 grids
(`lead`'s amendment, 393df7f, before any D call).

| | fully correct | clues | $ / grid |
|---|---|---|---|
| **D1, Opus asked directly** | **30 / 40** | 0.992 | 0.28 |
| full solver (013 + 014, stored) | 17 / 40 | 0.95–0.97 | 0.90–2.22 |
| calibrated frontier (014, stored) | 8 / 20 | 0.950 | 2.07 |

- **Paired against the full solver on 40 grids:** both 15, D1 only 15,
  solver only 2, neither 8. Under independent Beta(1,1) posteriors,
  **P(D1 > full solver) = 0.998**.
- **Paired against the calibrated frontier on 014's 20 grids:** D1 14,
  frontier 8; both 8, D1 only 6, frontier only 0. P = 0.969.
- **Free checks:** 0.05 crossing conflicts per grid (2 of 40 grids have
  any); ECE of the stated confidences 0.074 over 1,207 slots (10 bins).
  All 40 calls ended `end_turn`; none unfinished.
- **Decision (written before the data):** P ≥ 0.8, so **asking directly
  beats the bespoke route**. The next brief feeds D's answers in as the
  calibrated solver's first-round proposals (a hybrid), and the note's
  headline becomes that comparison.
- **D2 (Fable 5.1, high effort) was dropped by the brief's rule.** The
  account can call Fable (its smoke returned normally, fully correct on
  014's grid #1). But the smoke cost $1.57 per grid against D1's $0.37,
  so D1 + D2 projected ~$34 against the $25 cap. Fable's knowledge cutoff
  is unpublished; I used the Models API's `created_at` (2026-08-28) as an
  upper bound. Under 012's rule that leaves 12 of the 40 grids (28
  dropped).

**Stage A: gold-in-5 on the 17 stuck slots, per proposer arm.** Each arm
is one structured-output call per slot (arm 1: five samples). Intervals
are Beta(1,1) 90%.

| arm | n | gold-in-1 | **gold-in-5** [90%] | $ / slot | top share when wrong (n) |
|---|---|---|---|---|---|
| 1. Opus low, 5 resamples (control) | 17 | 5 | 6 [0.20, 0.55] | 0.041 | 0.78 (12) |
| 2. **Opus high** | 17 | 10 | **12 [0.50, 0.84]** | **0.023** | 0.60 (7) |
| 3. **Opus max** | 17 | 13 | **14 [0.62, 0.92]** | 0.236 | 0.68 (2) |
| 4. Fable high (its 9 eligible slots) | 9 | 4 | 5 [0.30, 0.78] | 0.147 | 0.61 (5) |
| 5. choose from W ∩ pattern (Opus low) | 17 | 5 | 6 [0.20, 0.55] | 0.006 | 0.53 (7) |
| 6. union of 5 and 3 | 17 | 12 | 14 [0.62, 0.92] | (5 + 3) | 0.51 (4) |
| A0. generator + verifier | 17 | 1 | 1 [0.02, 0.24] | 0 | — |

- **Decision (the brief's rule, written before any call):** the best arm
  is Opus max, r = 14/17, lower bound 0.62 ≥ 0.25, so **Stage B is
  triggered**. Opus high ties within its interval (upper 0.84 ≥ 0.82)
  and costs a tenth as much per slot, so **B's arm is Opus high**.
  `lead`'s middle-band rule (18227ae) does not apply: the lower bound
  clears the bar.
- **Depth, not breadth.** Five low-effort samples found 6/17; one
  high-effort call found 12/17, and cost less (one call's thinking
  against five). Max effort adds 2 more at 10× the price.
- **Two empty results for Opus max:** one refusal, and one reply cut off
  at 64,000 tokens (`max_tokens`). Both count as misses.
- **The 2 slots whose gold doesn't fit the final pattern** (a wrong
  committed crosser): Opus high and Opus max each found 1 of them (they
  were asked with the wrong pattern and answered outside it); every
  other arm found 0. On the 15 slots where gold fits the pattern: Opus
  max 13/15, Opus high 11/15, Fable 5/7, the control 6/15, arm 5 6/15.

**Stage A0 ($0, no calls): enumeration on the same 17 slots**
(`reports/015/a0.json`).

| | count / 17 | 90% interval |
|---|---|---|
| gold ∈ W (coverage) | 9 | [0.34, 0.71] |
| gold fits the final pattern | 15 | [0.69, 0.95] |
| gold ∈ W ∩ pattern | 8 | [0.29, 0.66] |
| gold is an anagram of a contiguous fodder span | 3 | [0.08, 0.38] |
| gold is hidden in the fodder (forwards or reversed) | 1 | [0.02, 0.24] |
| gold admitted by the verifier from a generated parse | 1 (Quarantine) | [0.02, 0.24] |

- **|W ∩ pattern|:** median 6, range 0–5,345. It is empty for 4 slots,
  ≤ 20 for 13, and over 300 (arm 5's limit) for 1.
- **Admitted words per slot:** 0 for 13 slots, 1 for 3, at most 4.
- **Misses by kind:** 8 not in W; 1 in W but excluded by a wrong
  pattern; 7 in W ∩ pattern but with no generated parse; 1 admitted.
  The split favours the depth arms over arm 5: W's coverage (9/17) caps
  enumeration below what one high-effort call reaches. Arm 5 found 6 of
  the 8 slots it could reach; the other 9 were out of its reach.

## What the stuck set is

As amended by `lead` (c7cd33c): an **uncommitted** slot whose gold no
proposer call of the full solver returned **in any round**, with its
final crossing pattern. These are rebuilt by replaying each run's own log
through the stub backend. Every replay matched its run's spend and clue
score.

- **17 slots:** 8 from 013, 9 from 014.
- **Reconciled against 014's "21 guessed slots, gold still not proposed":**
  of 014's 21 guessed-wrong slots, 9 never had gold returned, 4 had it
  returned and then dropped, and 8 had gold in the end state and lost in
  BP. Of the 48 wrong slots over 013 + 014, the final pattern excludes
  gold in 23 (comms 20261024T1715Z; now in `docs/LEAD.md`).

## Amendments, in order

All of these precede the data they govern (`git log`).

1. **c7cd33c (lead):**
   - A0 makes no calls;
   - the stuck-slot definition;
   - D's best arm, and how P is computed;
   - `lead` decides A's middle band.
2. **1c0e2d1 (opus):** Stage A's arms, formats and streaming, and Fable's
   cutoff bound, all pinned with A0.
3. **18227ae (lead):** the middle-band rule, before any A call.
4. **241338e (opus):** D's prompt and settings pinned before any D call.
   It was red for one push (fixed in bf6c685 with no change to the
   prompt or settings).
5. **393df7f (lead), then 909d4ec (opus):** the decision reads D1 on all
   40 grids, before any D call.

## Choices I made where the brief was open

- **Arms 2–4 use 004's pattern prompt, asking for up to 5 answers with
  shares** (`answer-pattern-top-v1`). Arm 1 is 014's exact instrument
  (k = 5, answer format). The brief says both "the same prompt as
  `propose_pattern`" and "top 5 with shares"; this reading keeps the
  wording and gets the list. P ≈ 0.65 that this is what was meant.
- **Arm outputs are not filtered by the pattern** (only by enumeration),
  because the pattern can hold a wrong letter.
- **W:** Moby Thesaurus II (every entry on every line) ∪ Open English
  WordNet 2025 lemmas, reduced to letters and keyed by letters per word
  (spaces and hyphens both split). No new source.
- **The generator's parse layout:**
  - an indicator of 1–2 tokens touching the fodder;
  - the definition at the clue's other end;
  - at most one link token between;
  - a reversed hidden word takes two indicator tokens, a reversal and a
    hidden.
  Words with no generated parse are "no parse".
- **D's input:** the clue lines are `1A. clue (enum)`; the grid lines are
  `1A (n letters): letter i = 2D letter j; …`. Each call has
  max_tokens 128,000, streamed.

## What was built

- **`ximenes.residual`:**
  - stuck-slot replay (`stuck_slots`, `stuck_of`, `proposed_answers`);
  - A0's generators (`anagram_words`, `hidden_words`, `parses`,
    `best_verdict`, `a0_row`);
  - the Stage A arms (`ask`, `union`, `score`, `decide`);
  - exact Beta tools (`beta_interval`, `p_greater`);
  - CLI.
- **`ximenes.direct`:** the puzzle as text, reading the reply, grid
  scoring with crossing conflicts, pairing against the stored runs,
  summary, CLI.
- **`data.load_wordlist`, `data.entry_key`.**
- **New instruments:** `propose_top`, `choose_from_list`, `solve_grid`,
  with prompts `answer-pattern-top-v1`, `choose-list-v1` and
  `direct-grid-v1`, and formats `shares`, `shares_other` and
  `grid_answers`. A request streams when max_tokens > 16,000.
- **Tests:**
  - `tests/test_015_residual.py`: Beta helpers, entry keys, the
    generators through the verifier, the stuck rule, the stub arms,
    the list limit, scoring, the decision bands;
  - `tests/test_015_direct.py`: puzzle text, scoring, reply parsing,
    the paired table, a stub run.
- **Data:** `data/instruments.json` sets Fable's knowledge cutoff to
  2026-08-28, an upper bound, with its source.

## Supersessions (D8)

None. No earlier test was edited.

## Reproduce

```bash
uv run python -m ximenes.residual stuck        # 17
uv run python -m ximenes.residual a0           # reports/015/a0.json
uv run python -m ximenes.direct run --arm D1   # run 20261024T150818Z-direct-D1
uv run python -m ximenes.direct summary        # reports/015/d.json
uv run python -m ximenes.residual arms --arm <arm> --log <smoke log>   # each of the five
uv run python -m ximenes.residual summary      # reports/015/a.json
```

Every call is logged under `runs/`, and `--backend stub --log …`
replays it.

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
303 passed
== kit: GREEN
```

## Open questions (for `lead`)

1. **B is triggered (Opus high, 12/17), and D says to build the hybrid.**
   The two overlap: D's one call per grid is itself depth on every slot
   at once. B's escalation (Opus high on stuck slots) may add little on
   top of a hybrid seeded with D's answers. Does B run as written (cap
   from the author), or fold into the hybrid brief as its escalation
   step? My guess: fold it in (p ≈ 0.6).
2. **D's 30/40 sits on grids the solver has now read.** They were read
   by our solver, not shown to Opus, so contamination is unchanged. But
   the hybrid's headline needs fresh grids (up to 88 unused in 012's
   harvest).
3. **Fable's knowledge cutoff** is a bound I set from `created_at`; the
   real date would let D2 and arm 4 use more grids.

## Probability complete

**0.8.** A0, D and A ran as pre-registered and amended, inside their
caps, with the decision rules applied as written. Doubts:
- the arm-2–4 prompt reading;
- n = 17;
- D2 dropped;
- one red push;
- B, which the brief triggers, needs the author's cap and is not run.
