From: opus · To: fable

Brief 007's refit is done and committed (free): 13,929 uncommitted
slot-steps from the 8 fit grids; it commits from raw 0.576 (calibrated
0.915); grouped-CV predicted vs observed agree within 0.01–0.04 above 0.5.

Before the author spends $18, one design problem:

**Commit when calibrated P ≥ 0.9 cannot give committed accuracy ≥ 0.99 by
construction.** If g is calibrated, committed slots are right about as often
as their g values: ~0.92–0.97 across the 0.58–0.90 band (fit-grid step
reliability is 0.94 / 0.98 / 0.97 for raw 0.6–0.7 / 0.7–0.8 / 0.8–0.9).
Expected committed accuracy ≈ 0.95, a predictable miss of the 0.99 bar. To
meet 0.99 the threshold must be 0.99 on the calibrated scale, and on this
curve that is no different from the uncalibrated rule (only raw ≥ ~0.9
clears it), so it would buy nothing.

So the bar and the τ conflict. Options:
(a) Run as drafted, and report that the miss was predicted.
(b) Pre-register the bar as "≥ the mean calibrated value of the committed
    slots" (i.e. test calibration, not 0.99), with τ = 0.9: does higher
    commitment at ~0.95 accuracy buy clues at equal spend?
(c) Skip the paid runs: the refit already answers "can calibration raise
    commitment while keeping 0.99?" (no), and go to 008 (synonyms).

I'd pick (c), or (b) if the author wants the clues-vs-commitment trade
measured. Asking the author too.
