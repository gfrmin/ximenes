# Agents working on ximenes

More than one coding agent works in this repo at the same time, often in
different sessions that can't see each other. **The repo is the only shared
channel.** Anything another agent needs to know goes in a committed and
pushed file, not only in a chat with the author.

Read this file, `CLAUDE.md`, `DESIGN.md` and `STATUS.md` before starting work.

## Names

Each agent picks a short, stable name and uses it everywhere: in `STATUS.md`,
in message filenames, and as a commit trailer `Agent: <name>`.

| name | who | first seen |
|---|---|---|
| `fable` | Claude session in claude.ai (Fable 5.1 until 2026-10-22 ~05:00 UTC, Opus 5.5 after; still `fable`, distinct from the `opus` builder), working with the author: scaffold, briefs, docs, reviews, answers in `QUESTIONS.md` on the author's behalf (git author `builder`, then `fable`, then `Claude <noreply@anthropic.com>` from 2026-10-21 ~18:30 UTC; the `Agent: fable` trailer is the identity) | 2026-10-21 |
| `opus` | Claude Opus 5.5 session: brief 000 harness | 2026-10-21 |

New agent: add a row in your first commit.

## Git

1. `git pull --rebase` before starting, before every commit, and before
   every push.
2. Small commits, pushed promptly. Unpushed work is invisible to the others.
3. Never force-push, and never rewrite history that has been pushed.
   Rewriting your own *unpushed* commits is fine.
4. Work on `master` (see `CLAUDE.md`). If a rebase conflicts in a file
   another agent owns (see Claims), keep their version and send a message
   (below). Don't merge over their work by guesswork.
5. CI runs `./kit/check.sh` on every push. Don't push red. If you find
   master red, the agent whose commit broke it fixes it. Message them if
   they aren't fixing it.

## STATUS.md: claims and running jobs

`STATUS.md` has one section per agent. **Edit only your own section**, which
keeps rebase conflicts away. Keep it current:

- **Working on:** brief number and task, and the files or directories you
  are changing (your *claim*). Don't edit files another agent has claimed;
  send a message instead.
- **Running jobs:** anything long or costly (API runs, downloads): the
  command, run id, start time, expected end, expected cost. This stops two
  agents paying for the same run. Never start a paid run that duplicates
  one listed here.
- **Blocked on:** what you're waiting for, and from whom.

Clear your claim when you finish or stop.

## Messages: `comms/`

To tell or ask another agent something, add **one new file per message**:

```
comms/<YYYYMMDDTHHMMZ>-<from>-to-<to|all>-<slug>.md
```

with the context needed to act on it without the sender's chat history.
One file per message means two agents never conflict editing the same file.
Never edit someone else's message. Reply with a new file whose first line
is `Re: <filename>`. When a message has been dealt with, the recipient adds
a reply saying so; don't delete messages.

On starting a session, read every file in `comms/` newer than your last
reply.

## Where things go

| what | where |
|---|---|
| questions only the author can answer | `QUESTIONS.md` (by brief; your reading and probability) |
| brief reports, headline numbers | `reports/NNN-*.md`; run summaries in `reports/NNN/` |
| design changes | `DESIGN.md`, with the reason in the commit (DESIGN preamble) |
| how LLMs are used | `docs/LLM-USE.md` |
| brief completion | append `NNN` to `briefs/DONE`, last commit = one-line headline (`CLAUDE.md`) |
| run logs | `runs/` (gitignored, local only); summaries go to `reports/` |

## Never commit

- Cryptonite or cryptic-wordplay rows, or clue text from them. The datasets
  are unlicensed newspaper text, used locally only, and this repo is public.
  Summaries carry split indices, not clues.
- Anything under `data/postcutoff/` (never read it either; see `CLAUDE.md`).
- Secrets. Keys live in gnome-keyring (`secret-tool lookup service env key
  NAME`). Don't put them on a command line (`curl -H "Authorization: ..."`),
  because argv shows up in `ps` and in tool output. Use env vars or header
  files.
- The author's personal details (name, email, location) in any outgoing
  request or file. Where an API wants contact info (Wikipedia's User-Agent
  policy, say), use the project: `ximenes (https://github.com/gfrmin/ximenes)`.
