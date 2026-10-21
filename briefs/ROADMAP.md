# Roadmap (briefs after 001 are sketches; each is drafted only when the
# previous one has merged). Framing: `docs/GAME.md`.

| # | Brief | Headline number | Depends on |
|---|---|---|---|
| 000 | Harness, splits, logged instruments, vote baseline | top-1 + ECE on test vs post-cutoff | — |
| 001 | Typed DSL + non-executing verifier + coverage law | gold-parse coverage; mutant false-accept = 0 | 000 |
| 002 | Proposer loop: answers → wordplay → formalise → verify, with hinted retries | top-1 with verifier vs vote baseline, quick/hard split | 001 |
| 003 | `Hyp` relation with semiring annotations (N[X] coverage, Why over oracle calls); `propagate` as semi-join; oracle calibration on val | exact-solve rate (singleton surviving set containing the truth); calibration curve P(correct \| quarantine reasons) | 002 |
| 004 | Grid: `Slot`/`Dom`, arc consistency over crossers, nogoods, re-propose with pattern on empty domains | fully-correct grid rate; share of solves *proven* vs *quarantined*; frontier tokens per correct grid | 003 |
| 005 | `wald` pack: price moves in seconds/tokens; value of computation (Hay et al.) vs MRV vs Dr.Fill confidence gap vs attempt-all-first; stopping rule for submit | expected score per unit time; "price of the floor" | 004, wald amendment |
| 006 | (deferred) Rejection-sample proven parses to distil a small proposer | — | 002, mutants at 0 |

Stop rule after 001: if gold-parse coverage on val is far below ~30%, the
sound-by-grammar verifier is not worth building on; refocus on 003 with the
verdict as a weaker feature.

Shared with `hkaddresses` (by design, once 003 exists): the `Hyp` kernel,
lattice tokeniser, alias tables, Ok/Quarantine. Not shared: the grammar.
