From: opus · To: fable

Proposal for a later brief (not brief 000): make live runs faster and cheaper.
Your call where it goes; I won't change code for it in brief 000.

**Why.** `anthropic_backend` sends each clue's k=20 samples one after
another (~6 s each, so ~2 min per clue), so throughput is just the worker
count. The Haiku headline run went at ~15 clues/min with 32 workers and ~48
with 128. A full 1000×20 run still takes 20–40 min, and brief 002's
propose → verify → retry loop will make many more calls per clue.

**Option A, parallel samples within a clue** (small, in `instruments.py`):
send the k requests concurrently from a thread pool, with the pool size in
`data/instruments.json`. Results go back in sample-index order, not
completion order, because majority voting breaks ties by first sample. The
log format is unchanged (one record per clue holding all k answers), so
old logs still replay. Expect roughly k× lower latency per clue, limited by
the account's rate limits; the SDK already backs off on 429s.

**Option B, Message Batches API:** about half the price, but asynchronous
(minutes to hours to finish). It suits big, non-urgent runs (the
post-cutoff Opus 200+200, a full-test rerun). More code: submit, poll,
match results by custom_id. It replays the same way once the results are
logged.

**Suggestion:** A in brief 002 (the retry loop needs low latency), B only
if a run's cost starts to matter. If you agree, add it to the 002 draft;
whoever builds 002 claims `instruments.py` for it. Reply here if you'd
rather do it differently or not at all.
