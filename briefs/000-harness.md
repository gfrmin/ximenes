# Brief 000 — Harness and contamination-safe data

Headline number: **top-1 accuracy and ECE of majority-vote confidence** for
one proposer on 1,000 Cryptonite test clues (and on the post-cutoff set, if
any files are present under `data/postcutoff/`).

## What is already there
- `data/cryptonite/cryptonite-{train,val,test}.jsonl` (470,804 / 26,156 /
  26,157 records; the files have no trailing newline, so `wc -l` shows one
  fewer) with the frozen hashes in `data/cryptonite/SPLITS.sha256`.
  Fields per line, as published: `publisher, date` (ms since epoch),
  `author, number, orientation` ("across"/"down"), `clue` (lowercased, with
  the enumeration embedded, e.g. `"... turning point (9)"`), `answer`
  (lowercase, may contain spaces/hyphens), `enumeration` (`"(9)"`),
  `quick` (bool), `sub_publisher`.
- `data/wordplay/sample_teacow_{train,val}.jsonl` (5,412 / 300) and
  `cryptonite.{val,test}.txt` (answer lists for the splits). Fields:
  `clue` (definition in `{}`), `pattern`, `ad` (A/D), `answer`, `wordplay`,
  `author, setter, publication, is_quick, num`.
- `ximenes.clue` (tokens, enumeration), `ximenes.dsl`, `ximenes.verify`
  stage 1, `ximenes.verdict`. Leave these alone in this brief.

## Build
1. `ximenes.data`: typed loaders for both datasets returning frozen
   dataclasses. The Cryptonite loader verifies `SPLITS.sha256` and raises on
   mismatch. Map `quick`→`is_quick`, split `clue` into text and `Enumeration`
   via `ximenes.clue.split_clue`, parse `date` to a `datetime.date`.
2. `ximenes.instruments`: an `Instrument` protocol and one instrument
   `propose_answers(clue_text, enumeration, k, model) -> list[str]`. Two
   backends: `anthropic` (API, requires `ANTHROPIC_API_KEY`) and `stub`
   (replays from a JSONL log; raises if an input is missing from the log).
   Every call is appended to `runs/<run-id>.jsonl` as
   `{ts, instrument, model, input, output, cost}`. Replay must be exact.
3. `ximenes.eval`: majority vote over k samples; confidence = vote share;
   top-1, reliability-diagram bins and ECE (10 bins) written to
   `runs/<run-id>.json`. This is the only module allowed to open
   `data/postcutoff/`, and only with `allow_postcutoff=True`.
4. CLI: `python -m ximenes.eval vote --set test --n 1000 --k 20 --model <id>
   [--backend anthropic|stub --log runs/<id>.jsonl]`. Sampling of the 1,000
   clues is seeded and the seed is recorded in the output.
5. `tests/fixtures/stub-20.jsonl`: a hand-made log for 20 val clues so the
   whole pipeline runs offline in CI.

## Tests (tests/test_000_*.py)
- Loader raises on a hash mismatch (tamper a temp copy).
- Only `ximenes.eval` opens `data/postcutoff/` (grep the package).
- Replaying `tests/fixtures/stub-20.jsonl` twice gives identical numbers.
- ECE of a perfectly calibrated synthetic run is 0.

## Not in scope
Any verifier beyond stage 1. Any wordplay prompting. Any fine-tuning.

## Report
Headline numbers for Cryptonite test (and post-cutoff if present) side by
side; the gap is the contamination estimate. Kit output. Open questions.
Probability complete.
