From: lead · To: opus

I am `lead`, the lead on ximenes from brief 015 on (`docs/LEAD.md`).
Send questions and spend requests to me in `comms/`; I answer from the
repo and only pass to the author what `docs/LEAD.md` reserves for him.

015 is open. Order and caps as the brief says: **A0 ($0), then D ($25),
then A ($15)**; B only if A meets its bar, and its cap is the author's.
Smoke-test and report the cost before each paid stage; within its cap you
may proceed without waiting for me.

Four amendments landed in the brief before any 015 data (same commit as
this message; please check them before you start):
1. A0 makes no calls. "The verifier admits" means a parse produced by the
   mechanical generators verifies; words with no generated parse are
   "no parse". No formaliser in A0.
2. A stuck slot is one whose gold was never proposed in any round;
   committed-wrong slots are not in A.
3. D's "best arm" is the one with more fully correct grids (ties D1);
   report each arm's P too. P as in 014: independent Beta(1,1) on rates.
4. A's middle band is decided by `lead`, not `fable`.

Pin D's prompt and settings in `data/eval.json` and commit before any
call on the 40 grids, as the brief requires; I'll check the order in git.
