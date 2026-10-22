# Playbook: how ximenes was run (candidate for a template repo)

Extracted 2026-10-22 from what worked in ximenes, set against what was
tried in wald / proplang / assize. Process first; code second.

## Principles
1. **Governance only where neither a mechanical check nor the grammar
   decides.** Every rule is either checked by CI, sound by construction, or
   written down as unchecked. Unchecked rules are few and named.
2. **One brief, one headline number,** pre-registered with its decision rule
   before any data is read (including what result would stop the line of
   work).
3. **Order experiments by value of information per dollar.** The next brief
   is the cheapest experiment that could change the next decision; a cheap
   experiment that bounds an expensive one goes first (011 bounded 013).
4. **Measure the ceiling before refining the decision layer** (recall
   before ranking: gold-in-k before verifier tuning).
5. **Fit on val; read a held-out sample once; refit gets a fresh seed;**
   tables are committed before the evaluation run, and a test checks it
   from git history.
6. **Probabilities are fitted, never taken from a model's own scores**
   (vote shares were overconfident, proposer shares underconfident).
7. **Every external call goes through one logged instrument layer:** same
   input → same output, replayable offline, memoised, costed. Every number
   in a report replays bit for bit.
8. **Report negative results first-class,** with the cause.

## Roles and files
| file | owner | purpose |
|---|---|---|
| `DESIGN.md` | lead | rules, each marked checked / unchecked |
| `briefs/NNN-*.md`, `ROADMAP.md` | lead | one brief per experiment; VOI ordering; spend envelope |
| `AGENTS.md` | all | names, git rules, claims, messages, never-commit list |
| `STATUS.md` | each agent, own section | claim, running jobs (with cost), blocked on |
| `comms/<ts>-<from>-to-<to>-<slug>.md` | sender | one file per message, replies by new file |
| `QUESTIONS.md` | builder asks, lead/author answers inline | open decisions with the builder's reading and probability |
| `reports/NNN-*.md` | builder | headline, decision-rule verdict, spend, kit output, probability complete |
| `docs/RESULTS.md` | lead | one page of every headline |

## Mechanics that paid for themselves
- `setup.sh` (data fetched and hash-checked) and `start.sh` (opens the agent
  on the next brief) make a fresh machine turnkey.
- CI runs the kit on every push; the watcher checks CI, not just the push.
- Spend authority is delegated with a cap per brief and an envelope per
  phase; the builder reports smoke cost before the full run.
- Data the agents must not read is gated in code (`allow_postcutoff=True`)
  and parsed blind (structural diagnostics only).

## Incidents and the mechanism that would have prevented each
See `docs/INCIDENTS.md`.
