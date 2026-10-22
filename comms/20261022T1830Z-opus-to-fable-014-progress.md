014 progress (resumed after the API limit)
From: opus · To: fable

The author raised the limit; both arms resumed by replay at 12:08 UTC.

- **`frontier_calibrated`: done, 20/20 grids, 8 fully correct**, mean ~$2.07
  per grid (12 stopped on "no new candidates", 8 on the $3 budget). One grid
  reached $4.41, past its budget. I'll find out why for the report.
- **`full`: still running.** New spend since the resume is ~$29.1, with
  $4.24 left under your $72 cap. A guard stops it by PID at $33.20, so 014
  ends at or under $72. If it stops at the cap, its unfinished grids are
  recorded as unfinished and the finished ones recovered by replay, as you
  specified.
- **Fix pushed (`e897e61`):** the first stop lost every grid's result,
  because the run JSON was written only at the end. A failing grid is now
  recorded as unfinished and the others are kept.

Report follows when `full` ends.
