# Report — brief 000 (harness)

Status: **harness complete; headline run on the free Ollama model pending
`OLLAMA_API_KEY`.** Run summaries live in `reports/000/` without clue text
(Cryptonite clues are unlicensed newspaper text and this repo is public).
Full per-call logs are under `runs/`, which is not committed.

## Headline numbers

Majority vote over k=20 samples, confidence = vote share, ECE with 10 bins.
1,000 test clues sampled with seed 20261021.

| set | run date | clue dates | model | n | top-1 | ECE | cost |
|---|---|---|---|---|---|---|---|
| Cryptonite test | 2026-10-21 | — | `minimax-m3.1-flash` (Ollama cloud) | 1000 | *pending* | *pending* | free |
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

## Reproduce

```bash
uv sync --extra llm
export OLLAMA_API_KEY=$(secret-tool lookup service env key OLLAMA_API_KEY)
uv run python -m ximenes.eval vote --set test --n 1000 --k 20 \
    --model minimax-m3.1-flash --backend ollama
# resume a run that died, paying only for calls the log doesn't have:
uv run python -m ximenes.eval vote ... --backend ollama --log runs/<run-id>.jsonl
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

1. The author stores the key: `secret-tool store --label=OLLAMA_API_KEY service env key OLLAMA_API_KEY`.
2. Smoke test: `--set test --n 5 --k 2 --model minimax-m3.1-flash --backend ollama`.
3. Full run (command above). If the free tier rate-limits, lower `--workers`;
   resume with `--log`. Then fill in the headline row, copy the summary into
   `reports/000/` with `items` removed (no clue text), paste the kit output,
   append `000` to `briefs/DONE`, and commit with the headline number as a
   one-line message. `git pull --rebase` before pushing: another agent
   shares this repo.
4. `briefs/DONE` does **not** list 000 yet, on purpose.
