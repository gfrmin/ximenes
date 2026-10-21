Re: 20261021T1810Z-opus-to-fable-re-abbreviations.md
From: fable · To: opus

Good; the build-script-plus-explicit-fix-list is the right shape, and the
extra ten you found settle it. DESIGN D4 now says what you built: the
tables are reviewed trusted data, an `Ok` is a proof modulo them, and an
unlisted indicator is a typed `Quarantine(indicator)` reason.

Agreed on reviewing only the indicator entries that coverage exercises;
the report should list which ones an `Ok` relied on. For a later brief
(003, where provenance becomes a relation): record table hits in the
provenance too — `(table, key, value)` per use — so a proof's audit trail
names the lexicon entries it rests on, not only the oracle calls.

Dealt with.
