From: lead · To: opus

Re 241338e (D pinned): checked; prompt and settings precede every D call.
One amendment, before any D call on the 40 grids: with D2 eligible on 12
of 40 grids, "the best arm by fully correct grids" compares counts over
different denominators. **The decision rule now reads D1 on all 40.**
Report D2 on its 12 grids against both solvers on the same 12, as a
secondary that decides nothing. The brief says so (next commit). If your
code computes the decision from "best arm", change it to D1 before the
run; if you've already called any of the 40 beyond the smoke grid, tell
me before reading the result.
