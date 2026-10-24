# Status

One section per agent; edit only your own (protocol: `AGENTS.md`).

## opus

- **Updated:** 2026-10-24 ~21:00 UTC
- **Working on:** brief 016 (the hybrid). Claims: `src/ximenes/hybrid.py`,
  `tests/test_016_*.py`, `reports/016*`, `data/hybrid-d-calibration.json`, `data/eval.json` `hybrid`.
- **Running jobs:** 016 full run (both arms, 40 grids), started ~21:05 UTC, `python -m ximenes.hybrid run --max-usd 30`, output `runs/016-full.out`; expected ~$15. Resume: same command with `--log <its jsonl>`.
- **Blocked on:** nothing.

## fable

- **Updated:** 2026-10-24 ~14:40 UTC
- **Working on:** nothing. From brief 015 on, the lead role is `lead`'s
  (`docs/LEAD.md`, started by the author with `./start-lead.sh`). My claims
  (`briefs/`, `docs/` except `reports/`, `DESIGN.md`, `QUESTIONS.md`
  answers, `README.md`, `setup.sh`, `start.sh`) pass to `lead`.
- **Running jobs:** 015 Stage A, all five arms on the 17 stuck slots (fable_high on its 9), started ~19:40 UTC, guard $5 per arm; smokes cost $0.57, projection ~$3. D done ($13.28).
- **Blocked on:** nothing.

## lead

- **Updated:** 2026-10-24
- **Working on:** 015 accepted (4edff24). Brief 016 (the hybrid)
  drafted and open, cap $30; Stage B folded into it.
- **Running jobs:** a watcher on `origin/master` (no spend).
- **Blocked on:** nothing; opus starts 016.
