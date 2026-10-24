# Report — brief 017 (harder puzzles: does asking directly hold up?)

Status: **complete (2026-10-24).** Built by `opus`.

Spend: **$10.02** of the $15 cap.

| part | $ |
|---|---|
| smoke | 0.32 |
| arm (a), new calls | 9.53 |
| arm (b), escalation | 0.17 |

Phase 3 envelope: $40.45 of $60. Cumulative across briefs 000–017:
**$285.59**.

**The sets.** Post-cutoff Times daily cryptics (from Times for the Times)
and Telegraph Toughies (from Big Dave's Crossword Blog), dated
2026-08-01 to 2026-10-24.
- Harvested under 012's protocol: the REST API, one category per source,
  20 s between requests, the project's User-Agent, local only, nothing
  committed. The author approved both sources (QUESTIONS § 017).
- 20 Times and 16 Toughie grids, sampled by seed 20261031 and pinned in
  `data/eval.json` before any was read (e027b06).
- Every grid was read once, by both arms.

## Headline number

**Opus asked directly (015's D1, unchanged): 28 / 36 grids fully
correct, 0.78, Beta(1,1) 90% interval [0.64, 0.87].**

| | fully correct | 90% interval | clues | crossing conflicts | ECE (stated) | $ / grid |
|---|---|---|---|---|---|---|
| **pooled** | **28 / 36** | [0.64, 0.87] | 0.993 | 0 | 0.067 | 0.27 |
| Times | 16 / 20 | [0.62, 0.90] | 0.993 | 0 | 0.063 | |
| Toughie | 12 / 16 | [0.54, 0.88] | 0.992 | 0 | 0.073 | |
| *015's dailies (different puzzles, not paired)* | *30 / 40* | | *0.992* | | *0.074* | *0.28* |
| *016's fresh dailies (different puzzles)* | *35 / 40* | | *0.996* | | *0.071* | *0.26* |

**Decision (written before the data):** the pooled lower bound, 0.64, is
≥ 0.5, so **the direct result holds on hard dailies.** The note can claim
it for the Times and the Toughie with these numbers. Hard puzzles cost
D1 little: 0.78 on them against 0.75 and 0.88 on the two daily sets.

## Arm (b): 016's hybrid, unchanged (`lead`'s ee33af0)

The same calibration map, BP, escalation and $1.00 budget as 016. It
reuses (a)'s calls by replay. ee33af0 landed before any 017 result was
read; (b) ran after (a), from (a)'s log, which the lead approved.

| | fully correct | clues | ECE |
|---|---|---|---|
| (a) direct | 28 / 36 | 0.993 | 0.067 stated, 0.004 through the map |
| (b) hybrid | 29 / 36 | 0.994 | 0.002 (final marginals) |

- **Paired:** both 28, only hybrid 1 (a Times grid), only direct 0,
  neither 7. On Toughies alone the arms are level (12 and 12).
- **Secondary decision:** θ ~ Beta(2, 1), **P(θ > ½) = 0.75**, the
  middle band. **Direct stays the default**, and the hybrid line closes
  as an accuracy claim. Its measured value is calibration: marginal ECE
  0.002 against 0.067 for D's stated confidence.
- The hybrid overturned 1 of D's answers, wrong → right, and nothing
  right → wrong. Stops: 33 grids had every slot committed, 3 had no new
  candidates.

## D's misses

Each of the 8 grids D got wrong has **exactly one wrong slot**, as in
015 and 016. The wrong answers' stated confidences and what the hybrid
did with them:

| publisher | stated confidence | hybrid |
|---|---|---|
| Times | 0.45 | repaired by escalation |
| Toughie | 0.45 | escalated, nothing new found |
| Times | 0.70 | committed from its calibrated prior |
| Toughie | 0.85 | committed from its calibrated prior |
| Times | 0.88 | committed from its calibrated prior |
| Toughie | 0.88 | committed from its calibrated prior |
| Times | 0.90 | committed from its calibrated prior |
| Toughie | 0.95 | committed from its calibrated prior |

Two of the 8 were stated at ≥ 0.9. In 016 it was 1 of 5, and in 015's
dev grids 0 of 10. 016's steep map commits 6 of these 8 before the grid
can test them, which is the limit 016's report named.

## Stage 0: the harvest (`reports/017/harvest.json`, counts only)

| source | posts | rows parsed | unique grids | incomplete | no grid | node limit | after 012's row checks |
|---|---|---|---|---|---|---|---|
| Times for the Times, Daily Cryptic | 60 | 1,774 | 54 | 2 | 3 | 1 | 54 |
| Big Dave, Toughie Crosswords | 46 | 662 | 16 | 21 | 8 | 1 | 16 |

- 012's parser, unchanged, read both sites' markup (signatures `table/*`
  for Times; `p+br/*` and `p/span` for Toughie).
- "Incomplete" means a clue number had no row. As in 012, this is mostly
  linked clues, which Toughies use often. The set therefore leans away
  from linked-clue puzzles, as 012's did.
- Every unique grid passed 012's row invariants.
- **Requests:** Times for the Times 3 (robots.txt, categories, posts),
  Big Dave's 5 (robots.txt, 3 category pages, posts).

## Choices I made where the brief was open

- **Categories:**
  - Times for the Times category 11, "Daily Cryptic". Quick, Jumbo,
    Weekend and Mephisto are separate categories and were not taken.
  - Big Dave's category 11, "Toughie Crosswords". Sunday Toughies are a
    separate category and were not taken.
- **The Toughie smoke grid is the first pinned Toughie,** since all 16
  are pinned. Its result was not printed, and the run replayed the call.
  The Times smoke grid came from outside the list. The lead approved
  both.
- **Smoke vs run cost:** the smoke projected $0.16 per grid, and the run
  cost $0.27. Some grids took longer thinking; it stayed under the cap.

## What was built

- **`ximenes.harvest`:** sources (`fetch(..., source)` asks for one
  category; `parse_all(..., publishers)`) and `--source`.
- **`ximenes.e2e.grids(publishers=...)`.**
- **`ximenes.hard`:** split, smoke, run, summary, and the `hybrid` step
  for arm (b).
- **`ximenes.direct.run(..., paths)` and `ximenes.hybrid.run(..., paths)`.**
- **`tests/test_017_hard.py`:** a source fetch asks for its category
  only; the pooled bands; the per-publisher summary.

## Supersessions (D8)

None.

## Reproduce

```bash
uv run python -m ximenes.harvest fetch --source tftt;  uv run python -m ximenes.harvest parse --source tftt
uv run python -m ximenes.harvest fetch --source bigdave; uv run python -m ximenes.harvest parse --source bigdave
uv run python -m ximenes.hard split
uv run python -m ximenes.hard run --smoke
uv run python -m ximenes.hard run --log <smoke log>                 # run 20261024T162803Z-hard
uv run python -m ximenes.hard hybrid --log <that run's log>         # run 20261024T163938Z-hybrid
```

The summaries are in `reports/017/direct.json` and
`reports/017/hybrid.json`.

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
310 passed
== kit: GREEN
```

## Open questions (for `lead`)

1. **Direct holds on hard puzzles** (28/36). With 015 and 016 it is
   93/116 grids over three sets. The note's headline could now be the
   pooled direct rate, with the bespoke solver's 17/40 beside it.
2. **The hybrid's edge is 2–0 over 76 paired grids (016 + 017).** Pooled,
   P(θ > ½) = 0.875, which would clear 0.8. But no pooled rule was
   pre-registered, so it decides nothing; I'm reporting it, not claiming
   it.

## Probability complete

**0.85.** The harvest followed 012's protocol. The list was pinned
before any read, and the arms ran as pinned and amended. Both rules were
applied as written, under the cap. Doubts: n = 16 Toughies, because the
parser loses linked-clue puzzles; and the smoke's cost projection was
low.
