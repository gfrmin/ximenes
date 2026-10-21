From: opus · To: fable

Brief 002 is done (`reports/002-proposer-loop.md`), $15.54 of the $25 cap.

- top-1 **0.552** vs the vote's 0.460 on the same 1,000 (+123 / −31).
- Verified set as your brief defines it: **505 at 0.861**, against the
  vote's ≥ 0.9 band of 275 at 0.858. My stricter pre-run reading gives 278
  at 0.777; it drops 227 clues that are right 0.965 of the time, and it
  admits low-definition `Ok`s. The report shows both.
- The minimum-oracle-score bands are monotone (0.25 / 0.82 / 0.90 / 0.96),
  which is good news for 003's calibration.
- A D6 bug: 38 synonym judgements were asked twice with different answers.
  Fixed with `memoized()`; the canonical replay (first-wins, explicit flag)
  reproduces the headline exactly.

Three questions under QUESTIONS.md § Brief 002 (verified-set definition for
003, a `judge_indicator` oracle for unlisted indicators, the formaliser's
cost). Ready for 003 when drafted.
