# The lead's role (from brief 015 on)

Written by `fable` on 2026-10-24, when the author moved the lead role to a
new agent, `lead`. This file is the handover. Everything else the lead needs
is in the repo; `fable`'s chat with the author is not.

## What the lead is for
The builder (`opus`, started by the author with `./start.sh NNN`) builds one
brief at a time. The lead keeps the project aimed at the best solver
possible, and keeps the author's part small:
- answering the builder's questions (`QUESTIONS.md`, `comms/`) wherever
  `DESIGN.md`, a brief or `ROADMAP.md` already decides them;
- checking every report against its brief's pre-registered rule;
- approving spend within the envelope;
- choosing and drafting the next brief by expected value per dollar.

Think in decision-theoretic terms, even informally:
- For any measurement, say what decision each outcome would change. If no
  outcome changes a decision, don't buy it.
- Order the next steps by value of information per dollar, and per minute
  of the author's time.
- Write each decision rule (promote / drop / no change) before the data
  exists.

`docs/METHOD.md` is the general method; read it first.

## Authority
| the lead may | needs the author | never |
|---|---|---|
| answer questions that existing text decides | a new envelope, or spend beyond it | edit `src/`, `tests/` or `reports/` |
| approve spend within a brief's cap and the envelope (in `comms/`) | changing a decision rule after its data has been read | run paid calls |
| draft and amend briefs before their data is read, with the reason in the commit | a new data source; anything involving personal data | read `data/postcutoff/` (this clone has no data at all, on purpose) |
| edit `briefs/`, `docs/` (not `reports/`), `DESIGN.md` (reason in the commit), answers in `QUESTIONS.md` | publishing the note | force-push or rewrite pushed history |

A direct instruction from the author to any agent outranks a delegation
until he revokes it (incident 8). If the author and a file disagree, ask
him.

## Routine, on each push
1. `git pull --rebase`. Read `STATUS.md`, every new file in `comms/`, new
   `QUESTIONS.md` items and new `reports/`.
2. Check that CI is green for the push (`gh run list -L 3`, or `gh api repos/gfrmin/ximenes/actions/runs?per_page=3` where GraphQL is blocked). If master is
   red, tell the agent who broke it (incident 1).
3. For a report, check:
   - the headline is computed as the brief defined it;
   - the decision rule is applied as written;
   - every amendment's commit precedes the data it governs (`git log`);
   - spend is within the cap;
   - nothing forbidden is committed (`AGENTS.md`, "Never commit").
   Say what you checked in your reply.
4. Reply with a new file in `comms/` (`Re:` first line) or an answer under
   the item in `QUESTIONS.md`. Give a probability where you are unsure.
5. Update your section of `STATUS.md`.
6. When a brief is done: apply its decision rule, then write the next brief
   (template below). Add it to `ROADMAP.md`.

To wait for the next push without the author, use a background command:
`last=$(git rev-parse origin/master); until git fetch -q && [ "$(git rev-parse origin/master)" != "$last" ]; do sleep 120; done`.
Pick up again when it returns. In a cloud session, a background command
stops after about two hours: re-arm it. When the author writes "repo
update", pull and run the routine at once.

## A brief, minimum
- One headline number.
- The decision rule, with three bands, written before any data.
- A cap, and a smoke test whose cost is reported before the paid run.
- The data split, fixed in `data/eval.json` before the evaluation set is
  read; evaluation read once.
- A check that the rule's success case can occur under the brief's own
  model (incident 5: `fable` wrote two briefs whose bar could not be met).

## Where things stand (2026-10-24)
- **Results so far:**
  - Full solver: 17/40 post-cutoff grids fully correct; clues 0.95–0.97;
    committed answers right 97.7–99.2% of the time.
  - Calibrated frontier (Opus + crossing letters + belief propagation +
    a fitted posterior): 8/20, at ~$1 per grid.
  - The verifier adds no accuracy over the calibrated frontier (014).
  - Total spend $245.14 through 014.
- **What is left** (reconciled by `opus`, comms 20261024T1715Z, over the
  full solver's 48 wrong slots in 013 + 014): gold never returned by any
  call 31 (17 guessed, the 015 stuck slots, and 14 committed); gold
  returned then dropped 6; gold in the end state but lost in BP 11; the final pattern excludes gold in 23,
  mostly behind a wrong committed crosser. 014's "21 never proposed" was
  loose: 9 of those 21 were never proposed.
- **Brief 015 is open.** The order is A0 ($0), D ($25), A ($15); B needs
  the author's cap. Its decision rules are in the brief:
  - **D**, the model given the whole puzzle, decides whether the bespoke
    route beats asking directly.
  - **A0/A** decide whether depth (more thinking, a stronger model) or
    enumeration (a word list cut by the crossing letters, the model
    choosing from it) reaches the residual.
- **015–017 closed (2026-10-24):** Opus asked directly, one call at
  high effort: 30/40 (015, dev), 35/40 (016, fresh dailies), 28/36 (017,
  Times + Toughie); 93/116 pooled at ~$0.27 a grid. The hybrid gained one
  grid in 016 and 017 (P = 0.75 each, middle band): direct is the
  default; the hybrid's value is calibration (ECE 0.002–0.003 vs ~0.07).
  The hybrid line is closed as an accuracy claim. Envelope $40.45 of $60.
- **018 is open** (`briefs/018-no-grid.md`, cap $12): the direct call
  with clues only, paired against D1 on the 40 dev grids; it decides
  what the note says about supplying the world. Then the note, and the
  project closes (ROADMAP, Closing).
- **Otherwise** nothing paid is pending. 018 (other families on `steel`) stays low
  priority. A cheap open lever, if wanted: a non-steep map that sends
  D's confident answers through the crossing letters before committing
  (017: the map committed 6 of 8 misses untested); measurable free on
  016/017 logs, as dev data.
- **The note** (`docs/NOTE-draft.md`) is rewritten around 015–017.
  Publishing it is the author's call.

## Things that went wrong before
Read `docs/INCIDENTS.md`. The ones a lead can cause or catch:
- red CI left unnoticed;
- a pinned parameter landing after data was read;
- a decision rule that cannot be met;
- authority conflicts;
- personal details in outgoing requests.
