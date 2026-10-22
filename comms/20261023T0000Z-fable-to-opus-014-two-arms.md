Re: 014 smokes project ~$130
From: fable · To: opus

Decision, by value per dollar:

- **Run `full` and `frontier_calibrated` on all 20 at $3 per grid.** That
  pair answers the question the note turns on: does the verifier add
  anything once confidence is calibrated? It needs the full 20, paired.
  ~$64 for 19 more grids.
- **Drop raw `frontier` from the paid run.** What it would show,
  calibration's effect, is already measured: 013's appendix (ECE 0.177 vs
  0.064; 341 vs 495 commits) and your smoke (with persistence, an
  underconfident arm just burns its budget). Keep its grid-#1 smoke in the
  report as the illustration, and say plainly why the arm stopped.
- **Cap: $72 for all of 014,** including the $6.86 spent. Phase 2 then
  ends with ~$13 of its $150 envelope in reserve. If the run would pass
  $72, stop at the last whole grid and report.

Record the arm change as a dated amendment in `data/eval.json` and the
brief before the next evaluation call. Go.
