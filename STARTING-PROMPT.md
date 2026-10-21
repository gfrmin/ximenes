# Starting prompt for the first Claude Code session

Run `claude` in the repo root and paste the block below. (CLAUDE.md is picked
up automatically; the prompt just points the session at the first brief and
sets the reporting contract.)

---

You are the builder for this repository. Read `CLAUDE.md`, then `CHARTER.md`,
then `briefs/000-harness.md`, in that order. Do not read anything under
`data/postcutoff/`.

Before writing code, report back in ≤ 15 lines:
1. Any conflict you see between the brief and the charter.
2. Your plan for brief 000 as a list of laws you will add under
   `tests/laws/000/` (names and one-line intents only).
3. Anything the brief leaves ambiguous, each with the reading you intend to
   take and a probability (0–1) that it is the reading I want.
Then stop and wait for my go-ahead.

After go-ahead: work on branch `b/000-harness`. Run `./kit/check.sh` and
`pytest -q` as you go. When done, give the report in the format CLAUDE.md
requires (headline numbers for the two sets, full kit output, open questions,
probability complete). Do not open or merge a pull request; that is my step.

Constraints to keep in mind for this brief: the only LLM calls are
`propose_answers` through `ximenes.instruments`, logged as JSONL and
replayable with the `stub` backend; no verifier, no wordplay prompting, no
fine-tuning. The Cryptonite files are at `data/cryptonite/`; the
post-cutoff set is mine and the loader must refuse it outside
`ximenes.eval(allow_postcutoff=True)`.

---

## Before you run it
- Place Cryptonite JSONL under `data/cryptonite/` (not committed).
- Clone `mdda/cryptic-wordplay` into `data/wordplay/` (not committed).
- `export ANTHROPIC_API_KEY=...` (or set the brief to use the stub only on
  the first pass and let it build the harness against the 20-clue fixture).
- Sign the charter once you've read it: `git tag -s charter-v0 -m "signed"`.
- Decide `u_wrong ∈ {−5, −9}` now and write it in `briefs/003-*.md` before any
  brief-002 numbers exist, so it is pre-registered.
