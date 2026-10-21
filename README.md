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

```bash
./setup.sh     # venv, deps, downloads + verifies Cryptonite and the wordplay sample, runs the kit
./start.sh     # opens Claude Code on the next brief not listed in briefs/DONE
```

`./start.sh 001` picks a brief; anything after it is passed to `claude`
(e.g. `./start.sh 001 --permission-mode auto`). Each brief ends by appending
its number to `briefs/DONE`, so `./start.sh` with no argument always opens the
next one. Set `ANTHROPIC_API_KEY` if you want the builder to run real proposer
calls; otherwise it builds against the stub backend and tells you the command
for the full run.

## Status

Brief 000 (harness) ready to start. See `briefs/ROADMAP.md`.
