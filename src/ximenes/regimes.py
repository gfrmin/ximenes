"""Brief 010: does hard commitment cost grids? Offline, $0.

Each logged grid's round-1 state is rebuilt by replaying its run's log: every
slot's proposals, and the formalised candidates of every slot the run solved
(a slot whose solve calls are not in the log keeps its vote candidates, as
brief 005's policies do before solving). No re-proposal, so the candidate
sets are fixed; then the three BP regimes of `ximenes.bp` (hard, soft,
soft-annealed) decode the same priors, and each is scored per grid.

    python -m ximenes.regimes --set 004 runs/grids 20 runs/<log>.jsonl [...] \
        --set 005 runs/grids-eval 10 runs/<log>.jsonl --set 006 ...
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from .bp import Edge, Var, hard, soft, soft_annealed, with_floor
from .eval import PARAMS
from .gridsolve import load_grid, slot_key
from .instruments import (
    SETTINGS,
    Instrument,
    MissingFromLog,
    memoized,
    metered,
    replay_then,
    stub_backend,
)
from .policy import GridRun, Tables, domain, load_tables

CFG = PARAMS["regimes"]
REGIMES = ("hard", "soft", "annealed")


def round1(run: GridRun, t: Tables) -> tuple[dict[str, tuple[tuple[str, ...], tuple[float, ...]]],
                                              dict[str, bool]]:
    """Each slot's (words, prior) after round 1, and whether it was solved:
    solved if every solve call is in the log, else its vote candidates."""
    priors, solved = {}, {}
    for k, s in run.s.items():
        try:
            if s.votes:
                run.apply("solve", k)
            solved[k] = s.solved
        except MissingFromLog:
            s.cands, s.formalised, s.solved = [], 0, False
            solved[k] = False
        words, prior = domain(s, t)
        priors[k] = (tuple(words), tuple(prior))
    return priors, solved


def decode_all(priors: Mapping[str, tuple[tuple[str, ...], tuple[float, ...]]],
               edges: Sequence[Edge]) -> tuple[dict[str, dict[str, str | None]], frozenset[str]]:
    """The three regimes' submissions, and the slots hard clamps."""
    vs = {k: Var(w, with_floor(p, CFG["floor"])) for k, (w, p) in priors.items()}
    h, clamped = hard(vs, edges, CFG["tau"])
    return {"hard": h, "soft": soft(vs, edges),
            "annealed": soft_annealed(priors, edges, CFG["annealed_floors"])}, clamped


def score(sub: Mapping[str, str | None], gold: Mapping[str, str],
          cells: Mapping[str, Sequence[tuple[int, int]]]) -> dict[str, Any]:
    """Clues right, letters right (a cell counts when every slot through it
    enters the gold letter), fully correct."""
    entered: dict[tuple[int, int], set[str]] = {}
    gold_cell: dict[tuple[int, int], str] = {}
    for k, cs in cells.items():
        for i, c in enumerate(cs):
            gold_cell[c] = gold[k][i]
            entered.setdefault(c, set()).add(sub[k][i] if sub[k] else "")
    letters = sum(v == {gold_cell[c]} for c, v in entered.items())
    clues = sum(sub[k] == gold[k] for k in gold)
    return {"clues": clues / len(gold), "letters": letters / len(gold_cell),
            "fully_correct": letters == len(gold_cell)}


def grid_result(priors: Mapping[str, tuple[tuple[str, ...], tuple[float, ...]]],
                solved: Mapping[str, bool], edges: Sequence[Edge], gold: Mapping[str, str],
                cells: Mapping[str, Sequence[tuple[int, int]]]) -> dict[str, Any]:
    subs, clamped = decode_all(priors, edges)
    return {
        "scores": {r: score(subs[r], gold, cells) for r in REGIMES},
        "slots": {k: {"solved": solved[k], "clamped": k in clamped, "gold_in": gold[k] in w,
                      **{r: subs[r][k] == gold[k] for r in REGIMES}}
                  for k, (w, _p) in priors.items()},
    }


def paired_interval(diffs: Sequence[float], rng: random.Random) -> tuple[float, float, float]:
    """Mean of per-grid differences and its percentile bootstrap interval."""
    n = len(diffs)
    means = sorted(sum(rng.choice(diffs) for _ in range(n)) / n
                   for _ in range(CFG["bootstrap_reps"]))
    tail = (1 - CFG["interval"]) / (1 + 1)
    lo = means[int(tail * len(means))]
    hi = means[min(len(means) - 1, int((1 - tail) * len(means)))]
    return sum(diffs) / n, lo, hi


def summarise(grids: Sequence[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(CFG["bootstrap_seed"])

    def mean(r: str, m: str) -> float:
        return sum(float(g["scores"][r][m]) for g in grids) / len(grids)

    out: dict[str, Any] = {"n_grids": len(grids),
                           "regimes": {r: {m: mean(r, m) for m in ("clues", "letters")}
                                       | {"fully_correct": sum(g["scores"][r]["fully_correct"]
                                                               for g in grids)}
                                       for r in REGIMES}}
    out["paired"] = {f"{r}-hard": {m: paired_interval(
        [g["scores"][r][m] - g["scores"]["hard"][m] for g in grids], rng)
        for m in ("clues", "letters")} for r in REGIMES if r != "hard"}
    return out


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m ximenes.regimes")
    p.add_argument("--set", nargs="+", action="append", required=True,
                   metavar=("NAME DIR N", "LOG"))
    p.add_argument("--out", default="runs/010-regimes.json")
    args = p.parse_args(argv)
    tables = load_tables()
    models = {"proposer": SETTINGS["solve_models"]["proposer"],
              "formaliser": SETTINGS["solve_models"]["formaliser"],
              "judge": SETTINGS["judges"]["model"]}
    grids = []
    for name, d, n, *logs in args.set:
        replay: Instrument = stub_backend(pathlib.Path(logs[0]), on_conflict="first")
        for extra in logs[1:]:
            replay = replay_then(pathlib.Path(extra), replay, on_conflict="first")
        gdir = pathlib.Path(d)
        summary = json.loads((gdir / "_summary.json").read_text())
        names = [r["puzzle"] for r in summary["puzzles"] if r["outcome"] == "unique"
                 and r["clues"] >= PARAMS["grid"]["min_clues"]][:int(n)]
        for puzzle in names:
            grid, clues = load_grid(gdir / f"{puzzle}.json")
            backend, totals = metered(memoized(replay))
            run = GridRun(puzzle, grid, clues, backend, totals, tables, models)
            priors, solved = round1(run, tables)
            cells = {slot_key(s): s.cells for s in grid.slots}
            grids.append({"set": name, "puzzle": puzzle,
                          **grid_result(priors, solved, run.edges, run.gold, cells)})
            print(name, puzzle, {r: grids[-1]["scores"][r]["clues"] for r in REGIMES},
                  file=sys.stderr)
    by = {"all": grids, **{f"set {s}": [g for g in grids if g["set"] == s]
                           for s in dict.fromkeys(g["set"] for g in grids)},
          **{f"publisher {pub}": [g for g in grids if g["puzzle"].split("-")[0] == pub]
             for pub in dict.fromkeys(g["puzzle"].split("-")[0] for g in grids)}}
    out = {"run_date": datetime.now(UTC).date().isoformat(), "sets": args.set,
           "summary": {k: summarise(v) for k, v in by.items()}, "grids": grids}
    pathlib.Path(args.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out["summary"]["all"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
