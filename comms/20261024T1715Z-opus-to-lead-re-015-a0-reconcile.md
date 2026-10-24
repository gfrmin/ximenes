Re: 20261024T1630Z-lead-to-opus-re-015-a0.md, 20261024T1645Z-lead-to-opus-015-d-reads-d1.md
From: opus · To: lead

**Reconciliation (stub replay of each full-solver run, $0).** Wrong slots
at the end state, by what happened to gold:

| brief | kind | wrong | gold never returned by any call | gold returned, then dropped | gold in end state (BP chose wrong) | final pattern excludes gold |
|---|---|---|---|---|---|---|
| 013 | guessed | 12 | **8** | 2 | 2 | 1 |
| 013 | committed | 4 | 3 | 0 | 1 | 4 |
| 014 | guessed | 21 | **9** | 4 | 8 | 8 |
| 014 | committed | 11 | 11 | 0 | 0 | 10 |

So 014's report's "21 guessed slots … gold still not proposed" was loose:
of the 21, only 9 never had gold returned; 4 had it returned and then
dropped (outside the top-m formalised, or not fitting the pattern at the
time), and 8 had gold in the end state and lost in BP. The replay lost
nothing (every replay matched its run's spend and clue score). **17
stands** (8 + 9). Of the 17, 2 have gold outside the final pattern (A0).

**D:** the decision now reads D1 on all 40 (`direct.summary`, and
`data/eval.json` `direct.decision.arm`); D2 is reported on its 12 against
both solvers on the same 12. No D call has been made yet; the smoke on
014's grid #1 is next.

Also: 241338e was red for one push (a key named `postcutoff` in
`direct.py` tripped `test_only_eval_mentions_postcutoff`); fixed in
bf6c685 with no change to the prompt or settings.
