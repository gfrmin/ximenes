# Open questions

Unanswered questions for the author, by brief. Each names the reading the
builder went with and how sure it was. Answers are written inline under the
question (marked **Answer**). The builder deletes an entry once it has acted
on the answer, and says so in the commit message.

## Brief 000

Acted on and removed (2026-10-21, opus): item 1 (datasets local only; original
fixture clues), 2 (vote rules kept; enum-fail share added as a diagnostic),
3 (Haiku is the proposer through 002–003; Opus partial moved to an appendix),
4 (no fallback or temperature; refusals reported), 5 (`load_postcutoff(model=…)`
filters on `postcutoff_floor` 2026-10-22 and per-model `released` dates, and
reports rows excluded), 6 (record counts fixed in the brief by fable).

**Author action:** fill `released` (ISO dates) in `data/instruments.json` for
any model you'll run on post-cutoff. While a date is null, post-cutoff runs
for that model refuse to start.

7. **The Ollama backend ignores `effort`.** The value still sits in the
   logged input, because the replay key is shared across backends, but it is
   not sent to Ollama. No `think` setting is sent either, so samples run at
   the model's defaults. Going with: model defaults (p≈0.7). (Restored
   2026-10-21: an edit in `c16f33d` deleted this item by accident.) Moot
   unless Ollama comes back: the free tier allows 1 concurrent request.
