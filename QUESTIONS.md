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

   **Answer (2026-10-21, fable):** D4 was wrong as written and is now
   changed: a verdict is about the wordplay; the definition is a separate
   confirmation reported alongside (`definition: pending | judged`). So the
   23 val / 42 train parses that rest only on the definition are `Ok`:
   7.7% / 8.4% is the honest "wordplay proven" rate, and the report should
   say so. Brief 002 implements the split (oracle judges the definition,
   result travels with the verdict, never changes the verdict's status).

2. **Expected status of the audited gold parses.** The brief says the 30
   hand-written parses "all verify (as Ok or Quarantine)". But 23 of the 30
   audited Rejects need an operator the DSL lacks, so no correct parse of
   them can verify. They are stored with the missing operator named and
   expected `Reject:surface:unknown_operator:<op>`; the other 7 are expected
   Quarantine. Going with: that reading (p≈0.7).

   **Answer:** your reading is right. When 002 adds an operator, the
   fixture entries whose expectation was `Reject:unknown_operator:<op>` for
   that operator are updated to their real status, and the 002 report lists
   each one; that is the "superseded by a later brief that says so" case in
   D8, not an edit of a frozen test.

3. **Train coverage is on a seeded 500-clue subsample**, not all 5,412
   ($1.46 vs ~$25 at the measured rate), to keep spend low. Run the full
   sample?

   **Answer:** keep the 500. ±3 points is enough for a secondary number; the
   full 5,412 is only worth $25 once something depends on it (distillation,
   brief 006).

4. **Quick vs hard is empty on both samples:** none of the 300 val or 500
   train rows is a quick clue. Should a later brief add quick clues from
   elsewhere, or drop the split?

   **Answer:** drop the quick/hard split for wordplay-based numbers (the
   teacow sample has none); keep it for Cryptonite-based numbers, where
   brief 000 had 77 quick clues. Say so once in each report.

5. **Next operators.** ~80% of Rejects need `last_letters` / `outer_letters`
   or `remove` / `strip_outer`. Add them in brief 002 (with tests) before
   the proposer loop, or keep the DSL fixed and treat 0.85 as the ceiling?
   Recommendation: add them first; they are mechanical and small.

   **Answer:** add them first, in 002, before the proposer loop:
   `first_letters`, `last_letters`, `outer_letters`, `middle_letters`,
   `remove`, `strip_outer`, `half`. All mechanical, each with a property
   test and mutants; definitions in `briefs/002-proposer-loop.md`. Leave out
   spoonerism, cycling and letter replacement (3–4 cases each).

6. **Indicator table review.** 87 val parses are Quarantined because an
   indicator phrase is missing from the table. That costs `Ok`, not
   soundness. A *wrong* entry would cost soundness, and the merged Deits
   lists have not been reviewed entry by entry (data/lexicon/REVIEW.md).
   Review before brief 002 relies on `Ok`?

   **Answer:** review only what `Ok` would rest on, and make the rest
   honest by construction (D4 now says this): tag indicator entries with an
   origin like the abbreviations; a step that rests on an *unreviewed*
   entry is `Quarantine(table_unreviewed)`, never `Ok`. Then review exactly
   the entries that accepted val+train parses hit (bounded, a few hundred),
   which converts those to `Ok`. The 87 missing phrases go in the report;
   add any to the hand table only with a source, never from formaliser
   output, or the table learns from the LLM and "mechanical" stops meaning
   anything. Full Deits review deferred.

## Brief 002

**Author action (fable, 2026-10-21):** `data/lexicon/reviewed.json` holds the
165 upstream table entries that brief 001's accepted parses rely on, reviewed
by opus (an LLM), plus 5 it left doubtful (`REVIEW.md`). An `Ok` is now a
proof modulo these entries, so this is the one human checkpoint in the
chain: spot-check a seeded 20 of the 165 and rule on the 5, then add a line
to `REVIEW.md` saying what you checked and when. Nothing blocks on it; the
002 report will state that the tables are LLM-reviewed until that line
exists.

**Questions from the brief 002 run (opus, 2026-10-21):**

1. **Which "verified set" should brief 003 pre-register?** The brief's
   definition (Ok, or Quarantine with every oracle score ≥ 0.5) gives 505
   clues at 0.861. My stricter reading, added before the run, also excluded
   Quarantines resting on an unscored indicator or unreviewed entry (278 at
   0.777). It drops 227 clues that are right 0.965 of the time, and it admits
   every `Ok`, including 8 whose definition scored < 0.5 (2 right). Proposal
   for 003: *wordplay accepted (Ok or Quarantine) and every judgement,
   definition included, scored ≥ floor*. Unlisted indicators would then need
   a score of their own (next question) or count as passing. Going with: no
   change until you or fable rule (p≈0.5 on which you'd pick).

2. **Unlisted indicators are now the commonest unscored step** (239 chosen
   answers rest on one). Either add a `judge_indicator` oracle (cheap: Haiku,
   one call per unlisted phrase, cacheable across clues), or grow the hand
   table from a sourced list. fable's rule forbids adding entries from
   formaliser output. Recommendation: the oracle, which keeps "mechanical"
   meaning what it says.

3. **The formaliser is the cost** ($14.58 of $15.14). If brief 003 re-runs
   the loop, candidates whose vote share is ≥ 0.9 could skip formalising the
   2nd and 3rd candidates. That's a pre-registration change, so it's yours
   to make.
