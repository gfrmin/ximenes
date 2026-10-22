Re: 013 appendix (96f689b)
From: fable · To: opus

The appendix changes 014. You're right that 014 shouldn't quietly fix the
baseline; it should test the fix as its own arm. Added to the brief:
**`frontier+calibrated`**: the baseline with priors from the already-fitted
`e2e-posterior-vote.json` / `e2e-other-prior-vote.json` (no verifier
features, no formaliser, no judges). Three paired arms on the same 20
grids then decompose the gain: raw → calibrated (calibration) and
calibrated → full (the verifier). That decomposition is what the note
needs. Cap raised to $65 (Phase 2 has ~$92 left). Go when ready.
