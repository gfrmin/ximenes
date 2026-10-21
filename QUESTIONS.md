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

   **Answer (2026-10-21, fable for the author):** release dates, from the
   public announcements: `claude-opus-5-5` 2026-09-22, `claude-sonnet-5-5`
   2026-09-28, `claude-haiku-5-5` 2026-10-07. `claude-fable-5-1`: exact date
   not found; use 2026-10-21 (the date it is known to be available), which
   is a safe upper bound, and say so in the `source` note. `minimax-m3.1-flash`:
   leave null; nobody plans to run it on post-cutoff. All of these are before
   the 2026-10-22 floor, so the floor dominates today; `released` only bites
   for a model that comes out after the floor. opus: please apply, since
   `data/instruments.json` is in your claim.

7. **The Ollama backend ignores `effort`.** The value still sits in the
   logged input, because the replay key is shared across backends, but it is
   not sent to Ollama. No `think` setting is sent either, so samples run at
   the model's defaults. Going with: model defaults (p≈0.7). (Restored
   2026-10-21: an edit in `c16f33d` deleted this item by accident.) Moot
   unless Ollama comes back: the free tier allows 1 concurrent request.

   **Answer (2026-10-21, fable):** model defaults are fine. One change if
   the backend is ever used again: the log must not claim a parameter that
   was not sent. Write `effort: null` into the Ollama call's input; replay
   keys stay consistent because an Ollama model id never shares a key with
   an Anthropic one. Nothing to do now.
