# Working on ximenes

Read `DESIGN.md` first, then the brief you're on under `briefs/`. One brief
per session. Work on `master`.

Other agents share this repo. Read `AGENTS.md` (protocol), `STATUS.md` (who's
doing what, running jobs) and new files in `comms/` before starting. How
LLMs are used: `docs/LLM-USE.md`.

## Rules that are mechanically checked (`./kit/check.sh`, also CI)
- Tests in `tests/` pass. Tests from earlier briefs are not edited or
  deleted; if one must change, say so in the report and explain why.
- No numeric literals in `src/ximenes/` except 0 and 1 (`kit/lint_numbers.py`).
  Numbers go in `data/` tables with a `source` field.
- No `exec`, `eval`, `subprocess`, `importlib`, `pickle`, or network calls in
  `src/ximenes/` (`kit/lint_forbidden.py`). Oracle and LLM calls go through
  `src/ximenes/instruments.py` and are logged to `runs/` as JSONL.
- Nothing under `data/postcutoff/` is ever committed.

## Rules that are not checked, so follow them
- Never read, print, or copy anything under `data/postcutoff/`. Loaders may
  open it only inside `ximenes.eval` with `allow_postcutoff=True`, and only
  to compute a number.
- Smallest change that makes the test pass. No features the brief doesn't
  ask for. No refactors across the brief's boundary.
- Run `./kit/check.sh` before saying a brief is done and paste its output.

## Report format (end of each brief)
The headline number for the brief; the kit output; open questions; a
probability (0–1) that the brief is correctly complete, with one sentence of
reasoning.

## Style
- `uv` manages the environment: `uv sync`, `uv run ...`, `uv add <pkg>` (never `pip`).
  Commit `uv.lock` when it changes.
- Python 3.11+, type hints everywhere, `dataclass(frozen=True)` for kernel
  types, no mutable state in the kernel.
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
