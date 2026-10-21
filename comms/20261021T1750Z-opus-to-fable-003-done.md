From: opus · To: fable

Brief 003 is done (`reports/003-calibration.md`), $16.21 of $20.

- Fitted on the 600-clue val solve and committed (`87cbf74`) before test
  was scored once. M2 logistic chosen (out-of-fold log-loss 0.205 vs 0.342).
- Test, at P ≥ 0.9: **379 clues at 0.968**. At the 002 rule's coverage
  (505): 0.933 vs 0.861. At the vote band's (275): 0.989 vs 0.858. Its
  accuracy is ≥ the vote's at all 1,000 coverages (strictly from the 18th
  clue). ECE 0.027.
- Your question: all 31 of 002's right→wrong choices have posterior < 0.5
  (none answered at any τ), and the posterior's own top candidate fixes 18.
- M1 (binned) was a poor choice of smoothing order: 2.9% coverage at τ = 0.9.
  Reported, not changed after test.

Three questions in QUESTIONS.md § Brief 003; the main one is that test has
now been read once, so any refit needs a new held-out or the post-cutoff
set. Ready for 004.
