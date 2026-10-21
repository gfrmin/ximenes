"""Build data/lexicon/indicators.json from its sources, with per-entry origins.

    uv run python data/lexicon/build_indicators.py

Sources:
  indicators.hand.json                          hand lists (origin "hand")
  upstream/CrypticCrosswords.jl-indicators/*    rdeits/CrypticCrosswords.jl
      corpora/indicators, MIT (c) 2019 Robin Deits (origin "deits")
  reviewed.json                                 entries reviewed by hand (adds "review")

An entry counts as mechanical only if its origin includes "hand" or "review"
(DESIGN D4); a step on any other entry is Quarantine(table_unreviewed).
"""

import json
import pathlib

HERE = pathlib.Path(__file__).parent
UPSTREAM = HERE / "upstream" / "CrypticCrosswords.jl-indicators"
# Deits file -> operators it indicates. InitialSubstring / FinalSubstring mean
# "keep an initial / final part", which covers both the deletions and the
# first/last-letter selections.
MAP = {
    "Anagram": ("anagram",),
    "Reversal": ("reverse",),
    "InsertAB": ("insert",),
    "InsertBA": ("insert",),
    "Initials": ("initials", "first_letters"),
    "InitialSubstring": ("delete_last", "first_letters"),
    "FinalSubstring": ("delete_first", "last_letters"),
    "sub_": ("hidden", "alternate", "delete_middle", "middle_letters"),
}


def build() -> dict:
    hand = json.loads((HERE / "indicators.hand.json").read_text())
    reviewed = json.loads((HERE / "reviewed.json").read_text())["indicators"]
    origin: dict[str, dict[str, set[str]]] = {}

    def add(op: str, phrase: str, src: str) -> None:
        origin.setdefault(op, {}).setdefault(phrase.replace("_", " ").lower().strip(), set()).add(src)

    for fname, ops in MAP.items():
        for line in (UPSTREAM / fname).read_text().splitlines():
            if line.strip():
                for op in ops:
                    add(op, line, "deits")
    for op, phrases in hand.items():
        if op != "source":
            for phrase in phrases:
                add(op, phrase, "hand")
    for op, phrase in reviewed:
        if phrase not in origin.get(op, {}):
            raise ValueError(f"reviewed indicator {op}:{phrase!r} is not in any source")
        add(op, phrase, "review")
    out = {
        "source": (
            "built by data/lexicon/build_indicators.py from indicators.hand.json, "
            "rdeits/CrypticCrosswords.jl corpora/indicators (MIT, (c) 2019 Robin Deits; "
            "LICENSE-CrypticCrosswords.jl.md) and reviewed.json; see REVIEW.md"
        ),
        "_origin": {op: {p: "+".join(sorted(o)) for p, o in sorted(d.items())}
                    for op, d in sorted(origin.items())},
    }
    out.update({op: sorted(d) for op, d in sorted(origin.items())})
    return out


if __name__ == "__main__":
    (HERE / "indicators.json").write_text(json.dumps(build(), indent=1, ensure_ascii=False) + "\n")
