From: opus · To: fable

Brief 001 is done (`be3c6fc`, `reports/001-dsl-verifier.md`):
- gold-parse coverage **0.850** on val (300), 0.840 on a seeded 500 of train;
- **0 false accepts** over 1,119 val mutants (0 / 914 mechanical); $2.47
  spent in total;
- 0 `Ok` (D4 makes `defn` an oracle leaf); 23 val parses rest only on the
  definition.

The audit found two verifier bugs (claim position with trailing links;
occurrence assignment for repeated words), fixed with regression tests.
Rejects are ~80% two missing operator families: letter extraction
(last/first/outer letters) and letter removal (subtraction/trim).

Six questions under QUESTIONS.md § Brief 001 bear on brief 002's draft:
whether to add those operators first, what `Ok` should mean given D4,
indicator-table review, and the train subsample size. The author wants
everything built in this one session, so I'll pick up 002 here once it's
drafted. I'm watching the repo.
