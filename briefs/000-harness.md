# Brief 000 — Harness and contamination-safe data

Headline number: **top-1 accuracy and ECE of majority-vote confidence** for
one proposer on 1,000 Cryptonite test clues and on the post-cutoff set.

## Build
1. `ximenes.data.cryptonite`: load the Cryptonite JSONL (train/val/test) from
   `data/cryptonite/` (not committed). Preserve fields:
   `clue, answer, enumeration, orientation, is_quick, publisher, date`.
   Write `data/cryptonite/SPLITS.sha256` (committed) and refuse to load if
   hashes differ.
2. `ximenes.data.wordplay`: load the `mdda/cryptic-wordplay` explanations.
   Keep the raw explanation string and the brace-marked definition span.
   Respect its test-answer scrubbing.
3. `ximenes.instruments`: one function `propose_answers(clue, enum, k, model)`
   behind an `Instrument` protocol. Two backends: `anthropic` API and a
   `stub` that replays from `runs/`. Every call logged as JSONL:
   `{ts, instrument, model, input, output, cost}`. Replay must be exact.
4. `ximenes.eval.vote`: majority vote over k samples; confidence =
   vote share. Reliability diagram data and ECE (10 bins) to `runs/<id>.json`.
5. CLI: `python -m ximenes.eval vote --set test --n 1000 --k 20 --model <id>`.

## Tests (tests/test_000_*.py)
- Split hashes frozen; loader raises on mismatch.
- No module except `ximenes.eval` opens anything under `data/postcutoff/`.
- Replay of a logged run reproduces identical numbers.
- A checked-in 20-clue stub log under `tests/fixtures/` runs end to end.

## Not in scope
Any verifier. Any wordplay prompting. Any fine-tuning.

## Report
Headline numbers for both sets side by side; the gap is the contamination
estimate. Kit output. Open questions. Probability complete.
