# Report — brief 008 (synonym attestation from published thesauri)

Status: **complete (2026-10-22).** Built by `opus`. **Spend: $0** (table
lookups and offline rescoring of logged runs only). Cumulative across briefs
000–008: **$103.18**.

## Headline numbers

Held-out set: the round-1 clue records of brief 006's 10 evaluation grids
(seed 20261024), i.e. every slot the calibrated VOC run solved: **176
clues**, never used to fit any posterior. Rebuilt offline from that run's log
(the formaliser's own NONE replies, 34% of first attempts, are genuine and
kept). These are hard slots: gold is among the candidates for only 73 of 176
(41%), since the easier slots were committed through crossers without being
solved.

| posterior (on the 176 held-out clues) | ECE | P ≥ 0.9: coverage | P ≥ 0.9: accuracy | top-1 |
|---|---|---|---|---|
| without attestation (003's committed logistic) | 0.074 | 0.131 | 0.913 | 0.352 |
| **with attestation** (refit on val) | **0.063** | **0.142** | **0.920** | 0.347 |

| risk–coverage (accuracy at coverage) | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.8 |
|---|---|---|---|---|---|---|
| without | 0.914 | 0.788 | 0.657 | 0.591 | 0.505 | 0.421 |
| with | 0.914 | 0.769 | 0.657 | 0.580 | 0.524 | 0.407 |

**Attestation helps a little and not reliably:** ECE 0.074 → 0.063 and one
or two more clues answered at P ≥ 0.9 (23 → 25), but the risk–coverage
curves cross. On val the out-of-fold log-loss moves 0.2048 → 0.2025. On
176 clues none of this is distinguishable from noise.

## Why: the judge already carries the signal

Synonym leaves of the chosen answers on brief 002's test run (1,000
clues, rescored):

| | judge ≥ 0.5 | judge < 0.5 |
|---|---|---|
| **attested** | 290 leaves; chosen answer right 0.866 | 41; 0.195 |
| **unattested** | 284; 0.877 | 232; 0.155 |

Given the Haiku judge's score, whether a thesaurus lists the pair changes
the chosen answer's accuracy by at most 4 points, in both directions.
Thesaurus attestation is real, independent evidence, but on this data it is
nearly redundant with the judge.

## Attestation rates

| synonym leaves | n | attested | Moby | WordNet | direct | 2-hop |
|---|---|---|---|---|---|---|
| 001 gold parses, val | 298 | 0.493 | 144 | 50 | 118 | 29 |
| 001 gold parses, train-500 | 469 | 0.522 | 242 | 64 | 198 | 47 |
| 002 test, chosen answers | 847 | 0.391 | 323 | 92 | 223 | 108 |
| 003 val solve, all candidates | 954 | 0.320 | | | | |

About half of the gold parses' synonym steps are in a thesaurus. Moby
carries most of it; WordNet adds a little (mostly overlapping). Crossword
synonymy stretches well beyond thesauri: definition by example, cryptic
substitution.

## What crossword usage stretches (the commonest unattested pairs among *correct* answers, 002 test)

quietly → P · poet → DANTE · the French → LA · councillor → CR · soldier
perhaps → ANT · service → RAF · lake → L · poet → POPE · women → W · colour →
RED (2 each) · on e perhaps → ORIENT · always briefly → EER · turn → U ·
concerts → C · Asian territories → INDIES · supplements → EKES · faced → MET
· revolutionary → CHE · French → FR · at college → UP (1 each).

**About half of these are not synonyms but standard abbreviations**
(quietly → P, lake → L, women → W, councillor → CR, French → FR, turn → U,
concerts → C, service → RAF). The formaliser wrote them as `syn` because the
abbreviation table lacks them, so they're quarantined when they could be
mechanical. Adding sourced abbreviations to the table (D4: reviewed entries)
would turn those steps into `Ok`-capable steps, which is a direct lever on
*proven*. The rest are definitions by example (poet → DANTE/POPE, soldier
perhaps → ANT, revolutionary → CHE), which no thesaurus lists.

## What was built

- **Sources** fetched by `setup.sh` into `data/.src/thesauri/` (not
  committed): Moby Thesaurus II (public domain) and Open English WordNet 2025
  (CC BY 4.0). Hashes in `data/thesauri/SOURCES.sha256`, licences in
  `data/thesauri/README.md`; the loader verifies them and refuses to run
  without them.
- **`ximenes.thesaurus`:** a pure `attest(phrase, value)` lookup. Matching is
  on letters only (DSL values carry no spaces), with a plural fallback (both
  words ending in s). Relations: "direct" (Moby: listed under the other's
  headword; WordNet: same or similar-to synset) or "2-hop" (Moby: share a
  line; WordNet: share a word between their synsets). `attach(record)` adds
  `attested` to synonym leaves without changing anything else.
- **`OracleLeaf.attested`** and Hyp `oracle_calls[].attested`: a field, so a
  verdict's status is unchanged (D4).
- **`posterior.features_attested` / `fit_attested`:** 003's features plus
  `syn_attested_share`, `syn_unattested_n`, `min_leaf_score_unattested`.
  Two missing-value flags (`syn_none`, `unattested_missing`) follow 003's
  "flag plus 0" rule; the brief didn't list them. Fitted on val only, and
  committed (`1841f19`) before the held-out records were scored.
- **Tests (`tests/test_008_*`):** `attest` as a table of cases (direct,
  2-hop, multiword, similar-to, plural, none); `attach` changes no status
  and leaves its input untouched; the loader refuses without sources; the
  real sources match their hashes; the refit is val-only.

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 31%]
........................................................................ [ 63%]
........................................................................ [ 95%]
..........                                                               [100%]
226 passed in 18.07s
== kit: GREEN
```

(In CI the tests that need the thesauri or local runs are skipped.)

## Open questions

See `QUESTIONS.md` § Brief 008.

## Probability complete

**0.8.** Every build item and test exists, the refit was committed before the
held-out records were scored, and no LLM was called. Doubts: the held-out
set is 176 hard clues (not the ~290 slots the brief expected, because VOC
committed the easy slots without solving them), so the headline difference
is within noise; and the two missing-value flags are my addition.
