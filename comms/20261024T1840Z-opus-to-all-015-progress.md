From: opus · To: lead, all

015 progress (opus's session is pausing at a usage limit; the D1 run
continues under nohup):
- A0 done and pushed (`reports/015/a0.json`): 17 stuck slots; gold in W
  9/17, in W∩pattern 8/17; generator+verifier gold-in-5 1/17.
- D smokes: D1 $0.37, D2 $1.57 → D2 dropped (brief rule).
- D1 on 40 grids: 17/40 calls returned so far, $3.80, all end_turn.
  Outcomes not read yet. Output: `runs/015-d1-full.out` and
  `runs/20261024T150818Z-direct-D1-anthropic-*.json` when finished.
  Resume if it stops: `uv run python -m ximenes.direct run --arm D1
  --max-usd 23 --log runs/20261024T150818Z-direct-D1-anthropic-4d99a2ae6d9e4e4caee13288550efea3.jsonl`
- Left: D summary (`python -m ximenes.direct summary`), Stage A (smoke 3
  slots per arm, then arms within $15), report 015, briefs/DONE.
