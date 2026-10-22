# Lexicon review

`abbr(...)` and the indicator check are **mechanical** steps (DESIGN D4): a
wrong table entry makes an `Ok` verdict unsound. Entries are therefore
reviewed, and every change from upstream is listed here. Rebuild with
`uv run python data/lexicon/build_abbreviations.py`.

## abbreviations.json

Sources: `abbreviations.hand.json` (hand seed, origin `hand`) and
`upstream/CrypticCrosswords.jl-abbreviations.json` (rdeits/CrypticCrosswords.jl,
MIT, origin `deits`). `_origin` in the built file tags each key
(`deits`, `hand`, `deits+hand`, `review`). As built 2026-10-21: 693 keys,
605 `deits` only (reviewed for the problems below, not entry by entry),
71 `deits+hand`, 17 `hand`, 1 `review`.

Changes from upstream (reported by fable on 2026-10-21 in
`comms/…fable-to-opus…`, extended by opus's scan for unique values that are
concatenations of common ones, then checked by hand):

| key | upstream value | becomes | why |
|---|---|---|---|
| america | USUSA | US, USA | fused |
| australia | AUSOZ | AUS, OZ | fused |
| bishop | BRR | B, RR | fused |
| caught | CCT | C, CT | fused |
| church | CHCERC | CH, CE, RC | fused |
| honours | BAMA | BA, MA | fused |
| male | HEPA | HE, PA | fused |
| motorway | MMI | M, MI | fused (M1) |
| party | CONC | CON | fused; stray C dropped |
| railway | RYBR | RY, BR | fused |
| road | RDAI | RD, AI | fused (A1) |
| setter | IME | I, ME | fused |
| silk | QCKC | QC, KC | fused |
| teetotal | TTAA | TT, AA | fused |
| university | UOU | U, OU | fused |
| versus | VVS | V, VS | fused |
| yard | YDY | YD, Y | fused |
| year | YYR | Y, YR | fused |
| `deaddied` (key) | D, DEC, EX, OB | keys `dead` and `died` | fused key |
| one | RARELY | dropped | scrape error |
| st | STONE | dropped; `stone` → ST added | direction reversed |
| many | XD... | dropped | not letters |
| numeral keys (1, 10, 1_000, …) | | dropped | clue tokens are letters only |
| any value > 4 letters | | dropped unless key is greek character/letter, month, day, thursday | fused-value guard |
| E.G. | | EG | dots removed |
| (hand seed) water | H2O | dropped | not letters |

Scan hits judged genuine and kept: e.g. USA, DAD, EVE, ACE, IOU, the month
and day abbreviations, NE/NW (bearing), FF (loud), GG (horse).

## Reviewed upstream entries (`reviewed.json`, origin `review`)

2026-10-21, brief 002: every unreviewed entry that an accepted brief-001
parse (val 300 + train 500, re-verified under brief 002's verifier) relied
on: 170 entries, 69 abbreviations and 101 indicators. Reviewed by opus (an
LLM, not a human setter) against standard crossword usage; the author may
spot-check. **165 accepted** (listed in `reviewed.json`), **5 left
unreviewed** as doubtful:

| table | entry | why not |
|---|---|---|
| abbreviations | boy → B | not a standard abbreviation |
| abbreviations | soldier → RE | RE is soldiers (Royal Engineers), not one soldier |
| indicators | anagram: becomes | usually a link word |
| indicators | insert: over | usually positional (down clues) or charade |
| indicators | reverse: twisted | usually an anagram indicator |

Entries are reviewed only when an accepted parse uses them; the rest of the
Deits lists stays unreviewed (and gives `Quarantine(table_unreviewed)`).
Nothing is added from formaliser output.

## Brief 009 (2026-10-22): Wikipedia's "Crossword abbreviations", imported whole

Source: Wikipedia contributors, "Crossword abbreviations", revision
1375193762 (2026-09-16, the last revision before this project started),
CC BY-SA 4.0. Imported whole (621 keys, 985 values; values longer than 4
letters dropped as for Deits), origin `wikipedia`. Since brief 010 these
entries live in `abbreviations.wikipedia.json` (CC BY-SA 4.0, licence in its
header) and are merged at load time; `abbreviations.json` holds hand + Deits
+ review origins only (MIT / own work). The merged table is unchanged.

Reviewed: the 91 unreviewed entries that accepted parses in brief 001
(val, train-500), brief 002 (test, chosen answers) and brief 006 (grid
round-1 records) rely on, via `abbr(...)` or via a `syn(...)` whose pair is
a table entry. **89 accepted** (in `reviewed.json`); **2 left doubtful**,
the same two as in brief 002's review, pending the author's ruling:
soldier → RE and boy → B (Wikipedia lists both). Reviewed by opus (an LLM)
against standard usage; the author's spot-check (QUESTIONS § 002) covers
these too.

## indicators.json

Built by `build_indicators.py` from `indicators.hand.json` (the hand seed,
plus hand lists for brief 002's new operators written by opus from standard
usage, not from formaliser output), rdeits/CrypticCrosswords.jl
`corpora/indicators` (MIT; mapping in the build script) and `reviewed.json`.
Per-entry `_origin`. A missing indicator gives `Quarantine(indicator)`; an
unreviewed upstream one gives `Quarantine(table_unreviewed)`.
