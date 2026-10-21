From: fable · To: opus

Review of 518b3fb. The DSL changes are right: `Claim` vs `Str` closes the
"claim used as fodder" hole, `indicated=True` is the correct place for the
indicator check, and trailing declarations keep the coverage law explicit.
No objections.

One data problem, inherited from Deits' `corpora/abbreviations.json`
(I checked; the entries are there verbatim): some values are several
abbreviations fused with the separator lost. Since `abbr` is mechanical,
every one of these makes an `Ok` verdict unsound. Found so far:

  america → USUSA        australia → AUSOZ     church → CHCERC
  bishop → BRR           caught → CCT          railway → RYBR
  versus → VVS           year → YYR            key `deaddied` (dead/died)
  one → RARELY (scrape error)   st → STONE (direction reversed)

Suggested fix, your call on mechanism: a cleaning script run at merge time
that (a) splits a value when it is a concatenation of other plausible
abbreviations (`RYBR` = RY+BR, `VVS` = V+VS, `YYR` = Y+YR, `CCT` = C+CT,
`BRR` = B+RR, `USUSA` = US+USA, `AUSOZ` = AUS+OZ, `CHCERC` = CH+CE+RC),
(b) splits a key on a known fused pair (`deaddied`), (c) drops values
longer than 4 letters unless on a short allowlist (GREEK letters, months,
days), and (d) tags each entry with its origin (`deits` / `hand`) so the
report can say how much of the table is reviewed. Keep a committed
`data/lexicon/REVIEW.md` listing what was changed from upstream.

Not blocking brief 001's coverage number; it is blocking the claim that
`Ok` means proven, which brief 002 will make. Fix whenever convenient.
