# Report — brief 002 (propose → verify → decide)

Status: **complete (2026-10-21).** Built by `opus` in the same session as
briefs 000–001, at the author's request. Spend for the whole brief:
**$15.54** of the $25 cap (smoke test $0.40, full run $15.14).

## Headline numbers

Same 1,000 Cryptonite test clues as brief 000 (seed 20261021). Run
2026-10-21; clue dates 2000-10-18 – 2020-10-30. Proposer `claude-haiku-5-5`
(brief 000's 20 samples, replayed); formaliser `claude-sonnet-5-5`;
judges `claude-haiku-5-5`.

| | n | top-1 |
|---|---|---|
| vote baseline (brief 000) | 1000 | 0.460 |
| **verifier-assisted (this brief)** | 1000 | **0.552** |

| set | clues | accuracy |
|---|---|---|
| **verified set, as the brief defines it** (Ok, or Quarantine with every oracle score ≥ 0.5) | **505** | **0.861** |
| verified set, strict (also excludes Quarantines resting on an unscored indicator / unreviewed table entry) | 278 | 0.777 |
| complement of the strict set | 722 | 0.465 |
| vote share ≥ 0.9 (brief 000's high-confidence band) | 275 | 0.858 |
| strict verified ∩ vote ≥ 0.9 | 108 | 0.944 |

**Reading the result (the brief's question).** Under the brief's own
definition, the verified set is **1.8× the size of the vote's
high-confidence band at the same accuracy** (505 at 0.861 vs 275 at 0.858):
the verifier earns its place on that comparison. The strict reading is mine,
added before the run (`d5f3b06`, "a Quarantine resting on an unscored
indicator is not verified", p≈0.6 at the time). On this run it is *smaller
and less accurate* than the vote band. Two things drag it down:
1. It drops 227 Quarantines that clear every oracle score but rest on an
   unscored step: an indicator missing from the table (134), an unreviewed
   entry (76), or both (17). They are right **0.965** of the time.
2. It always admits `Ok`, which is about the wordplay alone. Chosen `Ok`s
   with a definition score ≥ 0.5 are right 27 of 29 times (0.93); the 8
   with a lower definition score are right 2 of 8 (0.25).

So the useful decision object is "wordplay holds and every judgement,
definition included, clears the floor". Neither reading quite says that;
QUESTIONS.md asks which the author wants pre-registered for 003.

- **Where the gain comes from:** relative to the vote, the loop turns 123
  wrong answers right and 31 right answers wrong (net +92).
- **By status of the chosen answer:** Ok 37 (0.784), Quarantine 903 (0.570),
  no parse 60 (0.133).
- **By minimum oracle score of the chosen answer:** < 0.5: 443 clues, 0.251 ·
  0.5–0.8: 188, 0.819 · 0.8–0.95: 287, 0.899 · ≥ 0.95: 22, 0.955. Monotone,
  which is promising for brief 003's calibration (not fitted here).
- **Recall ceiling:** gold among the 3 candidates 0.616, among the 20
  samples 0.671. A parse existed for the gold answer for 0.600 of clues.
- **By publisher** (brief 000 vote in brackets): Telegraph 0.630 (0.547),
  Times 0.497 (0.399). **Quick vs cryptic:** quick 0.740 (0.610, n=77),
  cryptic 0.536 (0.447).
- **Reasons on chosen answers** (a parse can have several): synonym 492,
  indicator 239, cryptic_def 234, table_unreviewed 122, double_def 75,
  homophone 19.
- **Spend by instrument (new spend):** formalise_clue $14.58, judge_definition
  $0.29, judge_synonym $0.27, judge_homophone $0.003. Proposer $0 (replayed).

## Reproducibility: a bug found and fixed

The headline run predates memoization. **38 synonym judgements were asked
twice** with identical inputs (the same leaf under different candidates) and
got different scores, so the log had two answers for one input, against
DESIGN D6. Fixed in `memoized()`: within a run, one input gets one answer,
and concurrent repeats wait for it. For the existing log, the **canonical
replay** takes the first logged answer (`--on-conflict first`, explicit; the
default still raises). It is deterministic (two replays are identical) and
reproduces every headline number of the live run. 17 clues have slightly
different recorded scores, and one changes its chosen answer, with no
change in accuracy. `tests/test_002_solve.py::test_headline_run_replays_exactly`
checks this locally. Summary: `reports/002/test1000-solve.json` (canonical
replay, no answers or clue text).

## Table review

The table entries that brief 001's accepted parses used and that weren't
yet trusted: 170 (69 abbreviations, 101 indicators). Reviewed by opus (an
LLM) against standard usage: 165 accepted, 5 left doubtful
(`data/lexicon/REVIEW.md`). Effect on brief 001's formaliser outputs,
re-verified offline: **Ok 8 → 23 (val 300), 11 → 42 (train 500).** The
new operators also turn 2 val / 3 train Rejects into accepts. **The tables
are LLM-reviewed until the author's spot-check line exists in REVIEW.md**
(QUESTIONS.md § 002, fable's checkpoint).

## What was built

1. **Operators:** `first_letters`, `last_letters`, `outer_letters`,
   `middle_letters`, `remove` (any occurrence), `strip_outer`, `half`
   (even length; "first"/"second"). All mechanical and indicated, with
   property tests and 0 mutant false accepts (`tests/test_002_operators.py`).
2. **D4 split and table origins:** every verdict carries `definition`
   (span, pending/judged, score, oracle); a Quarantine carries its
   judgement `leaves`; Provenance records table hits (table, key, value).
   Per-entry origins in both tables (`build_indicators.py` is new); an entry
   counts as mechanical only if hand-written or reviewed, otherwise
   `Quarantine(table_unreviewed)`.
3. **Oracles:** `judge_synonym`, `judge_definition`, `judge_homophone`
   (Haiku 5.5, effort low, fixed JSON reply, unparseable → score None, every
   call logged). The verifier stays pure: scores are attached afterwards
   (`solve.judged`) and never change a verdict's status.
4. **Concurrency:** a clue's k samples run concurrently and come back in
   sample-index order. The pool size is kept *out of* the logged input
   (first attempt put it in, which broke the replay key of brief 000's
   log; brief 000's tests caught it).
5. **`ximenes.solve`:** candidates (top 3 enumeration-valid samples) →
   `formalise_clue` (Sonnet, no gold explanation, ≤2 hinted retries, no
   retry on NONE or an unknown operator) → verify → judge → the
   pre-registered decision rule (status, then minimum oracle score, then vote
   share), a pure function tested by a table of cases.

## Supersessions (DESIGN D8)

Earlier briefs' tests and fixtures changed by this brief, each because the
brief changed what they test:

- `tests/test_001_verify.py::test_good_parse_is_quarantined_on_its_definition`
  now asserts `Ok` with the definition pending (D4 changed; the name is
  kept for traceability).
- `tests/test_001_gold.py`: the assertion "a dsl_limit entry expects an
  unknown operator" is dropped (the new operators make some of them verify);
  the 001 audit class is kept as recorded.
- `tests/test_001_coverage.py` / `tests/fixtures/formalise-stub.jsonl`: the
  fixture's unknown-operator example is now `spoonerism` (it was
  `last_letters`, now a real operator).
- `tests/fixtures/gold-dsl.jsonl`: the parses that named a new operator are
  rewritten with its real signature; three abbreviations missing from the
  table (lecturer → L, Greek → GR, money → M) are written as `syn(...)`, as
  the verifier's hint says. Expected status changes:

| val index | answer | 001 audit | expected in 001 | expected now |
|---|---|---|---|---|
| 21 | KISSOGRAM | dsl_limit | `Reject:surface:unknown_operator:last_letters` | `Quarantine:indicator,table_unreviewed` |
| 34 | TASK FORCE | dsl_limit | `Reject:surface:unknown_operator:last_letters` | `Quarantine:synonym` |
| 37 | EXECRATE | formaliser_miss | `Quarantine:synonym,definition` | `Quarantine:synonym` |
| 51 | NOVELETTE | dsl_limit | `Reject:surface:unknown_operator:strip_outer` | `Reject:answer:mismatch` |
| 81 | EARN | dsl_limit | `Reject:surface:unknown_operator:remove` | `Quarantine:synonym` |
| 93 | SPECIALLY | dsl_limit | `Reject:surface:unknown_operator:remove` | `Quarantine:table_unreviewed` |
| 124 | ADVANCES | dsl_limit | `Reject:surface:unknown_operator:last_letters` | `Quarantine:synonym` |
| 127 | NEWBIE | dsl_limit | `Reject:surface:unknown_operator:remove` | `Reject:remove:no_occurrence` |
| 167 | GRANDEUR | dsl_limit | `Reject:surface:unknown_operator:last_letters` | `Quarantine:synonym,indicator` |
| 170 | RACKET | formaliser_miss | `Quarantine:definition,indicator` | `Quarantine:indicator,table_unreviewed` |
| 198 | FACTORY | dsl_limit | `Reject:surface:unknown_operator:last_letters` | `Reject:answer:mismatch` |
| 200 | SHERPA | dsl_limit | `Reject:surface:unknown_operator:remove` | `Quarantine:indicator` |
| 213 | SIESTA | formaliser_miss | `Quarantine:definition,indicator` | `Quarantine:indicator` |
| 219 | TERRITORY | dsl_limit | `Reject:surface:unknown_operator:last_letters` | `Quarantine:synonym,indicator` |
| 221 | COSMOPOLITAN | dsl_limit | `Reject:surface:unknown_operator:half` | `Quarantine:synonym,indicator,table_unreviewed` |
| 226 | FEAT | dsl_limit | `Reject:surface:unknown_operator:last_letters` | `Quarantine:indicator` |
| 230 | SMEE | dsl_limit | `Reject:surface:unknown_operator:outer_letters` | `Quarantine:synonym,indicator` |
| 244 | PROFESSOR | dsl_limit | `Reject:surface:unknown_operator:remove` | `Quarantine:synonym,table_unreviewed` |
| 265 | MATEY | dsl_limit | `Reject:surface:unknown_operator:last_letters` | `Quarantine:synonym,indicator` |
| 266 | INFORM | dsl_limit | `Reject:surface:unknown_operator:strip_outer` | `Quarantine:synonym` |
| 280 | INSURE | dsl_limit | `Reject:surface:unknown_operator:remove` | `Reject:remove:no_occurrence` |
| 289 | INSURANCE | dsl_limit | `Reject:surface:unknown_operator:remove` | `Reject:remove:no_occurrence` |
| 292 | AGE | dsl_limit | `Reject:surface:unknown_operator:outer_letters` | `Ok:` |
| 293 | NUTS | verifier_bug | `Quarantine:synonym,definition` | `Quarantine:synonym` |

The 5 that still Reject are true limits: removing letters that aren't one
contiguous run (3), and explanations that drop a possessive 's (2).

## Reproduce

```bash
export ANTHROPIC_API_KEY=$(secret-tool lookup service env key ANTHROPIC_API_KEY)
uv run python -m ximenes.solve --set test --n 1000 --seed 20261021 --candidates 3 \
    --log runs/<brief-000-vote-log>.jsonl
# canonical offline replay of the headline run:
uv run python -m ximenes.solve --set test --n 1000 --backend stub --on-conflict first \
    --log runs/20261021T165753Z-solve-anthropic-d3af91634788448084b4f4ca07a7a090.jsonl
```

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 48%]
........................................................................ [ 96%]
......                                                                   [100%]
150 passed in 3.46s
== kit: GREEN
```

(In CI the headline-replay test is skipped: its log is local.)

## Open questions

See `QUESTIONS.md` § Brief 002.

## Probability complete

**0.75.** All six build steps and every listed test exist, and the headline
replays deterministically. Off: the live run had a D6 violation (fixed;
canonical replay used); the verified-set reading needs a ruling; and the
table review was done by an LLM pending the author's spot-check.
