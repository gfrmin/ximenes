# Open questions

Unanswered questions for the author, by brief. Each names the reading the
builder went with and how sure it was. Delete an entry once it's answered,
and note the answer in the commit message.

## Brief 000

1. **Test fixture clues are original, not 20 Cryptonite val clues.** The brief
   asks for "a hand-made log for 20 val clues". Neither `aviaefrat/cryptonite`
   nor `mdda/cryptic-wordplay` has a licence on GitHub, the clues are
   newspaper text, and this repo is public. So `tests/fixtures/clues-20.jsonl`
   holds 20 clues written for this repo, in Cryptonite row format
   (`publisher: "synthetic"`). The path through real val clues is covered by
   a local-only test that builds its log in a temp dir. Going with: original
   clues (p≈0.75 that's what you want). Do you want real rows committed anyway?

2. **Vote rules.** Confidence = votes for the winner ÷ k, with blank and
   wrong-length samples left in the denominator. There's no filter on
   enumeration length, and ties go to the answer sampled first. Filtering by
   length would raise top-1, but it's a proposer choice and belongs in brief
   002. Going with: no filter (p≈0.75).

3. **Which model is "the proposer"?** The brief leaves `--model <id>` open.
   The headline run uses `claude-opus-5-5` with effort `low` and the
   `answer-only-v1` prompt (`data/instruments.json`). Its cost is mostly
   reasoning tokens, about $0.0096 per sample (~$190 for 1000×20). Should
   later briefs compare against a cheaper model, e.g. `claude-haiku-5-5`, as
   a second row?

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
