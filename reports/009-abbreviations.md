# Report — brief 009 (abbreviations hiding as synonyms)

Status: **complete (2026-10-22).** Built by `opus`. **Spend: $0** (offline
re-verification of logged parses). Cumulative across briefs 000–009:
**$103.18**.

## Headline numbers

`Ok` share of accepted parses, by offline re-verification. State 1 is brief
008's verifier and table. State 2 adds the new rule (a `syn` step on a
reviewed abbreviation entry is a mechanical table hit) with the old reviewed
set. State 3 is the rule plus Wikipedia's list and the 89 entries reviewed
in this brief.

| set (accepted parses) | state 1: 008 | state 2: + syn rule | **state 3: + Wikipedia, reviewed** | syn leaves → table hits (1 → 3) |
|---|---|---|---|---|
| 001 gold, val (257) | 23 (8.9%) | 24 (9.3%) | **25 (9.7%)** | 298 → 269 (−29) |
| 001 gold, train-500 (423) | 42 (9.9%) | 42 (9.9%) | **48 (11.3%)** | 469 → 430 (−39) |
| 002 test, chosen answers (940) | 37 (3.9%) | 38 (4.0%) | **43 (4.6%)** | 847 → 776 (−71) |
| 006 grid round-1 records (165) | 1 (0.6%) | 2 (1.2%) | **2 (1.2%)** | 134 → 130 (−4) |

| brief 006's 10 evaluation grids | before | after |
|---|---|---|
| **proven slots** (committed, `Ok`, right, every crosser committed) | **0** | **0** |
| committed slots that are both right and `Ok` | 1 of 162 | 1 of 162 |

**The lever works mechanically, but is small.** About 9% of synonym leaves
become table hits (29 of 298 on val, 71 of 847 on 002's chosen answers). A
parse usually rests on several synonym steps, though, and converting one
makes it `Ok` only if every step is then mechanical. So `Ok` rises by 0.5–1.4
points, and proven slots on the grids stay at zero. The remaining synonym
leaves are mostly genuine synonyms and definitions by example (008), which
no abbreviation list covers.

**Mutation suite with the new table: 0 false accepts** on val (1,127
mutants) and train (1,799), re-verifying the final logged parses.

## The source

Wikipedia contributors, "Crossword abbreviations", revision **1375193762**
(2026-09-16), CC BY-SA 4.0. That is the last revision before this project
started; the page was edited on 2026-10-21, during the project, so that
revision was not used. Imported whole: 621 keys, 985 values (values longer
than 4 letters dropped, as for Deits). Origin `wikipedia`; 355 entries are new
to the table, and 456 + 104 + 56 overlap with Deits / hand / reviewed. As an
adaptation, `data/lexicon/abbreviations.json` is now CC BY-SA 4.0 (stated in
its header and in REVIEW.md). `setup.sh` fetches the pinned revision and
checks its hash.

## Review

91 unreviewed entries are relied on by accepted parses in the four sets
(via `abbr(...)`, or via `syn(...)` whose pair is a table entry).
**89 accepted, 2 left doubtful:** soldier → RE and boy → B, the same two
brief 002 left for the author (Wikipedia lists both). All listed in
`data/lexicon/REVIEW.md` and `reviewed.json`. **Reviewed by an LLM**;
the author's spot-check (QUESTIONS § 002) covers these too.

The entries hit most often: article → THE (6) · at home → IN (5) ·
republican → R (4) · hospital department → ENT (4) · European → E (3) ·
cold → C (3) · ecstasy → E (3) · revolutionary → CHE (3) · lake → L (3) ·
quietly → P (3) · tense → T (2) · communist → RED (2) · earl → E (2) ·
area → A (2) · record → EP (2) · worker → ANT (2) · Spain → E (2) ·
friend → PAL (2) · good man → ST (2) · lecturer → L (2).

Several of brief 008's motivating pairs aren't on the Wikipedia page (women
→ W, French → FR, councillor → CR, turn → U, concerts → C), so they remain
synonyms. A second sourced list would be needed for those.

## What was built

- `data/lexicon/build_abbreviations.py`: `parse_wikipedia` (A–Z sections;
  keys split on "or", commas and slashes; letter-only `<small>` values) and
  a hash check on the pinned revision.
- `verify.py`: a `syn` step on a *reviewed* abbreviation entry is recorded
  as an abbreviation table hit, with no synonym reason or leaf. Otherwise
  it is unchanged. An unreviewed entry under `abbr(...)` still gives
  `Quarantine(table_unreviewed)`.
- `tests/test_009_abbreviations.py`: the parser on an excerpt in the page's
  format (lettered sections only); `syn` on a reviewed entry is `Ok` with a
  table hit; on an unreviewed one it stays a synonym (and `abbr` on it is
  `table_unreviewed`); a non-table synonym is unchanged.

## Supersessions (D8)

- `tests/test_001_verify.py::test_abbr_and_syn`: `syn` on a reviewed entry
  is now `Ok`; on an unreviewed one it is still `Quarantine(synonym)`.
- `tests/test_002_solve.py::test_headline_run_replays_exactly`: under the
  new verifier some verdicts (and so retries and judge calls) differ from
  the 2026-10-21 run. Brief 002's headline stands for that day's table; the
  test now checks the replay is deterministic, with calls the old run never
  made producing nothing.
- `tests/test_001_lexicon.py::test_built_file_matches_build_script`:
  skipped where the Wikipedia source isn't fetched (CI); the build now reads
  it.

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 31%]
........................................................................ [ 62%]
........................................................................ [ 93%]
..............                                                           [100%]
230 passed in 17.88s
== kit: GREEN
```

## Open questions

See `QUESTIONS.md` § Brief 009.

## Probability complete

**0.85.** Every build item and test exists, nothing was called, the whole
list was imported (not selected on outcome), the revision predates the
project, and the mutation suite is clean. Doubts: the review is an LLM's,
and "proven slots" on the grids depends on reconstructing which word each
committed slot held from the replayed run (it is 0 either way).
