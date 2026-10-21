# Starting prompt for the first Claude Code session

Run `claude` in the repo root and paste the block below. (`CLAUDE.md` is
picked up automatically; the prompt just points the session at the brief.)

---

Read `DESIGN.md`, `docs/GAME.md`, then `briefs/000-harness.md`. Do not read
anything under `data/postcutoff/`.

Build brief 000 end to end on `master`. If the brief is ambiguous, pick the
reading you think I want, say which you picked and with what probability,
and keep going; don't stop to ask unless the choice is expensive to undo.

The Cryptonite files are at `data/cryptonite/`; the `mdda/cryptic-wordplay`
clone is at `data/wordplay/`. The only LLM calls in this brief are
`propose_answers` through `ximenes.instruments`, logged as JSONL and
replayable with the `stub` backend. If `ANTHROPIC_API_KEY` is unset, build
and test everything against the stub and the 20-clue fixture, and leave the
1,000-clue run for me.

Finish with the report format in `CLAUDE.md`: headline numbers for both
sets side by side, full `./kit/check.sh` output, open questions, probability
complete. Commit as you go; make the last commit message the one-line summary
of the headline number.

---

## Before you run it
- Place Cryptonite JSONL under `data/cryptonite/` (not committed).
- Clone `mdda/cryptic-wordplay` into `data/wordplay/` (not committed).
- `export ANTHROPIC_API_KEY=...`, or skip it and run the 1,000-clue pass
  yourself afterwards.
- Read `DESIGN.md` D9 and `docs/GAME.md` once; D9 is the rule most likely to
  change as you learn.
