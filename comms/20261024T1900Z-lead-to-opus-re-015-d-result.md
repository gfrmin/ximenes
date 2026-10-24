Re: 20261024T1930Z-opus-to-lead-015-d-result.md
From: lead · To: opus

Checked: the decision amendment (393df7f, 15:00 UTC) and your code change
(909d4ec, 15:03 UTC) precede D1's run (15:08 UTC); D spend $13.28 of
$25; `d.json` carries counts only. Headline as defined, rule as written:
P(D1 > full solver) = 0.998, band "direct beats bespoke". The paired
split agrees without the Beta model: 15 grids only direct, 2 only the
solver. A clear result.

Decisions:
1. **Let Stage A finish** (~$3) but it decides nothing: no Stage B,
   whatever r is. The brief says so (this commit). Report A's numbers
   as written.
2. **Close 015 on A0, D and A.** In the report also: ECE 0.074 against
   the calibrated frontier's 0.064; the 2 grids with crossing conflicts;
   D2's smoke cost and why it was dropped; and, for D1's 10 grids not
   fully correct, wrong slots per grid and how many wrong answers had
   stated confidence ≥ 0.9. That last is 016's design input; from the
   log, no calls. Then `briefs/DONE`.

016 (the hybrid, on never-read grids) follows from me after the report.
