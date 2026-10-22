# Report — brief 012 (post-cutoff puzzles from Fifteensquared)

Status: **complete (2026-10-22).** Built by `opus`. **Spend: $0** (no model
calls). The author approved fetching ("just get the data, don't look at
them"). The parser was built blind: from hand-written fixtures and structural
counts only. No clue, answer or explanation was read, printed or
committed. Cumulative across briefs 000–012: **$122.87**.

## Headline numbers

Posts dated 2026-08-01 to 2026-10-22, fetched through the WordPress REST
API: **356 posts in 5 requests** (20 s apart, 88 s in all; no 403 or 429).
One more request to the RSS feed (`update` mode) found 1 newer post, not yet
parsed.

| publisher | posts | clues parsed | **unique grids** | clues in complete puzzles | incomplete (number gap) | no grid | search limit | multiple |
|---|---|---|---|---|---|---|---|---|
| FT | 77 | 2,109 | **49** | 1,485 | 14 | 3 | 6 | 0 |
| Independent | 84 | 2,265 | **42** | 1,281 | 17 | 16 | 7 | 0 |
| Guardian | 75 | 2,065 | **31** | 895 | 28 | 6 | 8 | 0 |
| Everyman (flagged) | 12 | 252 | **9** | 252 | 0 | 3 | 0 | 0 |
| Quiptic (flagged) | 12 | 178 | **5** | 148 | 1 | 6 | 0 | 0 |
| Quick Cryptic (flagged) | 13 | 272 | 0 | 0 | 1 | 0 | 0 | 12 |
| **all kept** | **273** | **7,141** | **136** | **4,061** | 61 | 34 | 21 | 12 |

83 posts were skipped by category (barred grids such as Listener,
Inquisitor, Azed and EV; Spectator, Genius, Jumbo, FT Sunday,
announcements). Complete puzzles span **2026-08-02 to 2026-10-22**.

The 122 daily cryptics with unique grids (FT 49, Independent 42, Guardian
31) are enough for 013's 20 evaluation + 8 fit grids, three times over.

## By blogger style (structural signature: tag names only)

| signature | unique | incomplete | no grid | limit | multiple |
|---|---|---|---|---|---|
| table, definitions as styled spans | 73 | 30 | 12 | 11 | 12 |
| table, `<u>` and spans | 25 | 10 | 0 | 3 | 0 |
| paragraphs, styled spans | 25 | 7 | 1 | 4 | 0 |
| paragraphs with `<br>` lines, spans | 13 | 13 | 18 | 3 | 0 |
| other (3 signatures) | 0 | 1 | 3 | 0 | 0 |

The `<br>`-line paragraph style is the weakest (13 of 47). "Incomplete" means
a clue number has no row. The likely causes are linked clues ("see 12",
multi-slot answers), which the parser does not join, and entries whose
answer is not in a recognisable capitals run. "No grid" means every number
has a row but no layout fits. That usually means an answer was taken from
the wrong capitals run (e.g. from the explanation), so crossing letters
disagree. All 12 Quick Cryptic puzzles have more than one valid 13×13
layout.

## How the parser was improved without reading posts

- **Fixtures:** three hand-written blogger styles (table; paragraphs with
  `<br>`; inline "1a ANSWER clue (n) – explanation"), with invented clues.
- **Diagnostics:** counts per post (entries per direction, highest
  number, missing numbers, segments that look like numbers or
  enumerations, headers), grouped by tag signature.
- **What they showed:** of 25 failing posts with no missing number, 9
  rebuilt uniquely once the search limit was 15× brief 004's. That made the
  limit the main cause, not the parser. The harvest now uses its own limit
  of 3M nodes (`harvest.reconstruct_node_limit`), and skips the search for
  posts with a numbering gap (they cannot match). Unique grids went from
  108 to 136.

## What was built

1. **`ximenes.harvest`** (I/O module, allowed network by the kit like
   `instruments`):
   - `polite()` enforces the 20 s crawl delay and stops on 403/429 or any
     non-200.
   - `fetch` (REST backfill, `_fields` trimmed) and `update` (RSS: one
     request, new posts only, as fable proposed after the author asked
     about RSS).
   - `parse` writes one Cryptonite-format JSONL per complete puzzle under
     `data/postcutoff/`. Each row carries the Cryptonite fields plus
     `wordplay`, `clue_marked` (definition in braces where the blogger
     marked it), `source_url` and `post_id`.
   - Grids are stored under `data/postcutoff/grids/` in the
     `gridsolve.load_grid` format, so 013 can load them directly. That is
     a JSON layout rather than ipuz: one format for every grid in the repo.
2. **`ximenes.fifteen`:** a pure parser.
   - It flattens HTML to segments, with underlined or definition-classed
     text in braces and bold noted.
   - "Across"/"Down" headers set the direction, or a number suffix does.
   - The clue is the segment carrying an enumeration (an inline
     explanation may follow).
   - The answer is the capitals run whose letter count matches the
     enumeration (bold preferred, or leading the clue).
   - The approach follows mdda/cryptic-wordplay's generic parser. That repo
     has no licence, so none of its code was copied.
3. **Post-cutoff rule:** a row counts for model M if it is dated on or
   after M's **knowledge cutoff + 31 days**, and never before the floor of
   **2026-08-01**. `knowledge_cutoff` per model is in
   `data/instruments.json`. Opus 5.5 is June 2026 (stated); Sonnet and
   Haiku 5.5 are assumed June 2026 per the brief, to be checked.
   `load_postcutoff(cutoffs=...)` replaces `released=`.
4. **Tests:**
   - `tests/test_012_parse.py`: three styles; numbers, directions,
     enumerations, answers, marked definitions, explanations; a
     wrong-length answer dropped.
   - `tests/test_012_harvest.py`:
     - crawl delay under a fake clock;
     - stop statuses;
     - paging;
     - the complete-puzzle rule and reconstruction on a synthetic 7×7 post
       (one clue removed gives no puzzle);
     - the RSS update storing only new posts.

## Supersessions (D8)

- `tests/test_000_postcutoff.py::test_only_eval_mentions_postcutoff`: now
  `eval.py` and `harvest.py`. The brief requires the harvester to write
  under `data/postcutoff/`.
- `tests/test_000_postcutoff.py`, the release-date tests: replaced by
  knowledge-cutoff tests (floor 2026-08-01, cutoff + 31 days), as the brief
  directs.
- `kit/lint_forbidden.py`: `harvest` added to the modules allowed I/O and
  network.

## Reproduce

```bash
uv run python -m ximenes.harvest fetch    # 5 requests, ~90 s
uv run python -m ximenes.harvest update   # 1 request (RSS)
uv run python -m ximenes.harvest parse    # ~70 min (reconstruction search)
```

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 26%]
........................................................................ [ 53%]
........................................................................ [ 80%]
...................................................                      [100%]
267 passed in 17.92s
== kit: GREEN
```

## Open questions

See `QUESTIONS.md` § Brief 012.

## Probability complete

**0.8.** Every build item and test exists, etiquette held (5 + 1 requests,
no stops), nothing harvested is tracked, and 013 has enough grids.
Doubts:
- The parser is blind, so a systematic error that still yields consistent
  grids would go unseen. The likeliest is a clue's text cut at a "(" inside
  it. Reconstruction checks answers and layout, not clue text.
- Linked clues are dropped, which biases the set against puzzles that
  use them.
- Sonnet and Haiku cutoffs are assumed. The floor makes them irrelevant
  for current data.
