# Roadmap (briefs after 001 are sketches; each is drafted only when the
# previous one has merged)

| # | Brief | Headline number | Depends on |
|---|---|---|---|
| 000 | Harness, splits, logged instruments, vote baseline | top-1 + ECE on test vs post-cutoff | — |
| 001 | Typed DSL + non-executing verifier + coverage law | gold-parse coverage; mutant false-accept = 0 | 000 |
| 002 | Proposer loop: answers → wordplay → formalise → verify, with hinted retries | top-1 with verifier vs vote baseline, quick/hard split | 001 |
| 003 | Calibrated selective solver: posterior over candidates from vote share × verdict × oracle scores; acts point/set/abstain/escalate at pre-registered u_wrong ∈ {−5, −9} | risk–coverage AUC; selective accuracy @95% precision | 002 |
| 004 | Grid: loopy BP over slot/cell nodes with set answers as domains and verdicts as likelihoods; local search | fully-correct grid rate; frontier tokens per correct grid | 003 |
| 005 | Metacomputation: price computations in seconds/tokens; myopic VOC vs Dr.Fill confidence-gap vs attempt-all-first | expected score per unit time; "price of the floor" | 004, wald amendment |
| 006 | (deferred) Rejection-sample `Ok` parses to distil a small proposer | — | 002, mutants at 0 |

Stop rule after 001: if gold-parse coverage on val is far below ~30%, the
sound-by-grammar verifier is not worth building on; refocus on 003 with the
verdict as a weaker feature.
