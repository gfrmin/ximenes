# Report — brief 000 (harness)

Status: **harness complete; headline run on `claude-haiku-5-5` in progress
(started 2026-10-21 ~15:40 UTC, ~$10 projected).** Run summaries live in `reports/000/` without clue text
(Cryptonite clues are unlicensed newspaper text and this repo is public).
Full per-call logs are under `runs/`, which is not committed.

## Headline numbers

Majority vote over k=20 samples, confidence = vote share, ECE with 10 bins.
1,000 test clues sampled with seed 20261021.

| set | run date | clue dates | model | n | top-1 | ECE | cost |
|---|---|---|---|---|---|---|---|
| Cryptonite test | 2026-10-21 | — | `claude-haiku-5-5`, effort low | 1000 | *running* | *running* | ~$10 |
| Cryptonite test (**partial, biased subset**) | 2026-10-21 | 2000-10-18 – 2004-01-27 | `claude-opus-5-5`, effort low | 98 | 0.918 | 0.024 | $10.80 |
| post-cutoff | — | — | — | 0 | no files | — | — |
| `stub-20` fixture (hand-made votes; checks the pipeline, not a model) | 2026-10-21 | synthetic | `hand-fixture` | 20 | 0.700 | 0.175 | — |

- **Contamination gap:** not measurable yet, because `data/postcutoff/` is
  empty. Opus's 0.918 on public 2000–2004 Times clues fits memorisation as
  well as solving; only the post-cutoff row can tell the two apart.
- **The Opus partial is biased.** The run worked through the sampled indices
  in order, and the test file is sorted by date, so the 98 finished clues are
  the oldest. I stopped it on cost: ~$0.0055 per sample, ~$110 for the full
  run. All 98 records are timestamped 15:08–15:13 UTC, and the process made
  no progress after that until it was killed (likely rate-limit backoff;
  not diagnosed).
- Opus partial reliability, as (bin, count, mean confidence, accuracy):
  0.3: 3, 0.33, 0.33 · 0.4: 1, 0.45, 1.00 · 0.5: 3, 0.50, 0.33 ·
  0.6: 6, 0.64, 0.67 · 0.7: 4, 0.74, 0.75 · 0.8: 4, 0.81, 0.75 ·
  0.9: 77, 0.99, 1.00. Full bins in `reports/000/test-opus-5-5-partial-98.json`.

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
    --model claude-haiku-5-5 --workers 32
# resume a run that died, paying only for calls the log doesn't have:
uv run python -m ximenes.eval vote ... --log runs/<run-id>.jsonl
# replay offline, bit for bit:
uv run python -m ximenes.eval vote ... --backend stub --log runs/<run-id>.jsonl
```

## Kit output

*(pasted at completion)*

## Open questions

See `QUESTIONS.md` § Brief 000.

## Probability complete

*(at completion)*

## Handoff / next steps (for whoever picks this up)

1. The Haiku run writes `runs/<run-id>.json` when it finishes. If it dies,
   resume with the same command plus `--log runs/<run-id>.jsonl`; logged
   calls are replayed for free.
2. Then fill in the headline row, copy the summary into `reports/000/` with
   `items` removed (no clue text), paste the kit output, append `000` to
   `briefs/DONE`, and commit with the headline number as a one-line message.
   `git pull --rebase` before pushing: another agent shares this repo.
3. `briefs/DONE` does **not** list 000 yet, on purpose.
4. Don't put API keys on a command line (e.g. `curl -H "Authorization: ..."`):
   they show up in `ps`. Pass headers via a file.
