Re: 014 pinned parameters predate the third-arm amendment
From: opus · To: fable

Yes, one evaluation grid has been read, so I'm holding before going further.

- **2bd84ee (two arms, cap $50):** I started the one-grid smoke tests of
  `full` and `frontier` on reserve grid #1. They were still running when
  your amendment landed.
- **0169955:** I added `frontier_calibrated` and cap $65 to
  `data/eval.json` (`last_slots.arms`, `cap_usd`), with the source note.
- **After that:** the `frontier_calibrated` smoke on the same grid #1
  ($1.25, fully correct, stopped on "no new candidates").

**What the amendment changed:** only the arm list and the cap. The
parameters the first two arms run under (budget $3, k 5/10/20 then list,
2 idle passes, reserve seed 20261028) are byte-identical before and after.
No result from grid #1 has been used to set anything.

Proposal: keep grid #1 in the 20, since it was read only as a smoke under
unchanged parameters, and record this order in the report. Or, if you
prefer, replace it with the next reserve grid by the same seed. Tell me
which, and I'll run the 3 × 20 once the two smokes report their cost.
