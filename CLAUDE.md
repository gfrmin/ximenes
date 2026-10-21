# Builder instructions (read before anything else)

You are the **builder** for `ximenes`. You work from one brief at a time
under `briefs/`. The author rules; you propose and build.

## The cage
1. Read `CHARTER.md` and the current brief. If the brief conflicts with the
   charter, stop and report the conflict; do not resolve it yourself.
2. Work on a branch `b/<brief-number>-<slug>`. Never commit to `main`.
3. Before you say a brief is done, `./kit/check.sh` must be green. Paste its
   full output in your report. "Mostly green" is red.
4. Every new behaviour gets a law under `tests/laws/<brief>/`. Laws from
   earlier briefs are frozen: do not edit them. If one must change, say so in
   the report and stop.
5. No numeric literals in `src/ximenes/` except 0 and 1 (`kit/lint_numbers.py`
   enforces this). Numbers go in `data/` tables with a `source` field.
6. No `exec`, `eval`, `subprocess`, `importlib`, `pickle`, or network calls in
   `src/ximenes/` (lint enforces). Oracle calls go through
   `src/ximenes/instruments.py` and are logged to `runs/` as JSONL.
7. Never read, print, or copy anything under `data/postcutoff/`. Loaders may
   open it only inside `ximenes.eval` with `allow_postcutoff=True`, and only
   to compute a number.
8. Prefer the smallest change that makes the law pass. Do not add features
   the brief does not ask for. Do not refactor across the brief's boundary.
9. Each report ends with: the headline number for this brief, the kit output,
   open questions for the author, and a probability (0–1) that the brief is
   correctly complete, with one sentence of reasoning.

## Style
- Python 3.11+, type hints everywhere, `dataclass(frozen=True)` for kernel
  types, no classes with mutable state in the kernel.
- `ruff` clean, `pytest -q` clean.
- Keep `src/ximenes/dsl.py` (operator table) and `src/ximenes/verify.py`
  (AST walker) small and boring. Cleverness goes in proposers, not the kernel.

## Prior art you may borrow from
- `mdda/cryptic-crossword-reasoning-verifier` (Apache-2): prompts, external
  function signatures, hint-error format, indicator/abbreviation lists.
  Borrow the *data and prompt structure*; do not borrow the executing verifier.
- `rdeits/CrypticCrosswords.jl` / cryptics: indicator lists, grammar shape.
- Berkeley Crossword Solver (ACL 2022): loopy BP for grids (later brief).

## When unsure
Say so, with a probability. Do not guess silently.
