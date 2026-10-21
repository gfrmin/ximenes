"""Brief 000 diagnostics: Haiku headline accuracy by clue year, publisher,
quick vs cryptic, and enumeration shape. Reads the local run summary in runs/
(not committed) and the Cryptonite test split; prints numbers only.

    uv run python reports/000/breakdown.py runs/<run-id>.json
"""

import json
import sys
from collections import defaultdict
from fractions import Fraction
from math import sqrt

from ximenes.data import load_cryptonite
from ximenes.eval import Vote, ece


def main(path: str) -> None:
    run = json.load(open(path))
    test = load_cryptonite("test")
    rows = [(test[i], it) for i, it in zip(run["indices"], run["items"], strict=True)]
    assert all(c.answer == it["answer"] for c, it in rows)
    groupings = {
        "clue year": lambda c: f"{c.date.year // 5 * 5}–{c.date.year // 5 * 5 + 4}",
        "publisher": lambda c: c.publisher,
        "type": lambda c: "quick" if c.is_quick else "cryptic",
        "enumeration": lambda c: "multi-word" if len(c.enumeration.parts) > 1 else "single word",
    }
    for name, key in groupings.items():
        groups = defaultdict(list)
        for c, it in rows:
            groups[key(c)].append(it)
        print(f"| {name} | n | top-1 (±95%) | mean conf | ECE |")
        for g in sorted(groups):
            its = groups[g]
            n = len(its)
            p = sum(i["correct"] for i in its) / n
            votes = [Vote(i["prediction"], Fraction(i["confidence"]).limit_denominator(run["k"]),
                          i["correct"]) for i in its]
            conf = sum(i["confidence"] for i in its) / n
            half = 1.96 * sqrt(p * (1 - p) / n)
            print(f"| {g} | {n} | {p:.3f} ± {half:.3f} | {conf:.3f} | "
                  f"{float(ece(votes, run['n_bins'])):.3f} |")
        print()


if __name__ == "__main__":
    main(sys.argv[1])
