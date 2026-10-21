# Open questions

Unanswered questions for the author, by brief. Each names the reading the
builder went with and how sure it was. Answers are written inline under the
question (marked **Answer**). The builder deletes an entry once it has acted
on the answer, and says so in the commit message.

## Brief 000

Answered 2026-10-21: Cryptonite and cryptic-wordplay are used locally and never
republished here, so the test fixture uses 20 original clues and reports hold no
clue text. (This was item 1.)

2. **Vote rules.** Confidence = votes for the winner ÷ k, with blank and
   wrong-length samples left in the denominator. There's no filter on
   enumeration length, and ties go to the answer sampled first. Filtering by
   length would raise top-1, but it's a proposer choice and belongs in brief
   002. Going with: no filter (p≈0.75).

   **Answer (2026-10-21):** Your reading is right. Brief 000's number is the
   proposer as it is, and blanks in the denominator are correct for
   calibration: a blank is evidence of uncertainty. The enumeration check is
   the first mechanical rule of the verifier, so it belongs to brief 002.
   One addition, as a diagnostic only, not a filter: report the share of
   samples that fail the enumeration (wrong length or no letters). It tells
   us in advance how much brief 002's cheapest check will prune.

3. **Which model is "the proposer"?** The brief leaves `--model <id>` open.
   The headline is `claude-haiku-5-5` at effort `low` (~$10 for 1000×20),
   after Opus (~$110 projected; stopped at 98 clues, $10.80) and free Ollama
   cloud (1 concurrent request; days for 20,000 calls) were ruled out. See
   `reports/000-harness.md` § Why Haiku. Open: should Opus be run on the
   post-cutoff set only, once it exists? That's where a contamination gap
   for a strong model would show.

   **Answer (2026-10-21):** Haiku at effort low as the headline proposer,
   yes, and keep that choice fixed through briefs 002–003 so the verifier's
   gain is measured against one proposer. On Opus: run it only once the
   post-cutoff set exists, and then on *both* sets at the same small size
   (200 post-cutoff and 200 Cryptonite test, same seed) so the gap is a
   like-for-like comparison. The 98-clue partial should stay out of the
   headline table: it is the oldest 2000–2004 clues, so it measures recall
   of the most-reprinted puzzles, not solving. Keep it in an appendix as
   what it is: evidence that strong models look solved on old public clues.
   No need to diagnose the stall; it has the shape of a rate limit.

4. **No refusal fallback, no temperature.** The API's server-side refusal
   fallback would answer some samples with a different model, which muddies
   "one proposer", so it's off. Refusals are counted in `cost.refusals` and
   treated as blank samples. Current models reject non-default `temperature`,
   so samples use the API's default sampling. Going with: off (p≈0.8).

   **Answer (2026-10-21):** Agreed on both. One proposer means one model and
   the API's own sampling. Keep logging refusal counts; if they are ever
   above a handful per thousand clues, say so in the report, since a refusal
   on a crossword clue would be a prompt problem worth seeing.

5. **Post-cutoff format.** `load_postcutoff` assumes `data/postcutoff/*.jsonl`
   in Cryptonite's row format, with `clue` including the enumeration. Nothing
   is there yet, so the contamination gap (test vs post-cutoff) is
   unmeasured. What format and dates will the files have?

   **Answer (2026-10-21):** Cryptonite row format, exactly as you assumed,
   so one loader serves both. Required per row: `publisher`, `sub_publisher`,
   `date` (ms epoch, the puzzle's publication date), `number` (the
   publisher's puzzle number), `orientation`, `clue` with the enumeration
   embedded, `answer`, `enumeration`, `quick`. Optional, for brief 001
   coverage later: `wordplay` and `clue_marked` (definition in `{}`) in the
   cryptic-wordplay style, and `source_url` for the blog parse. One file per
   puzzle, named `<publisher>-<number>-<yyyy-mm-dd>.jsonl`, so a row's
   provenance is its filename.

   Dates: nothing published before 2026-10-22 counts as post-cutoff for
   any model, because every model we might use was released before today.
   The rule the loader should enforce: a post-cutoff row is usable for model
   M only if `date` is after M's release date; `data/instruments.json` gets a
   `released` field per model (author fills it), and `load_postcutoff(model=…)`
   filters on it and reports how many rows were excluded. Collection starts
   now and is the author's job: Times daily (plus Quick Cryptic, flagged
   `quick`), Guardian and FT as available. 300 rows gives a ±5-point gap
   estimate; a month of the Times alone is ~800.

6. **Line counts in the brief are off by one.** `wc -l` gives 26,156 val and
   26,157 test, against 26,155 and 26,156 in the brief. The frozen hashes
   match, so the files are the published ones. Going with: the brief
   miscounted (p≈0.9).

   **Answer (2026-10-21):** The brief miscounted. The files have no trailing
   newline, so `wc -l` reports one less than the number of records. Record
   counts are 470,804 / 26,156 / 26,157. Fixed in `briefs/000-harness.md`
   in the same commit as this answer.
