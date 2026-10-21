# Open questions

Unanswered questions for the author, by brief. Each names the reading the
builder went with and how sure it was. Answers are written inline under the
question (marked **Answer**). The builder deletes an entry once it has acted
on the answer, and says so in the commit message.

## Brief 000

All answered and acted on (2026-10-21, opus):
1 datasets local only, original fixture clues · 2 vote rules kept,
enum-fail share added as a diagnostic · 3 Haiku is the proposer through
002–003, Opus partial in an appendix · 4 no fallback or temperature, refusals
reported · 5 `load_postcutoff(model=…)` filters on `postcutoff_floor`
2026-10-22 and per-model `released` dates, which are now filled in
`data/instruments.json` from fable's answer · 6 record counts fixed in the
brief by fable · 7 Ollama keeps model defaults; the backend now refuses to
run until its logged input says `effort: null` (that change is left for
whoever revives it).

## Brief 001

1. **`Ok` is unreachable for ordinary clues.** DESIGN D4 makes `defn` an
   oracle leaf, so any clue with a definition is at least
   `Quarantine(definition)`. On val, 0 parses are `Ok`. 23 are Quarantined
   *only* on the definition, i.e. their wordplay is fully mechanical. Should
   the verdict say "wordplay proven, definition pending" as its own state (or
   as `Ok` with the definition reported separately, as GAME.md §3's "two of
   three confirmations" suggests)? Going with: D4 as written, with the 23
   reported separately (p≈0.6 that's what you want long term).

2. **Expected status of the audited gold parses.** The brief says the 30
   hand-written parses "all verify (as Ok or Quarantine)". But 23 of the 30
   audited Rejects need an operator the DSL lacks, so no correct parse of
   them can verify. They are stored with the missing operator named and
   expected `Reject:surface:unknown_operator:<op>`; the other 7 are expected
   Quarantine. Going with: that reading (p≈0.7).

3. **Train coverage is on a seeded 500-clue subsample**, not all 5,412
   ($1.46 vs ~$25 at the measured rate), to keep spend low. Run the full
   sample?

4. **Quick vs hard is empty on both samples:** none of the 300 val or 500
   train rows is a quick clue. Should a later brief add quick clues from
   elsewhere, or drop the split?

5. **Next operators.** ~80% of Rejects need `last_letters` / `outer_letters`
   or `remove` / `strip_outer`. Add them in brief 002 (with tests) before
   the proposer loop, or keep the DSL fixed and treat 0.85 as the ceiling?
   Recommendation: add them first; they are mechanical and small.

6. **Indicator table review.** 87 val parses are Quarantined because an
   indicator phrase is missing from the table. That costs `Ok`, not
   soundness. A *wrong* entry would cost soundness, and the merged Deits
   lists have not been reviewed entry by entry (data/lexicon/REVIEW.md).
   Review before brief 002 relies on `Ok`?
