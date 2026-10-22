From: opus · To: fable

Brief 006 is done, with a negative headline (`reports/006-commitment.md`),
$9.15. Cumulative: $103.18.

- Calibrated commit on 10 fresh grids: committed 162/290 (56%, double
  004–005), but **accuracy 0.895, below the 0.99 bar**; clues at $0.94
  0.658. 0 committed-only grids.
- Why: the map was fitted on final-state marginals and applied mid-run.
  Commit-time reliability on evaluation is 0.63 / 0.90 / 0.92 / 0.98 for
  raw 0.5–0.6 / 0.6–0.7 / 0.7–0.8 / 0.8–0.9, against the map's 0.98.
  All-step reliability on the fit grids would have committed from about
  0.7.
- The uncalibrated comparison can't be made fairly offline: under the old
  rule the patterns differ, so the re-proposals were never logged. Reported
  as such, not as a win.
- Paired P1 on 005's grids: 0.693 vs VOC 0.706 at $0.94 (1–3 points
  everywhere; within noise). Added to the 005 report under a dated heading.
- A recording bug (tops read after the step's commits) found and fixed; it
  touched no score, commit or table.

QUESTIONS.md § Brief 006: refit on commit-time marginals (~$9, seed
20261025) or go to the synonym table; and whether to pair the uncalibrated
rule live. The author is asked before paid runs.
