"""Brief 010 appendix: gold-in-k from logged vote samples, $0.

For each clue, the distinct enumeration-valid answers in its k samples,
ranked by vote count (ties by first appearance, as the solvers rank them).
gold-in-k is the share of clues whose gold answer is among the top k; it is
what raising the number of formalised candidates m could buy at most.

    python -m ximenes.recall --clues test runs/<002 solve>.json \
        --clues val runs/<003 val solve>.json --grids 004 runs/grids 20 <log>... [...]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter
from collections.abc import Sequence

from .clue import Clue, normalise
from .data import format_enumeration, load_cryptonite
from .eval import PARAMS
from .gridsolve import load_grid
from .instruments import (
    SETTINGS,
    Instrument,
    memoized,
    metered,
    propose_answers,
    replay_then,
    stub_backend,
)
from .policy import GridRun, load_tables


def ranked(samples: Sequence[str], clue: Clue) -> list[str]:
    """Distinct valid answers by vote count, ties by first appearance."""
    answers = [a for a in map(normalise, samples) if a and clue.enumeration.matches(a)]
    counts = Counter(answers)
    first = {a: i for i, a in reversed(list(enumerate(answers)))}
    return sorted(counts, key=lambda a: (-counts[a], first[a]))


def curve(ranks: Sequence[int | None], k_max: int) -> list[float]:
    """gold-in-k for k = 1..k_max; a rank is 0-based, None if gold is absent."""
    return [sum(r is not None and r < k for r in ranks) / len(ranks)
            for k in range(1, k_max + 1)]


def rank_of(answers: Sequence[str], gold: str) -> int | None:
    return answers.index(gold) if gold in answers else None


def _replay(logs: Sequence[str]) -> Instrument:
    backend: Instrument = stub_backend(pathlib.Path(logs[0]), on_conflict="first")
    for extra in logs[1:]:
        backend = replay_then(pathlib.Path(extra), backend, on_conflict="first")
    return backend


def clue_ranks(run_json: str) -> list[int | None]:
    run = json.loads(pathlib.Path(run_json).read_text())
    population = load_cryptonite(run["set"])
    backend = _replay([run["log"], *(run["replayed_from"] or [])])
    out = []
    for i in run["indices"]:
        c = population[i]
        samples = propose_answers(c.text, format_enumeration(c.enumeration), PARAMS["k"],
                                  run["models"]["proposer"], backend=backend)
        out.append(rank_of(ranked(samples, Clue(c.text, c.enumeration, c.orientation)),
                           normalise(c.answer)))
    return out


def grid_ranks(d: str, n: int, logs: Sequence[str]) -> list[int | None]:
    gdir = pathlib.Path(d)
    summary = json.loads((gdir / "_summary.json").read_text())
    names = [r["puzzle"] for r in summary["puzzles"] if r["outcome"] == "unique"
             and r["clues"] >= PARAMS["grid"]["min_clues"]][:n]
    models = {"proposer": SETTINGS["solve_models"]["proposer"],
              "formaliser": SETTINGS["solve_models"]["formaliser"],
              "judge": SETTINGS["judges"]["model"]}
    replay, tables = _replay(logs), load_tables()
    out = []
    for name in names:
        grid, clues = load_grid(gdir / f"{name}.json")
        backend, totals = metered(memoized(replay))
        run = GridRun(name, grid, clues, backend, totals, tables, models)
        out += [rank_of([a for a, _sh in s.votes], run.gold[k]) for k, s in run.s.items()]
    return out


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m ximenes.recall")
    p.add_argument("--clues", nargs="+", action="append", default=[], metavar=("NAME", "RUN"))
    p.add_argument("--grids", nargs="+", action="append", default=[],
                   metavar=("NAME DIR N", "LOG"))
    p.add_argument("--out", default="runs/010-recall.json")
    args = p.parse_args(argv)
    sets = {name: clue_ranks(run) for name, run in args.clues}
    for name, d, n, *logs in args.grids:
        sets[f"grids {name}"] = grid_ranks(d, int(n), logs)
    sets["grids all"] = [r for k, v in sets.items() if k.startswith("grids ") for r in v]
    out = {k: {"n": len(v), "gold_in_k": curve(v, PARAMS["k"])} for k, v in sets.items()}
    pathlib.Path(args.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
