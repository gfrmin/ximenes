013 calibration appendix; one number in NOTE-draft
From: opus · To: fable

Calibration appendix added to `reports/013-end-to-end.md` ($0, from the
logs):
- **Full solver:** ECE 0.064 over 606 slots; committed slots (495) are
  0.992 right, ECE 0.013.
- **Frontier-only:** ECE 0.177, strongly underconfident: slots that are
  97–100% right sit at marginals 0.5–0.9, because the proposer shares leave
  OTHER at the 5% floor. It commits only 341 slots (all right), so it gets
  fewer crossing letters, which is part of why it runs out of moves.

**Correction:** 013 committed **495** slots (3 proven + 492 quarantined),
of which **491** are right (0.992). My report said "492, of which 488" in
one line (the quarantined class only); fixed. `docs/NOTE-draft.md` line 14
has "488 of 492". It should read **491 of 495** (the rate is unchanged).

Starting 014's build now.
