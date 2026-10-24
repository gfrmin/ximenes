# Status

One section per agent; edit only your own (protocol: `AGENTS.md`).

## opus

- **Updated:** 2026-10-24 ~18:00 UTC
- **Working on:** brief 015 (A0, then D, then A; B needs the author's cap).
  Claims: `src/ximenes/residual.py`, `src/ximenes/direct.py`,
  `tests/test_015_*.py`, `reports/015*`, the `residual`/`direct` blocks of
  `data/eval.json` and `data/instruments.json`.
- **Running jobs:** 015 Stage A, all five arms on the 17 stuck slots (fable_high on its 9), started ~19:40 UTC, guard $5 per arm; smokes cost $0.57, projection ~$3. D done ($13.28).
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
- **Working on:** 015 checked: D1 30/40 vs solver 17/40, P = 0.998.
  Stage A finishing as a secondary (no B). Drafting 016 (hybrid).
- **Running jobs:** a watcher on `origin/master` (no spend).
- **Blocked on:** opus's 015 report.
