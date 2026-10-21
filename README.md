# ximenes

A cryptic-crossword clue solver built as **propose → verify → decide**, where
the verifier is sound by grammar and the decision layer is Bayesian.

- **Propose** (untrusted): an LLM suggests candidate answers and wordplay
  parses.
- **Verify** (trusted): a small typed DSL. Parses are written in Python
  *syntax*, parsed to an AST, and **never executed**. Only declared operators
  exist. Every non-link clue token must be consumed exactly once
  (the *coverage law*). Verdicts are `Ok` / `Quarantine` / `Reject`, never a
  bare "verified".
- **Decide** (Bayesian search): hypotheses live in a relation with
  provenance annotations; crossers prune them by propagation; the only
  terminal act is *submit*. The decision problem is metacomputation: which
  computation next, when to pay for an oracle, when to stop. See
  `docs/GAME.md`.

Named after Ximenes (D. S. Macnutt), who wrote down what makes a clue fair.

## Why this and not "ask a frontier model"

Frontier ensembles already beat humans on speed (Darmok, Times Championship
final, Oct 2026). What nobody has published for cryptics is: a verifier that
can't be fooled, calibrated probabilities with abstention, grid inference that
uses *verified* wordplay as evidence, and a principled clue-ordering policy.
That is the target. See `docs/PRIOR-ART.md`.

## Layout

```
DESIGN.md           the rules the code is built to; which are mechanically checked
CLAUDE.md           instructions for Claude Code sessions
briefs/             one brief per session, numbered; each has tests and one headline number
kit/check.sh        lints + tests; runs in CI on every push
src/ximenes/        kernel: types, DSL operator table, AST verifier, loaders, eval
tests/              incl. the exploit-mutation suite; earlier briefs' tests are never edited
data/lexicon/       indicator / abbreviation tables (seeded; extend from Deits & A&W)
data/postcutoff/    private, never committed: post-cutoff clues for clean eval
docs/               prior art (PRIOR-ART.md), the decision-theoretic framing (GAME.md)
setup.sh, start.sh  turnkey: fetch data + check, then open Claude Code on the next brief
```

## Quick start

Needs `uv`, `git`, `curl`, `unzip`, and Claude Code on PATH.

```bash
./setup.sh     # uv venv + deps, downloads + verifies Cryptonite and the wordplay sample, runs the kit
./start.sh     # opens Claude Code on the next brief not listed in briefs/DONE
```

`./start.sh 001` picks a brief; anything after it is passed to `claude`
(e.g. `./start.sh 001 --permission-mode auto`). Each brief ends by appending
its number to `briefs/DONE`, so `./start.sh` with no argument always opens the
next one. Set `ANTHROPIC_API_KEY` if you want the builder to run real proposer
calls; otherwise it builds against the stub backend and tells you the command
for the full run.

## Status

- Brief 000 done (2026-10-21): vote baseline, `claude-haiku-5-5` at effort
  low on 1,000 Cryptonite test clues, k=20: **top-1 0.460, ECE 0.159**,
  over-confident in every bin. `reports/000-harness.md`.
- Brief 001 done (2026-10-21): typed DSL and non-executing verifier.
  **Gold-parse coverage 0.850** on the 300-clue wordplay val sample (0.840 on
  500 of train), **0 false accepts over 1,119 mutants**, $2.47. Wordplay
  fully mechanical for 7.7%; most parses rest on a synonym leaf. Rejects are
  ~80% two missing operator families. `reports/001-dsl-verifier.md`.
- Brief 002 done (2026-10-21): propose → verify → decide on the same 1,000
  test clues. **Top-1 0.552 vs 0.460** for the vote; the pre-registered
  verified set is **505 clues at 0.861** against the vote's ≥0.9 band of 275
  at 0.858 (1.8× the coverage at the same precision). $15.54.
  `reports/002-proposer-loop.md`.
- Brief 003 done (2026-10-21): a posterior fitted on a 600-clue val solve
  and read once on test. **At P ≥ 0.9 it answers 37.9% of test clues at
  0.968 (ECE 0.027)** and beats vote share at every coverage; at brief 002's
  coverage, 0.933 vs 0.861. $16.21. `reports/003-calibration.md`.
- Brief 004 done (2026-10-21): grids. Layouts reconstructed from Cryptonite
  clue lists (36/100 unique, 0 ambiguous). On 20 grids: **0 fully correct,
  letters 0.733, clues 0.712 vs 0.513 solved alone**; committed slots right
  99.1% of the time, guessed slots 54%. $0.94 per grid. `reports/004-grid.md`.
- Next: brief 005 (metacomputation: value of computation under a price).
  `briefs/ROADMAP.md`.
