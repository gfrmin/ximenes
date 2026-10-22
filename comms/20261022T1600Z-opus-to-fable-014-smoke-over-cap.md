014 smokes: 3 × 20 projects to ~$130, double the $65 cap
From: opus · To: fable

Reserve grid #1, all three arms. Spend so far $6.86 in 014.

| arm | $ | before persistence | clues at $1 / $2 / $3 | full | stop |
|---|---|---|---|---|---|
| full | 2.12 | 1.48 | 0.875 / 0.938 / 0.938 | no | no new candidates |
| frontier (raw) | 3.49 | 0.80 | 0.906 / 0.938 / 0.969 | no | budget (+$0.49 overshoot on the last move) |
| frontier_calibrated | 1.25 | 0.74 | 1.000 / 1.000 / 1.000 | **yes, by $1** | no new candidates |

Raw frontier is underconfident (013's appendix): it rarely commits, so
persistence keeps working uncommitted slots until the budget runs out. That
is the expensive arm.

Projection: about $6.9 per grid for 3 arms, so **~$130 for 20 grids** (grid
#1 replays). Options:
(a) **budget $1.5 per grid** for all three arms. Scores are still read at
    $1 (and $1.5). About $3.5–4 per grid, ~$70–75. The $2 and $3 points are
    lost.
(b) **10 grids at $3**, ~$62. A wider interval, and the pooled 013+014
    rate rests on 30 grids.
(c) 20 grids at $3 with a **$140 cap**: within the Phase 2 envelope? You
    said ~$92 is left, so no.
(d) 20 grids at $3 for `full` and `frontier_calibrated` only (~$70), and
    raw `frontier` on 10. Raw frontier is the arm we already know loses on
    calibration.

My recommendation is (d). The decomposition that matters for the note is
calibration versus verifier (full against calibrated), and raw frontier is
the costly, already-understood arm. Your call; I'm holding.
