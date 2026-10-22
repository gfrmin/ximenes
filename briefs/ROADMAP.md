# Roadmap (briefs after 001 are sketches; each is drafted only when the
# previous one has merged). Framing: `docs/GAME.md`.

| # | Brief | Headline number | Depends on |
|---|---|---|---|
| 000 | Harness, splits, logged instruments, vote baseline | top-1 + ECE on test vs post-cutoff | — |
| 001 | Typed DSL + non-executing verifier + coverage law | gold-parse coverage; mutant false-accept = 0 | 000 |
| 002 | Proposer loop on real clues: new operators, table-review rule, oracle instruments, concurrent samples, fixed decision rule | top-1 vs 0.460 on the same 1,000; verified-set size and accuracy | 001 |
| 003 | Calibrated posteriors fitted on a val solve, evaluated once on 002's test run; `judge_indicator`; point/set/abstain decision layer; `Hyp` schema named | risk–coverage on test; coverage and accuracy at P ≥ 0.9 vs vote share and the 002 rule; ECE | 002 |
| 004 | Grid: ipuz loader; reconstruct Cryptonite layouts from numbering + answers; loopy BP over `Hyp` rows with an OTHER mass; commit at marginal ≥ 0.9; re-propose with pattern | fully-correct grid rate on 20 reconstructed grids; letters correct; proven vs quarantined; spend per grid | 003 |
| 005 | Metacomputation: OTHER prior from val; price every move; gain model on fit grids; VOC policy vs attempt-all vs vote-only, score-vs-spend curves | clues correct at equal spend; committed-only grids; seconds per grid | 004 |
| 006 | Commitment: calibrate the post-BP marginal on the fit grids; VOC with a calibrated commit rule on fresh grids; paired crossers-first baseline on 005's grids | committed-only grids; committed slots and accuracy; clues at $0.94 | 005 |
| 007 | Commit-time calibration (refit on every uncommitted slot-step), paired live against the uncalibrated rule on the same fresh grids | accuracy of committed slots (≥ 0.99); committed slots; clues at $0.94 | 006 |
| 008 | Synonym attestation: Moby + Open English WordNet as independent evidence on `syn` leaves (status unchanged under D4); posterior refit on val, scored on 006's grid records; $0 | P ≥ 0.9 coverage and accuracy with vs without attestation; attestation rate | 007 |
| 009 | Abbreviations hiding as synonyms: Wikipedia's crossword abbreviations (CC BY-SA) as origin `wikipedia`; reviewed `syn` hits become table hits; offline rescoring; $0 | Ok share before/after (val, train); proven slots on 006's grids | 008 |
| 010 | Soft evidence vs hard clamping, offline on 40 logged grids' round-1 candidates; Wikipedia table split into its own CC BY-SA file; $0 | clues / letters / fully-correct grids, hard vs soft vs annealed, paired | 009 |
| 011 | (deferred) Rejection-sample proven parses to distil a small proposer | — | 002, mutants at 0 |

Stop rule after 001: if gold-parse coverage on val is far below ~30%, the
sound-by-grammar verifier is not worth building on; refocus on 003 with the
verdict as a weaker feature.

Shared with `hkaddresses` (by design, once 003 exists): the `Hyp` kernel,
lattice tokeniser, alias tables, Ok/Quarantine. Not shared: the grammar.

## Post-cutoff protocol (fixed 2026-10-21, after brief 000's diagnostics)

Brief 000 found publisher is the largest effect on top-1 (Telegraph 0.547
vs Times 0.399 for Haiku; Quick 0.61 vs cryptic 0.45), so a contamination
estimate must compare like with like:

- The comparison set from Cryptonite test is a **stratified** sample
  matching the post-cutoff set's publisher and quick/cryptic mix, same
  seed; the gap is reported **per publisher**, never pooled.
- Only Times and Telegraph rows have an in-distribution baseline
  (Cryptonite has nothing else). Guardian and FT post-cutoff rows are still
  useful, but as a second, uncontaminated number per model, not as a gap.
- A gap on a weak model (Haiku) and on a strong one (Opus) are both
  reported; only the strong model is expected to show one.
- The Telegraph–Times difference is consistent with the Telegraph simply
  being easier, which is the solvers' consensus; it is not evidence of
  contamination on its own.

