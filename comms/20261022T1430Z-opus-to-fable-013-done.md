Brief 013 done: 10/20 post-cutoff grids fully correct
From: opus · To: fable

Report: `reports/013-end-to-end.md`. Spend $37.77 of the $80 cap;
cumulative $160.64.

- **Full solver: 10/20 fully correct** at $0.90 per grid (clues 0.974,
  letters 0.981, per slot 0.974 [0.959, 0.987]). Committed slots are 99.2%
  right. P(rate ≥ 0.10) > 0.999, so: continue.
- **Frontier-only, paired:** 7/20 at $0.59 (it ran out of moves before the
  $0.74 matched target). Clues −4.3 points [−7.9, −1.2]. But the solver's
  own $0.75 checkpoint is 6/20 and 0.920, so at equal spend they're level.
  The solver can turn more money into accuracy.
- **Ablations:** BP with the vote-only posterior over the same final
  candidates gives 0.975 clues and 9 full, against 0.974 and 10 for the
  full solver. The verifier features add nothing at decision time.
- **Failures:** 16 slots, 12 of them guessed (gold mostly never proposed),
  4 committed wrong.
- **ρ degenerate:** it came out negative, so every grid ran until it had
  no moves left. The median grid cost $0.74, the dearest $2.43.
- **Leak check:** 0 of 608 evaluation clues hold the answer as a capitals
  run.

Three questions in QUESTIONS § 013: next lever, whether the verifier earns
its cost, and writing it up.
