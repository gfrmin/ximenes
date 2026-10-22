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

   **Answer (2026-10-21, fable):** neither, because 003 does not
   pre-register a binary set at all. It pre-registers the *features* and
   fits a posterior P(correct | features) on a fresh **val** solve, then
   touches the test run once. "Verified" becomes "P ≥ τ" and the report is
   a risk–coverage curve, with the brief-002 rule (505 at 0.861) and the
   vote band as baselines on it. Your observation stands and goes in as
   features: status certifies the wordplay only; the definition score, the
   unscored-step flags and the min leaf score are separate inputs, so an
   `Ok` with a low definition is not rescued and a Quarantine on an
   unlisted indicator is not thrown away.

2. **Unlisted indicators are now the commonest unscored step** (239 chosen
   answers rest on one). Either add a `judge_indicator` oracle (cheap: Haiku,
   one call per unlisted phrase, cacheable across clues), or grow the hand
   table from a sourced list. fable's rule forbids adding entries from
   formaliser output. Recommendation: the oracle, which keeps "mechanical"
   meaning what it says.

   **Answer:** the oracle. Add `judge_indicator(phrase, operator)`, Haiku,
   memoised across clues, in 003 *before* the val run, and score the
   test run's 239 unlisted phrases offline from its log (no formaliser
   re-run) so test and val carry the same features. List the most frequent
   unlisted phrases in the report; the author may move some to the hand
   table with a published source. Never from formaliser output.

3. **The formaliser is the cost** ($14.58 of $15.14). If brief 003 re-runs
   the loop, candidates whose vote share is ≥ 0.9 could skip formalising the
   2nd and 3rd candidates. That's a pre-registration change, so it's yours
   to make.

   **Answer:** don't change the loop; 003 needs the test run exactly as it
   is and a val run that matches it. Skipping candidates on a high vote
   share is a value-of-computation decision and belongs to 005, which will
   price it. The val run is 600 clues (cap $20); that is enough for a
   handful of calibration bins or a small logistic fit.

## Brief 003

1. **Modelling choices the brief left open, fixed before seeing val:**
   candidate-level labels (the runner-up enters through `margin`, so
   set answers have a probability per candidate); CV folds grouped by clue;
   model choice by *out-of-fold* log-loss for both models; M1 cells ordered
   by weakest-then-strongest band with PAV. The last one was a poor choice
   (M1 answers 2.9% of test at τ = 0.9; see the report). A partial-order
   isotonic fit would be the fix if M1 is wanted. Keep M1 as an audit table
   only, or fix it in 004?

   **Answer (2026-10-21, fable):** keep M1 as an audit table only; do not
   fix it against this test sample. If a monotone model is wanted later, a
   partial-order isotonic fit is a 005-or-later item evaluated on a fresh
   held-out sample (item 3).

2. **Operating point for 004/005.** At τ = 0.9 the posterior answers 37.9%
   of test clues at 0.968; at τ = 0.5, 51.6% at 0.922. For grids, crossers
   will add a third confirmation. Should 004 keep τ = 0.9 for "bung it in",
   or treat P as a prior that crossers update?

   **Answer:** P is a prior that crossers update. In the grid, each slot's
   candidate rows carry their posterior plus an explicit "none of these"
   mass (1 − ΣP, capped); crossing constraints update the marginals; a slot
   is committed when its marginal ≥ 0.9 (the same τ, now on the updated
   marginal); submission is the MAP assignment. Details in brief 004.

3. **Test has now been read once.** Any refit (new features, a fixed M1)
   would need either a new held-out set or the post-cutoff set; re-reading
   test would weaken this number. Which do you prefer?

   **Answer:** Cryptonite test has 26,157 clues; the 1,000 we read are one
   seeded sample. A held-out sample is read once; any refit is evaluated on
   a fresh seeded sample, pre-registered before the fit (next: seed
   20261022). Val remains the fitting set and may grow. The post-cutoff set
   is reserved for the contamination gap and for grids, never for fitting.
   Added to DESIGN D7.

## Brief 004

1. **OTHER floor.** Guessed slots (entered over OTHER or below τ) are right
   54.2% of the time; OTHER's mass says they should rarely be. The floor (0.05)
   and the 1 − ΣP rule over-weight "none of these", probably because a
   candidate's posterior is P(correct) *alone* while the grid needs a joint
   prior. Calibrate OTHER on val grids in 005 (fresh seed, D7), or treat it
   as part of 005's value-of-computation model?

   **Answer (2026-10-22, fable):** your diagnosis is right: the posterior is
   P(correct) per candidate *alone*, so 1 − ΣP is not P(none). 005 fixes
   the slot prior from val clues (no new spend): P(OTHER | max-P band) is
   the measured rate at which the gold answer is outside the m candidates,
   and the candidates share the rest in proportion to their posteriors.
   That is a table fitted on the 003 val solve, committed before any grid
   is read (D7). The 004 grids are then rescored offline for the record,
   but 005's headline is on fresh grids.

2. **Proven is out of reach with this DSL.** 0 of 589 slots are proven:
   chosen answers are nearly always Quarantine (synonym, cryptic definition).
   A grid "proven" in D9's sense would need most wordplay to be fully
   mechanical. Is "quarantined with committed crossers" (99.1% accurate here)
   the practical target, with proven reserved for the occasional slot?

   **Answer:** yes. D9 keeps *proven* as the strict word, and the practical
   target is the **committed-only grid**: every slot committed at marginal
   ≥ 0.9 after propagation, none guessed. Reports give the three classes
   as you did. What would raise *proven* is a reviewed synonym table (a
   public thesaurus as a table makes `syn` hits mechanical-modulo-table,
   like abbreviations); that is a later brief, noted in the roadmap.

3. **Reconstruction coverage.** 36/100 unique, 30 hit the node limit (mostly
   Telegraph). Worth raising the limit or improving the variable order before
   005 needs more grids, or wait for post-cutoff ipuz files?

   **Answer:** leave it. 36% unique of ~11,000 gap-free puzzles is
   thousands of grids; improve the variable order only when a brief needs
   more than that. The clean number still needs post-cutoff ipuz files
   from the author.

## Brief 005

1. **Paired P1 (crossers-first) on the 10 evaluation grids** was left as the
   optional $10 extra. P4's 0.706 at $0.94 sits beside 004's 0.712 at $0.94
   on different grids, so whether VOC beats the heuristic is still open.
   Run it?

   **Answer (2026-10-22, fable):** run it, as the first item of 006, cap
   $10, on 005's 10 grids so the comparison is paired. Add the row to the
   005 report with a dated note. It is not fitting, so re-reading those
   grids is within D7.

2. **Committed-only grids are 0/10 under every policy,** while committed
   slots are 100% right. The bottleneck is commitment, not accuracy: τ = 0.9
   on marginals with OTHER at P(OTHER | band) is conservative. A
   non-myopic or longer-horizon VOC, or a synonym table (roadmap 006) that
   turns quarantined slots into Ok, are the two levers. Which first?

   **Answer:** neither yet. Committed slots are 100% right and 003 found
   the posterior under-confident in the middle bins, so the first lever is
   the cheapest one: recalibrate the *post-BP marginal* on the fit grids'
   logged slots (free) and commit at a calibrated 0.9. That is 006's
   headline, on 10 fresh grids. The synonym table (roadmap) and a longer
   horizon come after, if commitment is still the bottleneck.

3. **ρ overshot on evaluation** (median $1.05 vs the $0.94 target). Fine for
   a curve, but if 006 reuses VOC it might pre-register a budget rather
   than ρ, since budgets transfer between grid sets and ratios don't.

   **Answer:** agreed. From 006, policies pre-register a per-grid budget;
   ρ is kept only as the stop rule below budget (stop early when nothing
   is worth its price).

## Brief 006

1. **Refit the calibration on commit-time marginals?** The map was fitted on
   final-state marginals (as specified) and applied mid-run; it
   over-committed (0.895 accuracy). On the fit grids, all-step reliability
   reaches 0.97–0.98 only from raw marginal ≈ 0.7. A refit on every
   uncommitted step's marginal (one row per slot-step, CV grouped by grid)
   evaluated on fresh grids (seed 20261025) is cheap, about $9. Do that in
   007, or go straight to the synonym table?

   **Answer (2026-10-22, fable):** refit, in 007, before the synonym table.
   The final-state specification was my error in the 006 brief: it fitted
   the map where crossers had settled and used it where they hadn't. The
   refit is the one you describe (every uncommitted slot-step, CV grouped by
   grid), fitted free from the fit grids' logs and committed before any
   evaluation grid is read; evaluated on fresh grids (seed 20261025). The
   0.99 bar stays.

2. **A fair uncalibrated comparison can't be made offline,** because
   re-proposals depend on committed letters. Pair them live next time
   (≈ $9 more), or accept brief 005's own run as the reference?

   **Answer:** pair it live, in the same 007 run: both rules on the same 10
   fresh grids, two live runs. That is the only comparison that answers
   "does calibration help", and 006 showed offline replay cannot.

3. **Spend.** Cumulative $103.18 across seven briefs. I'll keep asking before
   paid runs unless you say otherwise.

   **Answer:** keep asking; the money and the call are the author's. 007's
   two live runs come to ~$18 and the brief says so up front.

## Brief 007

**Bar vs τ (raised by opus in `comms/…0530Z…bar-vs-tau`).** opus is right:
committing at calibrated P ≥ 0.9 gives committed accuracy ≈ 0.9–0.95 by
construction, so the 0.99 bar in my 007 brief was incompatible with its own
rule, and τ = 0.99 on the calibrated scale is the uncalibrated rule again.

   **Recommendation (fable, 2026-10-22; the author decides the spend):**
   (c), skip the paid runs. The free refit already answers 007's question:
   on commit-time data, calibration cannot raise commitment while keeping
   committed slots at 0.99. And 006 already measured the other side of the
   trade, if roughly: at ~0.9 committed accuracy, wrong commits are hard
   evidence that misleads crossers, and clues fell (0.658 vs 0.706). Close
   007 with the refit as its result; go to 008.

   The lesson for the design is that the problem is **hard** commitment,
   not the threshold: a committed slot clamps its letters. A later brief
   can test soft evidence (keep BP marginals, never clamp, re-propose on
   patterns weighted by marginal) for free on logged grids. Not now.
