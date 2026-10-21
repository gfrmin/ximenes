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

## indicators.json

Hand seed merged with rdeits/CrypticCrosswords.jl `corpora/indicators`
(MIT); mapping in the file's `source`. An indicator that is missing gives
`Quarantine(indicator)`, never `Ok`, so a missing entry costs coverage of
`Ok`, not soundness. A *wrong* entry would cost soundness: not yet reviewed
entry by entry (open item).
