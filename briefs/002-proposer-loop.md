# Brief 002 — Propose → verify → decide, on real clues

Headline number: **top-1 on the same 1,000 Cryptonite test clues as brief
000 (seed 20261021), verifier-assisted, against the vote baseline 0.460**;
and the **verified set**: how many of the 1,000 end with an `Ok` or a
Quarantine whose oracle scores all clear the floor, and the accuracy inside
that set. Spend cap for the whole brief: **$25** (`max_usd` per run in
`data/eval.json`; stop and report if a run would pass it).

## What is already there
Brief 000's vote run is logged: the 20 Haiku samples per clue replay for
free (`runs/…d1625083….jsonl`; the author has it locally). Brief 001 gives
the verifier (stages 1–5), the formaliser instrument and prompt, the
mutation suite, the lexicon build with origin tags, and the gold fixture.
Answers to QUESTIONS.md § Brief 001 apply; D4 now says a verdict is about
the wordplay and the definition is reported alongside.

## Build, in this order

### 1. New mechanical operators (first, with tests, before any LLM call)
Each takes an indicator token first (`indicated=True`), fodder, and claims
its result; each gets a property test with random fodder and joins the
mutation suite. Enumeration/length checks are unchanged.
- `first_letters(ind, span)` / `last_letters(ind, span)`: first/last letter
  of each word in the span, in order.
- `outer_letters(ind, A)`: first and last letter of A.
- `middle_letters(ind, A, "RESULT")`: A with one letter stripped from each
  end, repeated until the claimed result is reached; result must be a
  non-empty centred substring.
- `remove(ind, A, B, "RESULT")`: delete one contiguous occurrence of B from
  A; accept if *any* occurrence gives the claimed result (an existential
  check is still mechanical).
- `strip_outer(ind, A)`: A without its first and last letter.
- `half(ind, A, "first" | "second")`: for even length only; a claim names
  the half.
Then update `tests/fixtures/gold-dsl.jsonl` expectations that named one of
these operators, and list each change in the report (D8 supersession).

### 2. Table origins and the unreviewed rule
Give `data/lexicon/indicators.json` the same `_origin` tags as the
abbreviations. In the verifier, a step resting on an entry whose origin is
not `hand` or `review` yields `Quarantine(table_unreviewed)` (new `Reason`).
Review the entries that the accepted val+train parses of brief 001 hit
(list them; a few hundred), moving them to `review` in `REVIEW.md`. Report
how many 001 parses become `Ok` as a result.

### 3. Oracle instruments (logged, replayable, cheap)
Three instruments in `ximenes.instruments`, model `claude-haiku-5-5` at
effort low, one call each, returning a score in [0, 1] and one line of
reason, parsed from a fixed JSON reply:
- `judge_synonym(clue_word_or_phrase, value, context)`
- `judge_definition(definition_span, answer, clue_text)`
- `judge_homophone(spoken, heard)`
Scores attach to the verdict (`Quarantine.oracle_scores`, and the new
`definition` field on every verdict). No thresholding inside the verifier:
it reports; the decision layer decides. Each oracle call logged with inputs
so brief 003 can calibrate against gold.

### 4. Concurrent samples within a clue
As agreed in `comms/…parallel-samples`: the k requests of one
`propose_answers` call go out concurrently from a pool whose size is in
`data/instruments.json`; results are kept in sample-index order. A test
shows a replayed log gives the same vote, tie-breaks included, regardless
of how the live run was scheduled.

### 5. The loop (`ximenes.solve`, single clue, no crossers)
For one clue, with its enumeration and orientation:
1. Candidates: the 20 vote samples (replayed from brief 000's log; live only
   for clues not in it), normalised, enumeration-filtered; keep the top
   `m = 3` by vote share.
2. For each candidate: `formalise_clue(clue, candidate, model)` — the 001
   formaliser prompt without the gold explanation, asking for a definition
   span and a DSL parse; model `claude-sonnet-5-5`, effort low; up to 2
   hinted retries on `Reject`.
3. Verify; call the oracles for every oracle leaf of an accepted parse and
   for the definition.
4. Decide, by a fixed pre-registered rule (no fitting in this brief):
   rank candidates by (`Ok` > `Quarantine` > no parse), then by the minimum
   oracle score (definition included), then by vote share. Output the top.
   Record for every clue: chosen answer, verdict, reasons, min oracle score,
   vote share of the chosen answer, and whether a parse existed for the
   gold answer among the candidates (recall ceiling, as in A&W).
5. The **verified set** = clues whose chosen answer is `Ok`, or Quarantine
   with every oracle score ≥ `oracle_floor` (`data/eval.json`, pre-register
   0.5). Report its size and accuracy; also accuracy of the complement.

### 6. CLI and run
`python -m ximenes.solve --set test --n 1000 --seed 20261021 --candidates 3
[--backend stub --log …]`, writing `runs/<id>.json` with everything above
and a `reports/002/` summary without clue text. Expected spend: ~3 × 1,000
formaliser calls with retries (~$14 at 001's rate) plus oracle calls
(Haiku, a few dollars). Smoke test on 20 clues first; report its cost.

## Tests (tests/test_002_*.py)
- Every new operator: property test; mutants give 0 false accepts.
- Oracle instruments: logged, replayable; a stub fixture for 20 clues runs
  the whole loop offline.
- The decision rule is a pure function of the recorded fields (a table of
  cases).
- A wordplay that works for the wrong answer: verdict unchanged, definition
  judged low, and the decision rule prefers a candidate with a higher
  minimum score.
- Replaying the 1,000-clue run reproduces the headline exactly.

## Not in scope
Crossers and grids (004). Calibration, learned thresholds, set answers
(003). Changing the proposer model. Batches API. Fine-tuning.

## Report
Headline table: vote baseline 0.460 vs verifier-assisted top-1 on the same
1,000; verified-set size and accuracy; complement accuracy; recall ceiling
(gold among the 3 candidates; gold among the 20); Ok / Quarantine / none
breakdown of chosen answers; per-publisher split (Times vs Telegraph) and
quick vs cryptic; spend by instrument. Then the fixture supersessions, the
table-review counts, kit output, open questions, probability complete.

Reading the result: the interesting comparison is not only top-1 but
**accuracy inside the verified set vs vote share ≥ 0.9** (brief 000: 275
clues at 0.86). If the verified set is as accurate and larger, or more
accurate at a similar size, the verifier earns its place; if not, say so.
