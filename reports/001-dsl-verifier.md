# Report — brief 001 (typed DSL and non-executing verifier)

Status: **complete (2026-10-21).** Built by `opus` in the brief-000 session,
at the author's request.

## Headline numbers

| set | run date | n | gold-parse coverage | Ok | Quarantine | Reject | mutants | false accepts | cost |
|---|---|---|---|---|---|---|---|---|---|
| wordplay **val** (FT, teacow) | 2026-10-21 | 300 | **0.850** | 0 | 255 | 45 | 1,119 | **0** | $0.93 |
| wordplay train, seeded 500 of 5,412 | 2026-10-21 | 500 | 0.840 | 0 | 420 | 80 | 1,787 | **0** | $1.46 |

- **Coverage** = share of gold explanations that the formaliser
  (`claude-sonnet-5-5`, effort low, ≤2 hinted retries) wrote in the DSL and
  the verifier accepted (`Ok` or `Quarantine`). Seed 20261021. Both runs
  replay bit for bit offline from their logs (`--backend stub`).
- **Quick vs hard:** neither sample contains a quick clue (`is_quick` is false
  on all 300 val rows and on the 500 train rows), so the quick/hard split is
  empty: coverage_hard = coverage, coverage_quick undefined.
- **Stop rule** (ROADMAP: "far below ~30%"): not triggered. 0.85 is well
  above it, with the caveats below.
- **Spend:** $2.47 in total, including a $0.08 smoke test (cap $10 per run,
  `data/eval.json`). The full train sample would have been ~$25 at the
  measured rate; 500 was chosen to keep spend low (QUESTIONS.md).
- Summaries without DSL source or clue text: `reports/001/`.

## What the number means, and what it doesn't

- **No parse is `Ok`.** DESIGN D4 makes `defn` an oracle leaf, so every clue
  with a definition is at least `Quarantine(definition)`. As specified, `Ok`
  is unreachable for ordinary clues (question for the author in
  QUESTIONS.md). The closer analogue of "wordplay proven" is a Quarantine
  whose *only* reason is `definition`: **23 of 300 val (7.7%), 42 of 500
  train (8.4%)**.
- **Quarantine reasons on val** (a parse can have several): definition 225,
  synonym 175, indicator 87 (indicator phrase not in the table),
  double_def 24, cryptic_def 6, homophone 5. Charades get most of their
  letters from `syn`, a judgement (median 78% of answer letters on val); that
  is what brief 002's oracle calls must check.
- **The definition is not checked in this brief.** A parse whose wordplay
  works for the wrong answer would also pass, quarantined on the definition
  (a test pins this down). Only the wordplay arithmetic and the coverage law
  are enforced.
- **1 val parse is a single `syn(...)` equal to the answer** (effectively a
  double definition, honestly quarantined as synonym). The first run had 6:
  the double-definition bug below rejected those parses, and the formaliser's
  retry worked around it by writing them as a synonym.

## Why parses are rejected (what the next operator should be)

Final val run, 45 Rejects; train in brackets (80):

| family | val | train | DSL operator that would cover it |
|---|---|---|---|
| extract letters: last/first/outer letters (`[offic]E`, `S[ensibl]E`) | 20 | 39 | `last_letters`, `outer_letters` (and `first_letters` of one word) |
| remove letters: subtraction or trimming (`[l]EARN` = LEARN − L, `[r]IN[g]`) | 16 | 31 | `remove(ind, A, B)`, `strip_outer(ind, A)` |
| middle letters | 4 | 2 | `middle_letters` |
| half a word | 1 | 3 | `half` |
| other (spoonerism, cycle, replace a letter, "what could make") | 3 | 4 | — |
| formaliser error (`insert:no_position`) | 1 | 1 | — |

**Recommendation: add `last_letters` / `outer_letters` and `remove` /
`strip_outer` next.** Together they account for ~80% of Rejects on both
splits. Per the brief, no operators were added; this table is the case for
doing so.

## 30-Reject audit (seeded sample of the first val run's 50 Rejects)

Each Reject was hand-parsed from the clue and explanation
(`tests/fixtures/gold-dsl.jsonl`; tokens stored as positions, no clue text):

| outcome | n | examples |
|---|---|---|
| **DSL limit** (needs an operator the DSL lacks) | 23 | last letters ×9, remove letters ×8, outer/strip ×4, half, a double insertion |
| **formaliser miss** (expressible; the formaliser didn't find it) | 3 | a hidden word it read as two truncations; a hidden-then-reversed word; a down-clue positional charade |
| **verifier bug** (now fixed) | 4 | below |

The verifier bugs the audit found, fixed in `ed495f8` with regression tests:

1. The stated answer of `double_def`/`cryptic_def` was read from the *last*
   argument, which is a trailing `link(...)` when one is present. Every
   double definition with a link word was wrongly rejected (3 of the 30).
2. Repeated words: the k-th reference took the k-th occurrence in preorder,
   so "Bowl over and over" gave the indicator "over" the first occurrence and
   the span "bowl over" had nothing left. Occurrences are now assigned so that
   references don't overlap when possible.

Coverage before the fixes was 0.833 (first run); after them 0.850 on the
same formaliser outputs (re-run replayed from the log, no new calls). The
audit numbers above describe the first run's Rejects.

## Mutation suite (false accepts must be 0)

Each accepted parse gets up to six mutants (`src/ximenes/mutants.py`):
- wrong answer,
- a trailing declaration dropped,
- an extra `link` on an already-used token,
- one letter changed in a **mechanical** stated string (anagram/insert/hidden
  result, abbreviation value),
- one letter changed in an **oracle** stated string (a `syn` value, a homophone
  source),
- a definition span shortened.

Mechanical mutants must be Rejected; oracle-claim mutants must not be `Ok`.

| kind | val mutants | accepted | false accepts |
|---|---|---|---|
| answer | 255 | 0 | 0 |
| claim (mechanical) | 155 | 0 | 0 |
| drop_decl | 141 | 0 | 0 |
| extra_link | 255 | 0 | 0 |
| oracle_claim | 205 | 7 | 0 |
| shrink_defn | 108 | 0 | 0 |

The first version of the suite counted any accepted mutant as false and
reported **7 / 991**. All 7 were oracle-claim mutants. For example,
`syn(tok("Spirits"), "GHOSTS")` became `"HHOSTS"` under `delete_first`, which
then removes the changed letter. The verdict was `Quarantine(synonym)`,
correct under D4: the verifier doesn't judge synonyms, and the verdict says
the parse rests on one. The suite now separates the two kinds, keeps the raw
`accepted` count per kind, and still counts an oracle-claim mutant returning
`Ok` as a false accept. **Mechanical false accepts: 0 / 914 on val, 0 / 1,449
on train.**

## What was built

- **`verify.py` stages 2–5:** sort check (a bare string is a `Claim` and is
  never fodder), token resolution, evaluation over candidate-string sets,
  indicator and abbreviation tables, the coverage law (DESIGN D3), and the
  answer/enumeration check, with Andrews & Witteveen-style hints on every
  Reject.
- **`dsl.py`:** `Sort.CLAIM`, trailing declarations (`link`, `double_duty`)
  on the four top-level forms, and an `indicated` flag. Arities and operator
  names are unchanged. **`verdict.py`:** `Reason.INDICATOR` (fable updated
  DESIGN D4 to match, `34086aa`).
- **`instruments.formalise_gold`:** Sonnet, with the system prompt (DSL spec
  plus six original examples, `prompts.py`) prompt-cached. Hinted retries,
  and no retry when the parse names an unknown operator. The reply's last
  balanced top-level expression is taken. `budgeted()` enforces `max_usd`.
- **`python -m ximenes.eval coverage --set val|train`:** refuses Cryptonite
  test; resumable with `--log`.
- **`data/lexicon/`:** merged with rdeits/CrypticCrosswords.jl (MIT); fused
  upstream abbreviation values fixed with an explicit, reviewed list
  (`REVIEW.md`, reported by fable).

## Reproduce

```bash
export ANTHROPIC_API_KEY=$(secret-tool lookup service env key ANTHROPIC_API_KEY)
uv run python -m ximenes.eval coverage --set val --model claude-sonnet-5-5
uv run python -m ximenes.eval coverage --set train --n 500 --model claude-sonnet-5-5
# offline, bit for bit:
uv run python -m ximenes.eval coverage --set val --model claude-sonnet-5-5 \
    --backend stub --log runs/<run-id>.jsonl
```

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 60%]
................................................                         [100%]
120 passed in 1.06s
== kit: GREEN
```

## Open questions

See `QUESTIONS.md` § Brief 001.

## Probability complete

**0.8.** Every build item and test in the brief exists and is green. The
headline replays exactly offline, and the mutation suite finds no mechanical
false accepts. The main doubts are two readings of the brief: the expected
status of DSL-limit gold parses, and `Ok` being unreachable under D4 (both
in QUESTIONS.md). The audit also showed the verifier had bugs a test suite
alone didn't catch, so others may remain.
