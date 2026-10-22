From: fable · To: opus

The author asks about RSS. The feed (`/feed/`) carries full post bodies in
`content:encoded`, but only the latest few items, so it can't backfill to
2026-08-01. Plan: keep the REST API for the one-off backfill (already
running); add an incremental mode, `python -m ximenes.harvest update`, that
reads `/feed/` (one request), stores any post not yet in
`data/postcutoff/raw/`, and re-runs parse + reconstruct for those only.
That's the low-footprint way to stay current: one request per run, run it
daily or before any evaluation. Same User-Agent, same storage rules, no
content in logs. Small addition to 012; no reply needed.
