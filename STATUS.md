# Status

One section per agent; edit only your own (protocol: `AGENTS.md`).

## opus

- **Updated:** 2026-10-24 ~18:00 UTC
- **Working on:** brief 015 (A0, then D, then A; B needs the author's cap).
  Claims: `src/ximenes/residual.py`, `src/ximenes/direct.py`,
  `tests/test_015_*.py`, `reports/015*`, the `residual`/`direct` blocks of
  `data/eval.json` and `data/instruments.json`.
- **Running jobs:** 015 D1 on all 40 grids, started ~15:10 UTC (`python -m ximenes.direct run --arm D1 --max-usd 23`, output `runs/015-d1-full.out`), expected ~$15, ~30 min. Smokes done: D1 $0.37, D2 $1.57 (D2 dropped: D1+D2 projects ~$34 > $25). If anything stops mid-run: rerun the same command with `--log runs/<that run>.jsonl` (replays finished grids free).
- **Blocked on:** nothing.

## fable

- **Updated:** 2026-10-24 ~14:40 UTC
- **Working on:** nothing. From brief 015 on, the lead role is `lead`'s
  (`docs/LEAD.md`, started by the author with `./start-lead.sh`). My claims
  (`briefs/`, `docs/` except `reports/`, `DESIGN.md`, `QUESTIONS.md`
  answers, `README.md`, `setup.sh`, `start.sh`) pass to `lead`.
- **Running jobs:** 015 D1 on all 40 grids, started ~15:10 UTC (`python -m ximenes.direct run --arm D1 --max-usd 23`, output `runs/015-d1-full.out`), expected ~$15, ~30 min. Smokes done: D1 $0.37, D2 $1.57 (D2 dropped: D1+D2 projects ~$34 > $25). If anything stops mid-run: rerun the same command with `--log runs/<that run>.jsonl` (replays finished grids free).
- **Blocked on:** nothing.

## lead

- **Updated:** 2026-10-24
- **Working on:** lead for brief 015. A0 checked (1c0e2d1). Middle-band
  rule for Stage A added to the brief before any A call. Asked `opus`
  to reconcile 17 stuck slots with 014's 21 before Stage A.
- **Running jobs:** 015 D1 on all 40 grids, started ~15:10 UTC (`python -m ximenes.direct run --arm D1 --max-usd 23`, output `runs/015-d1-full.out`), expected ~$15, ~30 min. Smokes done: D1 $0.37, D2 $1.57 (D2 dropped: D1+D2 projects ~$34 > $25). If anything stops mid-run: rerun the same command with `--log runs/<that run>.jsonl` (replays finished grids free).
- **Blocked on:** nothing.
