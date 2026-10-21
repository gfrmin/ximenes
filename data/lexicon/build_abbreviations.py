"""Build data/lexicon/abbreviations.json from its two sources, with reviewed fixes.

    uv run python data/lexicon/build_abbreviations.py

Sources:
  abbreviations.hand.json                          hand seed (origin "hand")
  upstream/CrypticCrosswords.jl-abbreviations.json rdeits/CrypticCrosswords.jl
      corpora/abbreviations.json, MIT (c) 2019 Robin Deits (origin "deits")

Every change from upstream is listed in REVIEW.md. abbr() is a mechanical
operator, so a bad value here makes an Ok verdict unsound: fixes are explicit
and reviewed, never inferred.
"""

import json
import pathlib

HERE = pathlib.Path(__file__).parent

# Upstream values that are several abbreviations fused, the separator lost.
SPLIT = {
    ("america", "USUSA"): ("US", "USA"),
    ("australia", "AUSOZ"): ("AUS", "OZ"),
    ("bishop", "BRR"): ("B", "RR"),
    ("caught", "CCT"): ("C", "CT"),
    ("church", "CHCERC"): ("CH", "CE", "RC"),
    ("honours", "BAMA"): ("BA", "MA"),
    ("male", "HEPA"): ("HE", "PA"),
    ("motorway", "MMI"): ("M", "MI"),
    ("party", "CONC"): ("CON",),
    ("railway", "RYBR"): ("RY", "BR"),
    ("road", "RDAI"): ("RD", "AI"),
    ("setter", "IME"): ("I", "ME"),
    ("silk", "QCKC"): ("QC", "KC"),
    ("teetotal", "TTAA"): ("TT", "AA"),
    ("university", "UOU"): ("U", "OU"),
    ("versus", "VVS"): ("V", "VS"),
    ("yard", "YDY"): ("YD", "Y"),
    ("year", "YYR"): ("Y", "YR"),
}
# Upstream keys that are two keys fused.
SPLIT_KEYS = {"deaddied": ("dead", "died")}
# Upstream values that are wrong, not fused.
DROP = {
    ("one", "RARELY"),  # scrape error
    ("st", "STONE"),  # direction reversed: stone -> ST, added below
    ("many", "XD..."),  # not letters
}
ADD = {"stone": ("ST",)}
# Values longer than MAX_LETTERS are dropped unless the key is on this list.
LONG_OK = {"greek character", "greek letter", "month", "day", "thursday"}
MAX_LETTERS = 4


def _norm_key(k: str) -> str:
    return k.replace("_", " ").lower().strip()


def build() -> dict:
    hand = json.loads((HERE / "abbreviations.hand.json").read_text())
    up = json.loads((HERE / "upstream" / "CrypticCrosswords.jl-abbreviations.json").read_text())
    table: dict[str, set[str]] = {}
    origin: dict[str, set[str]] = {}

    def add(key: str, values: list[str] | tuple[str, ...], src: str) -> None:
        table.setdefault(key, set()).update(values)
        origin.setdefault(key, set()).add(src)

    for raw_key, raw_values in up.items():
        key = _norm_key(raw_key)
        if key.replace(" ", "").isdigit():
            continue  # numerals never occur as clue tokens (letters only)
        values: list[str] = []
        for v in (x.upper().replace(".", "") for x in raw_values):
            if (key, v) in DROP or (key, v.replace("...", "")) in DROP:
                continue
            values.extend(SPLIT.get((key, v), (v,)))
        values = [v for v in values if v.isalpha()
                  and (len(v) <= MAX_LETTERS or key in LONG_OK)]
        for k in SPLIT_KEYS.get(key, (key,)):
            add(k, values, "deits")
    for k, vs in ADD.items():
        add(k, vs, "review")
    for k, vs in hand.items():
        if k != "source":
            add(_norm_key(k), [v.upper() for v in vs if v.isalpha()], "hand")

    out = {
        "source": (
            "built by data/lexicon/build_abbreviations.py from abbreviations.hand.json "
            "(hand seed 2026-10-21) and rdeits/CrypticCrosswords.jl corpora/abbreviations.json "
            "(MIT, (c) 2019 Robin Deits; LICENSE-CrypticCrosswords.jl.md), with the reviewed "
            "fixes listed in REVIEW.md; keys lowercased, values uppercased letters"
        ),
        "_origin": {k: "+".join(sorted(origin[k])) for k in sorted(table)},
    }
    out.update({k: sorted(table[k]) for k in sorted(table) if table[k]})
    return out


if __name__ == "__main__":
    (HERE / "abbreviations.json").write_text(
        json.dumps(build(), indent=1, ensure_ascii=False) + "\n")
