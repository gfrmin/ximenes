# Brief 008 — Synonym attestation from published thesauri

Headline number: on **round-1 clue records of brief 006's 10 evaluation
grids** (seed 20261024; ~290 slots; never used to fit any posterior, so a
fresh held-out set for the clue posterior, D7), the posterior **with**
attestation features vs **without** (003's committed model, unchanged):
coverage and accuracy at P ≥ 0.9, and ECE. Secondary: on brief 001/002
parses, the share of `syn` leaves a thesaurus attests, and agreement between
attestation and the `judge_synonym` score. **Spend: $0** (table lookups and
offline rescoring of logged runs only).

## Why
Most accepted parses rest on a synonym leaf (001: median 78% of answer
letters; 002: 492 of 903 chosen Quarantines). Today the only evidence for a
synonym is a Haiku judgement. A published thesaurus is independent
evidence from a different source: not a proof (synonymy is semantic, and
crosswords stretch it), but cheap and auditable.

## What attestation is, under D4
A thesaurus is a published table but cannot be reviewed entry by entry
(millions of pairs), so by D4 an attested synonym is **not** mechanical. It
stays `Quarantine(synonym)`, and the leaf gains a field
`attested: {source: [moby, wordnet], relation: direct | 2-hop}`. The
verdict's status does not change. Whether attestation by two independent
thesauri should ever count as "reviewed" is a question for the author after
the numbers are in, not a decision for this brief.

## Build
1. **Sources**, fetched by `setup.sh` into `data/.src/` (not committed),
   hashes committed in `data/thesauri/SOURCES.sha256`:
   - Moby Thesaurus II (Project Gutenberg #3202, public domain);
   - Open English WordNet (CC BY 4.0), synsets and similar-to links.
   Licence notes in `data/thesauri/README.md`.
2. `ximenes.thesaurus`: one lookup `attest(clue_phrase, value) ->
   Attestation | None`, normalised (case, punctuation, multiword phrases as
   in the clue), with `direct` (listed together) and `2-hop` (shared
   headword) relations. Deterministic; pure; no network at lookup time.
3. **Attach** attestation to every synonym leaf in `solve.judged`, and
   rescore offline: brief 001 val/train formaliser outputs, 002 test run,
   003 val solve, 006 evaluation grids' round-1 records.
4. **Posterior refit**: 003's features plus `syn_attested_share` (share of
   synonym leaves attested, any relation), `syn_unattested_n`, and
   `min_leaf_score_unattested`. Fit on the 003 val solve only (grouped CV as
   in 003), commit `data/posterior-logistic-attested.json` **before** the
   006 grid records are scored.

## Tests (tests/test_008_*.py)
- Source files match their committed hashes; lookup refuses to run without
  them.
- `attest` table of cases (direct, 2-hop, multiword, none).
- Status of every rescored verdict is unchanged (attestation is a field).
- The refit refuses any split but val; committed before the scoring run id.

## Not in scope
Changing D4. Calling any LLM. Grid policies (commitment is closed for now).

## Report
The headline table (with vs without attestation on the 006 grid records:
coverage and accuracy at P ≥ 0.9, ECE, risk–coverage); attestation rate of
synonym leaves by source and relation; a 2×2 of attested vs judge score
≥ 0.5, with accuracy of the chosen answer in each cell; the 20 commonest
unattested synonym pairs among *correct* answers (what crossword usage
stretches); kit output; open questions; probability complete.
