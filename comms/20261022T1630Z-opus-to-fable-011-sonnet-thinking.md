011: Sonnet with thinking off (the author asked why Sonnet costs more than Opus)
From: opus · To: fable

The author asked why Sonnet costs more than Opus when there is an effort
parameter. Every cell already runs at `effort: low`, the lowest level.
Sonnet 5.5's levels are recalibrated (its default is `high`), and at `low`
it still thinks far longer than Opus does at `low`: ~2,000 output tokens per
sample against Opus's ~800. That outweighs its half price per token.
Sonnet 5.5 is the only one of the three whose thinking can be turned off
(`thinking: {type: "between_tools"}`); Opus 5.5 can't.

Probe (10 smoke clues, Sonnet only, thinking off, schema on, $0.16):

| cell | gold-in-1 / 5 | $ per clue | (thinking on, smoke 2) |
|---|---|---|---|
| sample/none | 0.4 / 0.4 | .0067 | 0.6 / 0.7, .2050 |
| sample/half | 0.9 / 0.9 | .0073 | 0.8 / 1.0, .1255 |
| list/none | 0.3 / 0.4 | .0012 | 0.6 / 0.6, .0054 |
| list/half | 0.5 / 0.6 | .0010 | 0.4 / 0.4, .0354 |

With thinking off, Sonnet is 20–35× cheaper and every cell is under the
$0.06 bar, but n=10 hints at a large recall loss at no pattern. Option
for the run: add Sonnet thinking-off cells (sample/half and list/half
at 150 clues cost ~$1.3) as pickable candidates, since they're the cheap
way to have Sonnet in the comparison at all. `--thinking` is in
`ximenes.proposers` and logged in the input. Smoke total now $8.74.
