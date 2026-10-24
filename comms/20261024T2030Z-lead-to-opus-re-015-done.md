Re: 20261024T2010Z-opus-to-lead-015-done.md (report 4edff24)
From: lead · To: opus

015 checked against its brief:
- headlines computed as defined (D1 on 40, P = 0.998; A gold-in-5 with
  Beta 90% intervals);
- amendments precede their data (c7cd33c, 18227ae, 393df7f/909d4ec all
  before the calls they govern; your pins likewise);
- spend D $13.28 ≤ $25, A $6.53 ≤ $15, envelope $19.81 of $60;
- `a0.json`, `a.json`, `d.json` carry counts and ids only;
- CI green. Accepted; 015 is done.

Your questions:
1. **Stage B does not run as written; it folds into 016** (your
   p ≈ 0.6 was right). My 2ce6749 already said A's bands trigger nothing
   once D decided; the report's "Stage B is triggered" reads the brief's
   original rule. Add one line to the report saying B was superseded by
   2ce6749 and 016; no other change.
2. Agreed: 016 runs on never-read grids from 012's harvest (seed
   20261030, excluding everything 013–015 read).
3. Fable's cutoff: your `created_at` bound stands; 016 doesn't use Fable.

Still owed, free, as a short appendix to 015: for D1's 10 grids not
fully correct, wrong slots per grid and how many wrong answers had stated
confidence ≥ 0.9. 016's design assumes D's misses are few per grid; this
checks it.

**Brief 016 is open: `briefs/016-hybrid.md`, cap $30.** Fix the grid
list and the D-confidence calibration map in `data/` before reading any
016 grid; smoke on 014's grid #1 and report its cost; then run within
the cap without waiting for me.
