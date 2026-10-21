# Open questions

Unanswered questions for the author, by brief. Each names the reading the
builder went with and how sure it was. Delete an entry once it's answered,
and note the answer in the commit message.

## Brief 000

Answered 2026-10-21: Cryptonite and cryptic-wordplay are used locally and never
republished here, so the test fixture uses 20 original clues and reports hold no
clue text. (This was item 1.)

2. **Vote rules.** Confidence = votes for the winner ÷ k, with blank and
   wrong-length samples left in the denominator. There's no filter on
   enumeration length, and ties go to the answer sampled first. Filtering by
   length would raise top-1, but it's a proposer choice and belongs in brief
   002. Going with: no filter (p≈0.75).

3. **Which model is "the proposer"?** The brief leaves `--model <id>` open.
   The headline is `claude-haiku-5-5` at effort `low` (~$10 for 1000×20),
   after Opus (~$110 projected; stopped at 98 clues, $10.80) and free Ollama
   cloud (1 concurrent request; days for 20,000 calls) were ruled out. See
   `reports/000-harness.md` § Why Haiku. Open: should Opus be run on the
   post-cutoff set only, once it exists? That's where a contamination gap
   for a strong model would show.

4. **No refusal fallback, no temperature.** The API's server-side refusal
   fallback would answer some samples with a different model, which muddies
   "one proposer", so it's off. Refusals are counted in `cost.refusals` and
   treated as blank samples. Current models reject non-default `temperature`,
   so samples use the API's default sampling. Going with: off (p≈0.8).

5. **Post-cutoff format.** `load_postcutoff` assumes `data/postcutoff/*.jsonl`
   in Cryptonite's row format, with `clue` including the enumeration. Nothing
   is there yet, so the contamination gap (test vs post-cutoff) is
   unmeasured. What format and dates will the files have?

6. **Line counts in the brief are off by one.** `wc -l` gives 26,156 val and
   26,157 test, against 26,155 and 26,156 in the brief. The frozen hashes
   match, so the files are the published ones. Going with: the brief
   miscounted (p≈0.9).
