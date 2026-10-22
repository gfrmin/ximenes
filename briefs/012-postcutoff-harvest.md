# Brief 012 — Post-cutoff puzzles from Fifteensquared

Headline number: **post-cutoff puzzles harvested** (from 2026-08-01), by
publisher, with **clues parsed / clues in puzzle**, and **grids
reconstructed uniquely** from numbering + enumerations + answers (brief
004's method). **Spend: $0** (no model calls). Runs locally on the
author's machine; nothing harvested is ever committed.

## Why
Every number so far is on Cryptonite (2000–2020), which strong models have
probably seen. Fifteensquared (https://fifteensquared.net) blogs Guardian,
Independent, FT and other cryptics daily: every clue with its number,
direction and enumeration, the answer in bold, and a wordplay explanation.
That is a post-cutoff evaluation set, with gold explanations, and, via
reconstruction, grids. It replaces the need for the author to supply
puzzles.

## Etiquette (non-negotiable)
- Use the WordPress REST API (`/wp-json/wp/v2/posts?after=…&per_page=100`,
  `content.rendered`), not page crawling: a few requests in total.
- robots.txt asks for a **20-second crawl delay**: at least 20 s between
  any two requests. Stop on any 403/429 and report it.
- User-Agent: `ximenes-research (https://github.com/gfrmin/ximenes)`. No
  personal details (AGENTS.md).
- Raw responses and everything parsed stay under `data/postcutoff/`
  (gitignored). Reports carry counts and ids only, never clue text,
  answers or explanations. The explanations are never put in any prompt.
- Skip posts for prize puzzles until their closing date, and any post the
  site marks as not for discussion.

## Build
1. `ximenes.harvest` (an I/O module, allowed network like `instruments`):
   fetch posts dated ≥ 2026-08-01 for the daily cryptics: Guardian Cryptic,
   Independent, FT, Times (if blogged), Everyman/Quiptic flagged
   separately. Store raw JSON per post.
2. **Parser** for the clue lists. Blogger formats vary (lists, tables,
   bold answers, coloured definitions); borrow mdda/cryptic-wordplay's
   author-aware parsing rules where they apply. Output rows in the
   post-cutoff format of QUESTIONS § 000 item 5 (Cryptonite fields plus
   `wordplay`, `clue_marked` where the definition is marked, `source_url`),
   one file per puzzle `<publisher>-<number>-<yyyy-mm-dd>.jsonl`. A puzzle
   counts as complete only if every clue number in the grid has a row.
3. **Reconstruction:** run `ximenes.grid.reconstruct` on complete puzzles
   (15×15, 180° symmetry; Guardian and Independent use standard blocked
   grids). Store layouts as ipuz under `data/postcutoff/grids/`.
4. **Dates:** change the post-cutoff rule from model release dates to
   model **knowledge cutoffs** plus a month's margin: a row is post-cutoff
   for model M if its date ≥ cutoff(M) + 1 month. Put `knowledge_cutoff`
   per model in `data/instruments.json` with sources (Anthropic's model
   pages; June 2026 for the current generation where stated); the floor
   becomes 2026-08-01. Update the loader and its tests; this supersedes
   brief 000's floor rule, say so in the report.

## Tests (tests/test_012_*.py)
- Parser on hand-written fixture HTML in three blogger styles (original
  text, not copied posts): numbers, directions, enumerations, answers,
  explanation lines.
- Complete-puzzle rule; reconstruction on a fixture.
- Crawl delay enforced (a fake clock).
- Loader filters by knowledge cutoff + margin; reports exclusions.
- Nothing under `data/postcutoff/` is tracked (kit already checks).

## Report
Posts fetched, by publisher; puzzles complete; clues parsed; grids
reconstructed (unique / multiple / none) by publisher; date range; number
of requests and total wall time; parser failures by blogger style. No
content. Kit output; open questions; probability complete.
