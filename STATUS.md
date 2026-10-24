# Status

One section per agent; edit only your own (protocol: `AGENTS.md`).

## opus

- **Updated:** 2026-10-22 ~13:30 UTC
- **Working on:** nothing; brief 014 done (`reports/014-last-slots.md`). Claims released.
- **Running jobs:** none.
- **Blocked on:** next brief.

## fable

- **Updated:** 2026-10-24 ~14:40 UTC
- **Working on:** nothing. From brief 015 on, the lead role is `lead`'s
  (`docs/LEAD.md`, started by the author with `./start-lead.sh`). My claims
  (`briefs/`, `docs/` except `reports/`, `DESIGN.md`, `QUESTIONS.md`
  answers, `README.md`, `setup.sh`, `start.sh`) pass to `lead`.
- **Running jobs:** none.
- **Blocked on:** nothing.

## lead

- **Updated:** 2026-10-24
- **Working on:** lead for brief 015 (`docs/LEAD.md`). Claims (from
  `fable`): `briefs/`, `docs/` except `reports/`, `DESIGN.md`, answers in
  `QUESTIONS.md`, `README.md`, `setup.sh`, `start.sh`.
- **Amended before any data:** 015's A0 makes no calls (verifier admits
  only generator-made parses); "stuck slot" = gold never proposed; D's
  best-arm selection stated; A's middle band decided by `lead`.
- **Running jobs:** a watcher on `origin/master` (no spend).
- **Blocked on:** `opus` starting 015 (A0 first).
