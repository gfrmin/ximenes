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
CHARTER.md          one page, author-signed; what cannot change without a sitting
CLAUDE.md           instructions for the caged builder (Claude Code)
briefs/             one brief per builder session, numbered; each has a kit check and one number
kit/check.sh        the mechanical gate every PR must pass
src/ximenes/        kernel: types, DSL operator table, AST verifier, loaders, eval
tests/              laws (frozen per brief) incl. the exploit-mutation suite
data/lexicon/       indicator / abbreviation tables (seeded; extend from Deits & A&W)
data/postcutoff/    private, never committed: post-cutoff clues for clean eval
docs/               prior art, design notes
```

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
./kit/check.sh
```

## Status

Brief 000 (harness) not started. See `briefs/`.
