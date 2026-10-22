# Brief 009 — Abbreviations hiding as synonyms

Headline number: **share of accepted parses that are `Ok`** before and
after the extended abbreviation table, on brief 001's val (300) and train
(500) formaliser outputs, and **proven slots** on brief 006's 10 evaluation
grids, all by **offline re-verification** of logged parses. **Spend: $0.**

## Why
Brief 008 found that about half of the commonest unattested "synonym"
pairs in correct answers are standard abbreviations missing from the table
(quietly → P, lake → L, women → W, councillor → CR, French → FR…). As
`syn` leaves they are oracle judgements; as reviewed table entries they are
mechanical (D4). This is the most direct lever on *proven* so far.

## Build
1. **Source.** Wikipedia, "Crossword abbreviations"
   (https://en.wikipedia.org/wiki/Crossword_abbreviations), CC BY-SA 4.0.
   `setup.sh` fetches a fixed revision (oldid pinned) into `data/.src/`;
   `data/lexicon/build_abbreviations.py` parses it into origin `wikipedia`
   entries and merges them with the existing table. The built table's
   header carries the licence, revision and attribution. Import the **whole**
   list, not the pairs 008 surfaced, so evaluation is not selected on its
   outcome.
2. **Verifier.** `syn(tok, V)` where (phrase, V) is a *reviewed*
   abbreviation entry is recorded as an abbreviation table hit (mechanical);
   otherwise unchanged. An unreviewed `wikipedia` entry gives
   `Quarantine(table_unreviewed)` as for Deits entries.
3. **Review.** List every `wikipedia` entry that an accepted parse in the
   rescored sets hits; review them as in 002 (accepted / doubtful), record
   in `REVIEW.md`, and note that review is by an LLM pending the author's
   spot-check (QUESTIONS § 002).
4. **Rescore** offline: 001 val/train, 002 test, 006 grid records. Report Ok
   and proven before vs after, and how many `syn` leaves became table hits.

## Tests (tests/test_009_*.py)
- Parser: a fixture page excerpt gives the expected entries; the build is
  deterministic and equals the committed table.
- `syn` → table hit only for reviewed entries; unreviewed stays Quarantine.
- Mutation suite: 0 false accepts with the new table (rerun on val).
- No status change except Quarantine(synonym) → Ok or
  Quarantine(other reasons) when a syn leaf becomes a reviewed hit.

## Not in scope
Any LLM call. Changing D4. Posterior refit (features unchanged; if Ok
share moves materially, a later brief refits on val with a fresh seed).

## Report
Ok share before/after on val and train; proven slots on 006's grids
before/after; syn leaves converted; review counts; the entries most often
hit; mutants; kit output; open questions; probability complete.
