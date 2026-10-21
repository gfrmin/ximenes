# data/

| path | committed? | source | notes |
|---|---|---|---|
| `lexicon/indicators.json` | yes | seeded by hand; extend from Deits (`rdeits/cryptics`) and A&W verifier repo | `{indicator phrase: [operator, ...]}` |
| `lexicon/abbreviations.json` | yes | seeded by hand; extend from Deits | `{word: [ABBR, ...]}` |
| `cryptonite/` | **no** | Efrat et al. 2021 (aviaefrat/cryptonite) | author places files; `SPLITS.sha256` is committed by brief 000 |
| `wordplay/` | **no** | mdda/cryptic-wordplay | explanations with `{definition}` spans |
| `postcutoff/` | **never** | author-maintained; Times/Guardian/FT after every model cutoff, with Fifteensquared / Times for the Times parses | opened only by `ximenes.eval` with `allow_postcutoff=True` |

Every table carries a top-level `"source"` field. A number without a source
fails the kit.
