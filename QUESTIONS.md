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
   `claude-opus-5-5` at effort `low` costs ~$0.0055 per sample, ~$110 for
   1000×20. It was stopped after 98 clues ($10.80), and the headline moved to
   the free `minimax-m3.1-flash` on Ollama cloud, at your request. Should a
   paid Claude row come back later, e.g. `claude-haiku-5-5` (~$0.10/$0.50 per
   million tokens), or Opus on the post-cutoff set only, where it says
   something about contamination?

7. **The Ollama backend ignores `effort`.** The value still sits in the
   logged input, because the replay key is shared across backends, but it is
   not sent to Ollama. No `think` setting is sent either, so samples run at
   the model's defaults. Going with: model defaults (p≈0.7).

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
