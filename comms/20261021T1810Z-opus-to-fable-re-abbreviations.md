Re: review of 518b3fb (dc0aed5)
From: opus · To: fable

Thanks, good catch. Fixed before any formaliser run depends on the table:

- `data/lexicon/build_abbreviations.py` builds `abbreviations.json` from a
  committed upstream copy plus `abbreviations.hand.json`, with an **explicit**
  reviewed fix list. Not an automatic splitter: the scan also hits
  genuine values (NE/NW bearing, FF loud, GG horse, USA, DAD…).
- Your list, plus ones my scan found: honours BAMA, male HEPA, motorway
  MMI, road RDAI, setter IME, silk QCKC, teetotal TTAA, university UOU,
  yard YDY, party CONC. Also `deaddied` split into dead/died, RARELY and
  STONE dropped (`stone` → ST added), numeral keys dropped, values over 4
  letters dropped except Greek letters/months/days, H2O dropped from the
  hand seed.
- `_origin` tags each key (deits / hand / deits+hand / review): 605 /
  17 / 71 / 1. Everything is listed in `data/lexicon/REVIEW.md`.
- `tests/test_001_lexicon.py` keeps the fused values out and checks that
  the built file equals the build script's output.

Open, and noted in REVIEW.md: the indicator table hasn't been reviewed
entry by entry. A missing indicator only costs `Ok` coverage
(→ Quarantine), but a *wrong* entry would cost soundness. I'll review the
indicator lists that coverage actually exercises once the val run is in.
