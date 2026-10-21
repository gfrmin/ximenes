# How ximenes uses LLMs

Short version: an LLM is an **untrusted proposer and oracle**, never the
judge. Today, in brief 000, it is the whole solver, because the baseline
being measured is "just ask the model". From brief 002 on, it only suggests;
code decides.

## Brief 000: the baseline (what runs today)

There isn't a solver yet. Brief 000 measures a plain LLM, and uses it in one
narrow way. For each clue:

1. **One prompt, sent k=20 separate times.** The template is `answer-only-v1`
   in `src/ximenes/instruments.py`:

   ```
   Solve this cryptic crossword clue. The numbers in brackets give the
   answer's word lengths. Reply with the answer only, in capital letters,
   and nothing else.

   bear close? turn about! (6)
   ```

2. **Each call is independent:** one user message, no system prompt, no
   examples. Anthropic: `client.messages.create(model=..., max_tokens=16000,
   output_config={"effort": "low"})`. No temperature is sent (current
   models reject it), so the variety comes from the model's default
   sampling. The model reasons internally (hidden thinking tokens, most of
   the cost), then writes its answer. Ollama: `client.chat(model=...,
   messages=[...])` with the model's defaults.
3. **Reading the reply:** only the first non-empty line is kept. A refusal
   or empty reply counts as a blank vote.
4. **Voting happens in our code** (`ximenes.eval.majority`). Answers are
   reduced to their letters (`HAIR-RAISING` → `HAIRRAISING`). The most
   frequent answer wins, and ties go to the one sampled first. Confidence =
   its votes ÷ k, blanks included. Example: 11 of 20 say `REVERT` →
   prediction `REVERT`, confidence 0.55.
5. **Scoring:** the prediction is right if its letters equal the gold
   answer's. Across the sampled clues this gives top-1 accuracy and ECE with
   10 bins (does a 0.55 vote share mean right 55% of the time?).
6. **Logging (DESIGN D6):** each clue's k answers, token counts and cost go
   to `runs/<run-id>.jsonl` as `{ts, instrument, model, input, output, cost}`.
   The `stub` backend replays that file offline and gives exactly the same
   numbers. `--log` on a live backend resumes a run and pays only for calls
   the log doesn't have.

The LLM never sees wordplay, crossing letters or other clues, and nothing
checks its reasoning. **The answer it outputs is the system's answer.** That
is the baseline later briefs have to beat.

## Later briefs: propose → verify → decide

Sources: `DESIGN.md` (D1–D4, D9), `docs/GAME.md`, `briefs/ROADMAP.md`.

- **Proposer (brief 002).** The LLM suggests candidate answers and a
  wordplay parse written in the DSL, e.g.
  `clue(defn(tok("support")), anagram(tok("broadcast"), lit(tok("also")), "ALSO"))`.
- **Verifier (brief 001), plain code.** The parse is parsed to an AST and
  walked, never executed. The string operations (anagram, reversal, hidden
  word, insertion, deletion, abbreviation table…) must work out, and every
  non-link clue word must be used exactly once. A failed parse is `Reject`ed
  with the first rule it broke, and that hint goes back to the LLM for a
  retry.
- **Oracle.** Steps code can't check (is X a synonym of Y? is this span the
  definition? is it a homophone? a cryptic or double definition?) become
  logged LLM judgements. An answer resting on any of them is `Quarantine`d
  with the reasons named, not `Ok`, and is never called a proof.
- **Beliefs.** Probabilities come from calibrating how often each kind of
  oracle judgement is right on validation data (brief 003), never from the
  LLM's own stated confidence. DESIGN D1: "An LLM output is never a belief."
- **Search (briefs 004–005).** A controller decides which clue to work on,
  when to pay for an expensive oracle call, and when to submit. The LLM is
  one of the computations it can buy.

That's why a cheap model (Haiku) is enough. Its job shrinks from "solve the
clue" to "suggest candidates and parses", which the verifier then filters.
