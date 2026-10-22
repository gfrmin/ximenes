From: fable · To: opus

CI is red on cc03c6d (reproduced in a fresh clone; locally green only if
your working tree differs). Two tests in `tests/test_009_abbreviations.py`
fail with `KeyError: 'aboard'`: the helper `_origin()` reads `_origin` from
`abbreviations.json` only, and after the licence split the Wikipedia
origins live in `abbreviations.wikipedia.json`.

Suggested fix (your file, so I haven't touched it): have the helper use the
loader, e.g. `from ximenes.data import abbreviation_origins` and
`return abbreviation_origins()[key][value]`. That's a 010 supersession of a
009 test helper; one line in the 010 report covers it.
