Read `DESIGN.md`, `docs/GAME.md`, then `{BRIEF}`. Do not read anything under
`data/postcutoff/`.

Build brief {NUM} end to end on `master`. If the brief is ambiguous, pick the
reading you think I want, say which you picked and with what probability, and
keep going; stop to ask only if the choice is expensive to undo.

Data is already in place: Cryptonite under `data/cryptonite/` (hashes in
`SPLITS.sha256`), the wordplay sample under `data/wordplay/`. LLM and oracle
calls go through `ximenes.instruments` and are logged as JSONL under `runs/`,
replayable with the `stub` backend. If `ANTHROPIC_API_KEY` is unset, build and
test everything against the stub and a checked-in fixture, and leave the
full run for me with the exact command to run it.

Commit as you go. When the brief is done: run `./kit/check.sh`; append `{NUM}`
on its own line to `briefs/DONE`; make the last commit message a one-line
summary of the headline number. Then give the report in the format
`CLAUDE.md` requires: headline number(s), full kit output, open questions,
probability complete.
