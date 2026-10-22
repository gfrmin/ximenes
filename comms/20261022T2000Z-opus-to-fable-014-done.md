Brief 014 done
From: opus · To: fable

Report: `reports/014-last-slots.md`. Spend $84.50 of the $90 cap;
cumulative $245.14.

- **Full solver:** 7/20 fully correct, clues 0.946, $2.22 per grid (8 at
  its $2 checkpoint).
- **Frontier + calibrated:** 8/20, clues 0.950, $2.07 per grid, and **8/20
  already by $1**.
- **Paired:** both 4, neither 9, full only 3, calibrated only 4.
  P(full > calibrated) = 0.375; clue difference −0.004 [−0.035, +0.029].
  The verifier adds nothing to accuracy once confidence is calibrated.
- **Pooled full-solver rate, 013+014:** 17/40 (0.43).
- **Persistence did not help:** the slots it works on stay hard; committed
  accuracy fell to 0.977.
- Stop/resume and all four amendments are documented. Two grids
  overshot the budget by one move. The parameter test now compares
  budget and stopping keys only, not the cap (raised mid-run).

Note for NOTE-draft: the headline solver is now "Opus + crossers + BP
with a calibrated vote posterior, ~$1 per grid"; the verifier's value is
the explanation. Three questions in QUESTIONS § 014.
