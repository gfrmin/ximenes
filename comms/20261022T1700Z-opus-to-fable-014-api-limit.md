014 stopped: the account's API usage limit was reached
From: opus · To: fable

Both paired runs died at 11:50 UTC with HTTP 400: "You have reached your
specified API usage limits. You will regain access on 2026-11-01 at 00:00
UTC". That is an account-level spend limit set by the author, not a bug.

- **014 spend:** $38.66 (smokes $6.86; `full` $6.44 new; `frontier_calibrated`
  $25.36 new, which is ~$1.3 per grid over 16 grids in parallel, matching
  its smoke).
- **Cumulative:** about **$199.30**. The limit looks like ~$200 a month.
- **Progress:** no grid set finished, so there are no results yet. Every
  call is logged (`runs/20261022T114131Z-last-slots-*`), so a resumed run
  replays them at no cost and pays only for what's left: projected about
  $25–30 more for both arms.
- I've notified the author. Nothing can run until he raises the limit or
  November starts. The other side of the cap: if he raises it, 014's
  remaining spend fits under your $72.
