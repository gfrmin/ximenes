"""Build data/lexicon/abbreviations.json from its two sources, with reviewed fixes.

    uv run python data/lexicon/build_abbreviations.py

Sources:
  abbreviations.hand.json                          hand seed (origin "hand")
  upstream/CrypticCrosswords.jl-abbreviations.json rdeits/CrypticCrosswords.jl
      corpora/abbreviations.json, MIT (c) 2019 Robin Deits (origin "deits")
  reviewed.json                                    entries reviewed by hand (adds "review")
  ../.src/wikipedia/crossword-abbreviations-<oldid>.wiki  Wikipedia, "Crossword
      abbreviations", revision WIKIPEDIA_OLDID (2026-09-16), CC BY-SA 4.0
      (origin "wikipedia"; brief 009), imported whole

`_origin` is per entry: {key: {VALUE: origin}}. An entry counts as mechanical
only if its origin includes "hand" or "review" (DESIGN D4).

Every change from upstream is listed in REVIEW.md. abbr() is a mechanical
operator, so a bad value here makes an Ok verdict unsound: fixes are explicit
and reviewed, never inferred.
"""

import json
import pathlib

HERE = pathlib.Path(__file__).parent

WIKIPEDIA_OLDID = 1375193762
WIKIPEDIA = HERE.parent / ".src" / "wikipedia" / f"crossword-abbreviations-{WIKIPEDIA_OLDID}.wiki"
WIKIPEDIA_SHA256 = "ba16dc1e423241b09f44501f6e87fcae14cb987b365beb025c8cca99eaa5cb69"


def parse_wikipedia(text: str) -> dict[str, set[str]]:
    """Entries under the A-Z headings: "* Key – <small>V</small> or <small>W</small> ...".
    Keys split on " or ", "," and "/"; values are the letter-only <small> contents."""
    import re

    out: dict[str, set[str]] = {}
    in_list = False
    for line in text.splitlines():
        if line.startswith("=="):
            in_list = bool(re.fullmatch(r"==\s*[A-Z]\s*==", line.strip()))
            continue
        if not in_list or not line.startswith("*"):
            continue
        body = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", line.lstrip("* "))
        parts = re.split(r"\s+[–—-]\s+", body, maxsplit=1)
        if len(parts) < 2:
            continue
        key, rest = parts
        values = {v.upper() for v in re.findall(r"<small>\s*([^<]+?)\s*</small>", rest)
                  if re.fullmatch(r"[A-Za-z]+", v.strip())}
        for k in re.split(r"\s*(?:,|/|\bor\b)\s*", key.replace("''", "")):
            k = re.sub(r"[^a-z' ]", "", k.lower()).strip()
            if k and values:
                out.setdefault(k, set()).update(values)
    return out


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
    reviewed = json.loads((HERE / "reviewed.json").read_text())["abbreviations"]
    origin: dict[str, dict[str, set[str]]] = {}

    def add(key: str, values: list[str] | tuple[str, ...], src: str) -> None:
        for v in values:
            origin.setdefault(key, {}).setdefault(v, set()).add(src)

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
    import hashlib

    if hashlib.sha256(WIKIPEDIA.read_bytes()).hexdigest() != WIKIPEDIA_SHA256:
        raise ValueError(f"{WIKIPEDIA} does not match its pinned hash (run ./setup.sh)")
    for k, vs in parse_wikipedia(WIKIPEDIA.read_text(encoding="utf-8")).items():
        add(_norm_key(k), sorted(v for v in vs if len(v) <= MAX_LETTERS), "wikipedia")
    for k, vs in ADD.items():
        add(k, vs, "review")
    for k, vs in hand.items():
        if k != "source":
            add(_norm_key(k), [v.upper() for v in vs if v.isalpha()], "hand")

    for key, value in reviewed:
        if value not in origin.get(key, {}):
            raise ValueError(f"reviewed abbreviation {key}->{value} is not in any source")
        add(key, (value,), "review")

    # brief 010: share-alike stays in its own file. The main table holds every
    # origin except "wikipedia"; the Wikipedia file holds the Wikipedia entries
    # (and "review" for the ones only it lists). Loading merges by union.
    main_origin: dict[str, dict[str, set[str]]] = {}
    wiki_origin: dict[str, dict[str, set[str]]] = {}
    for k, d in origin.items():
        for v, o in d.items():
            rest = o - {"wikipedia"}
            if rest:
                main_origin.setdefault(k, {})[v] = rest
            if "wikipedia" in o:
                extra = {"review"} if "review" in o and not (rest - {"review"}) else set()
                wiki_origin.setdefault(k, {})[v] = {"wikipedia"} | extra
                if extra and main_origin.get(k, {}).get(v) == {"review"}:
                    del main_origin[k][v]
    wiki = {
        "source": (f"Wikipedia contributors, \"Crossword abbreviations\", revision "
                   f"{WIKIPEDIA_OLDID} (2026-09-16), https://en.wikipedia.org/w/index.php?oldid="
                   f"{WIKIPEDIA_OLDID}; parsed by data/lexicon/build_abbreviations.py "
                   "(values over 4 letters dropped; reviewed entries per REVIEW.md)"),
        "license": "CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/); this file "
                   "is an adaptation and carries the same licence",
        "_origin": {k: {v: "+".join(sorted(o)) for v, o in sorted(d.items())}
                    for k, d in sorted(wiki_origin.items()) if d},
    }
    wiki.update({k: sorted(d) for k, d in sorted(wiki_origin.items()) if d})
    origin = {k: d for k, d in main_origin.items() if d}

    out = {
        "source": (
            "built by data/lexicon/build_abbreviations.py from abbreviations.hand.json "
            "(hand seed 2026-10-21) and rdeits/CrypticCrosswords.jl corpora/abbreviations.json "
            "(MIT, (c) 2019 Robin Deits; LICENSE-CrypticCrosswords.jl.md), with the reviewed "
            "fixes listed in REVIEW.md. Keys lowercased, values uppercased letters. Wikipedia's "
            "entries (CC BY-SA 4.0) are in abbreviations.wikipedia.json, merged at load time"
        ),
        "_origin": {k: {v: "+".join(sorted(o)) for v, o in sorted(d.items())}
                    for k, d in sorted(origin.items()) if d},
    }
    out.update({k: sorted(d) for k, d in sorted(origin.items()) if d})
    return out, wiki


if __name__ == "__main__":
    main, wiki = build()
    (HERE / "abbreviations.json").write_text(json.dumps(main, indent=1, ensure_ascii=False) + "\n")
    (HERE / "abbreviations.wikipedia.json").write_text(
        json.dumps(wiki, indent=1, ensure_ascii=False) + "\n")
