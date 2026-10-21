# Report — brief 000 (harness)

Status: **complete (2026-10-21).** Headline: `claude-haiku-5-5` majority vote,
top-1 **0.460**, ECE **0.159** on 1000 Cryptonite test clues. Run summaries live in `reports/000/` without clue text
(Cryptonite clues are unlicensed newspaper text and this repo is public).
Full per-call logs are under `runs/`, which is not committed.

## Headline numbers

Majority vote over k=20 samples, confidence = vote share, ECE with 10 bins.
1,000 test clues sampled with seed 20261021.

| set | run date | clue dates | model | n | top-1 | ECE | enum-fail share | refusals | cost |
|---|---|---|---|---|---|---|---|---|---|
| Cryptonite test | 2026-10-21 | 2000-10-18 – 2020-10-30 | `claude-haiku-5-5`, effort low | 1000 | **0.460** | **0.159** | 0.136 | 0 | $10.56 |
| post-cutoff | — | — | — | 0 | no files | — | — | — | — |

- **Calibration:** Haiku is over-confident in every bin; vote share
  overstates accuracy by 5–32 points. As (bin, count, mean confidence,
  accuracy): 0.0: 2, 0.05, 0.00 · 0.1: 28, 0.13, 0.07 · 0.2: 90, 0.23, 0.16 ·
  0.3: 133, 0.33, 0.20 · 0.4: 106, 0.43, 0.25 · 0.5: 119, 0.52, 0.34 ·
  0.6: 100, 0.62, 0.45 · 0.7: 67, 0.72, 0.45 · 0.8: 80, 0.82, 0.50 ·
  0.9: 275, 0.97, 0.86. A vote share above 0.9 is the only band where it is
  usually right. This is the gap a verifier should close: a mechanically
  checked parse is evidence that a vote share is not.
- **Enum-fail share 0.136:** about one sample in seven has the wrong length
  or no letters, so brief 002's cheapest check prunes ~14% of proposals
  before any parsing.
- **Run:** `20261021T155819Z-anthropic-d1625083…`, seed 20261021, k=20,
  0 refusals. It was resumed once at 128 workers (~48 clues/min, against
  ~15 at 32) from `20261021T153518Z-anthropic-6f528ee1…`; the 346 logged
  clues were replayed for free. $10.56 counts each logged call once (~$0.30
  of in-flight work lost at the restart isn't counted). **An offline stub
  replay reproduced every number, bin and per-clue result exactly.**
  Summary: `reports/000/test-haiku-5-5-1000.json`.
- **Contamination gap:** not measurable yet, because `data/postcutoff/` is
  empty. Plan (QUESTIONS.md item 5 answer): Opus on 200 post-cutoff + 200
  test clues, same seed, once the post-cutoff set exists.
- **Enum-fail share** is a diagnostic, not a filter: the share of samples
  with no letters or the wrong length for the enumeration, i.e. what brief
  002's first mechanical check would prune.
- **Pipeline check (not a result):** the hand-made `stub-20` fixture replays
  to top-1 0.700, ECE 0.175, enum-fail share 0.1075, every time, with no
  network.

## Why Haiku, not Opus or Ollama

- **What the LLM does here:** propose an answer from clue text plus
  enumeration (`answer-only-v1` prompt), 20 independent samples per clue.
  Majority vote gives the prediction and its vote share the confidence.
  There's no wordplay or verification yet.
- **Opus 5.5:** ~$0.0055 per sample, ~$110 projected. Stopped after 98
  clues ($10.80). At 0.918 it is near the ceiling on old clues, which leaves
  later briefs little room to show gains.
- **Ollama cloud, free tier:** the free plan allows **1 concurrent request**
  (ollama.com/pricing). Extra requests are queued or rejected with 429
  `too many concurrent requests`. On 2026-10-21 a one-word "hello" to
  `minimax-m3.1-flash` got no reply within 300 s, so 20,000 calls would
  take days. The backend stays in the code (`--backend ollama`, use
  `--workers 1`).
- **Haiku 5.5:** smoke test (10 clues × 4) gave top-1 0.30, ECE 0.475, at
  $0.00052 per sample (~1,000 output tokens, mostly reasoning, even at
  effort low). That's cheap, and its weakness leaves room to measure the
  verifier's gains in briefs 002–003.

## Reproduce

```bash
uv sync --extra llm
export ANTHROPIC_API_KEY=$(secret-tool lookup service env key ANTHROPIC_API_KEY)
uv run python -m ximenes.eval vote --set test --n 1000 --k 20 \
    --model claude-haiku-5-5
# resume a run that died, paying only for calls the log doesn't have:
uv run python -m ximenes.eval vote ... --log runs/<run-id>.jsonl
# replay offline, bit for bit:
uv run python -m ximenes.eval vote ... --backend stub --log runs/<run-id>.jsonl
```

## Appendix: partial Opus run (not a headline)

`claude-opus-5-5`, effort low, k=20, on the first **98** of the 1000 sampled
test clues: top-1 **0.918**, ECE **0.024**, 0 refusals, $10.80. Run date
2026-10-21; clue dates 2000-10-18 – 2004-01-27. Summary:
`reports/000/test-opus-5-5-partial-98.json`.

This measures recall of the oldest, most-reprinted public clues, not
solving. The run went through sampled indices in order, the test file is
sorted by date, and the run was stopped on cost (~$0.0055 per sample, ~$110
projected). It's kept as evidence that strong models look solved on old
public clues. All 98 records are timestamped 15:08–15:13 UTC, and no more
arrived before the run was killed: the shape of a rate limit (not diagnosed).

Reliability as (bin, count, mean confidence, accuracy): 0.3: 3, 0.33, 0.33 ·
0.4: 1, 0.45, 1.00 · 0.5: 3, 0.50, 0.33 · 0.6: 6, 0.64, 0.67 · 0.7: 4, 0.74,
0.75 · 0.8: 4, 0.81, 0.75 · 0.9: 77, 0.99, 1.00.

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................                                 [100%]
40 passed in 0.54s
== kit: GREEN
```

## Open questions

See `QUESTIONS.md` § Brief 000.

## Probability complete

**0.85.** Every build item and test in the brief exists and is green, the
headline ran live and replays bit for bit offline; the remaining risk is the
post-cutoff path, which is tested only on synthetic rows because no real
post-cutoff files exist yet.

## Handoff / next steps

- Brief 000 is done (`briefs/DONE`). Next: brief 001, which the author
  starts with `./start.sh 001`.
- Planned, not done: concurrent samples within a clue (brief 002, agreed
  with fable in `comms/`); Batches API and the Opus post-cutoff 200/200
  comparison, once `data/postcutoff/` has rows.
- Don't put API keys on a command line: argv shows up in `ps`.
