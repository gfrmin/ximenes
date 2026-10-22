"""Brief 011: recall by proposer.

For each proposer x prompt x pattern level, on a fresh stratified sample of
Cryptonite test clues: gold-in-k, $ per clue, enumeration and pattern
failures, refusals, output tokens; a year-of-clue probe; and the
pre-registered pick for brief 012 with its early-stop verdict. Nothing is
formalised or verified.

    python -m ximenes.proposers --n 10            # smoke test (10 clues per cell)
    python -m ximenes.proposers                   # full run (n from data/eval.json)
    python -m ximenes.proposers --backend stub --log runs/<run>.jsonl   # replay
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import re
import sys
import threading
import uuid
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from .clue import Clue, normalise
from .data import CryptoniteClue, format_enumeration, load_cryptonite
from .eval import PARAMS, sample_indices
from .gridsolve import fits
from .instruments import (
    Cost,
    Instrument,
    Json,
    anthropic_backend,
    budgeted,
    logged,
    propose_answers,
    propose_list,
    propose_pattern,
    stub_backend,
)
from .recall import curve, rank_of, ranked

CFG = PARAMS["recall"]
PROMPT_KINDS = ("sample", "list")
PATTERNS = ("none", "half")

_NUMBERING = re.compile(r"^\s*(?:\d+\s*[.):]|[-*•])\s*")
_TRAILER = re.compile(r"\s*(?:\(|\s-\s|\s—\s|:).*$")


# --- pure pieces ------------------------------------------------------------------------


def sample_clues(population: Sequence[CryptoniteClue]) -> tuple[int, ...]:
    """CFG["n"] test indices, excluding brief 000's sample, stratified by
    publisher in proportion to the eligible pool (largest remainder)."""
    excluded = set(sample_indices(len(population), CFG["exclude_n"], CFG["exclude_seed"]))
    pools: dict[str, list[int]] = {}
    for i, c in enumerate(population):
        if i not in excluded:
            pools.setdefault(c.publisher, []).append(i)
    total = sum(len(v) for v in pools.values())
    exact = {p: CFG["n"] * len(v) / total for p, v in sorted(pools.items())}
    quota = {p: int(x) for p, x in exact.items()}
    for p in sorted(exact, key=lambda p: (quota[p] - exact[p], p))[:CFG["n"] - sum(
            quota.values())]:
        quota[p] += 1
    rng = random.Random(CFG["seed"])
    return tuple(sorted(i for p in sorted(pools) for i in rng.sample(pools[p], quota[p])))


def half_pattern(answer: str, index: int) -> str:
    """Alternate letters revealed from a seeded offset, never more than half
    (odd lengths start at the second letter)."""
    n = len(answer)
    offset = random.Random(f"{CFG['seed']}:{index}").randrange(1 + 1) if n % (1 + 1) == 0 else 1
    return "".join(ch if i % (1 + 1) == offset else "?" for i, ch in enumerate(answer))


def parse_list(text: str) -> list[str]:
    """One candidate per line: numbering, bullets and trailing glosses
    stripped, normalised, de-duplicated in order (no length check here)."""
    out: list[str] = []
    for line in text.splitlines():
        a = normalise(_TRAILER.sub("", _NUMBERING.sub("", line)))
        if a and a not in out:
            out.append(a)
    return out


def candidates(raw: Sequence[str], kind: str, clue: Clue, pattern: str | None
               ) -> tuple[list[str], int, int]:
    """(ranked valid candidates, raw answers failing the enumeration, valid
    ones failing the pattern). `sample` ranks by vote; `list` keeps order."""
    answers = [a for a in map(normalise, raw) if a]
    enum_fail = sum(not clue.enumeration.matches(a) for a in answers)
    ranked_all = ranked(raw, clue) if kind == "sample" else [
        a for a in answers if clue.enumeration.matches(a)]
    keep = [a for a in ranked_all if pattern is None or fits(a, pattern)]
    return keep, enum_fail, len(ranked_all) - len(keep)


def pick(cells: Mapping[str, Mapping[str, Any]], pattern: str) -> str | None:
    """Max gold-in-pick_k among cells at `pattern` within the price bar; ties
    within the tie margin go to the cheaper cell."""
    ok = {c: v for c, v in cells.items() if v["pattern"] == pattern
          and v["usd_per_clue"] <= CFG["max_usd_per_clue"]}
    if not ok:
        return None
    best = max(v["gold_in"][str(CFG["pick_k"])] for v in ok.values())
    near = [c for c, v in ok.items() if v["gold_in"][str(CFG["pick_k"])] >= best - CFG["tie"]]
    return min(near, key=lambda c: (ok[c]["usd_per_clue"], c))


def bootstrap(hits: Sequence[bool], rng: random.Random) -> tuple[float, float]:
    n = len(hits)
    means = sorted(sum(rng.choice(hits) for _ in range(n)) / n
                   for _ in range(CFG["bootstrap_reps"]))
    tail = (1 - CFG["interval"]) / (1 + 1)
    return means[int(tail * len(means))], means[min(len(means) - 1,
                                                    int((1 - tail) * len(means)))]


def year_bin(year: int) -> str:
    starts = CFG["year_bins"]
    lo = max((s for s in starts if s <= year), default=starts[0])
    nxt = [s for s in starts if s > lo]
    return f"{lo}-{(nxt[0] - 1) if nxt else 'on'}"


# --- the run ----------------------------------------------------------------------------


def cell_name(model: str, kind: str, pattern: str) -> str:
    return f"{model}|{kind}|{pattern}"


def recording(backend: Instrument, sink: list[tuple[str, Cost]]) -> Instrument:
    """Pass calls through, keeping each call's cost under its cell name."""
    lock = threading.Lock()

    def call(instrument: str, model: str, inp: Mapping[str, Json]) -> tuple[Json, Cost]:
        output, cost = backend(instrument, model, inp)
        kind = "list" if instrument == "propose_list" else "sample"
        with lock:
            sink.append((cell_name(model, kind, "half" if "pattern" in inp else "none"), cost))
        return output, cost

    return call


def one(c: CryptoniteClue, index: int, model: str, kind: str, pattern: str,
        backend: Instrument) -> dict[str, Any]:
    clue = Clue(c.text, c.enumeration, c.orientation)
    gold = normalise(c.answer)
    pat = half_pattern(gold, index) if pattern == "half" else None
    enum = format_enumeration(c.enumeration)
    if kind == "list":
        raw = parse_list(propose_list(c.text, enum, pat, model, backend=backend))
    elif pat is None:
        raw = propose_answers(c.text, enum, CFG["k"][model], model, backend=backend)
    else:
        raw = propose_pattern(c.text, enum, pat, CFG["k"][model], model, backend=backend)
    cands, enum_fail, pattern_fail = candidates(raw, kind, clue, pat)
    return {"index": index, "rank": rank_of(cands, gold), "n_raw": len(raw),
            "enum_fail": enum_fail, "pattern_fail": pattern_fail, "n_cands": len(cands)}


def summarise(rows: Mapping[str, list[dict[str, Any]]], costs: Sequence[tuple[str, Cost]],
              years: Mapping[int, int], publishers: Mapping[int, str]) -> dict[str, Any]:
    cells: dict[str, Any] = {}
    for name, rs in rows.items():
        model, kind, pattern = name.split("|")
        cs = [c for n, c in costs if n == name]
        messages = sum(CFG["k"][model] if kind == "sample" else 1 for _ in cs)
        ranks = [r["rank"] for r in rs]
        cells[name] = {
            "model": model, "prompt": kind, "pattern": pattern, "n": len(rs),
            "gold_in": {**{str(k): curve(ranks, k)[-1] for k in CFG["ks"]},
                        "all": sum(r is not None for r in ranks) / len(ranks)},
            "curve": curve(ranks, max(CFG["k"].values())),
            "usd_per_clue": sum(c.get("usd") or 0.0 for c in cs) / len(rs),
            "enum_fail_share": sum(r["enum_fail"] for r in rs) / max(1, sum(r["n_raw"]
                                                                           for r in rs)),
            "pattern_fail_share": sum(r["pattern_fail"] for r in rs) / max(1, sum(
                r["pattern_fail"] + r["n_cands"] for r in rs)),
            "refusals": sum(c.get("refusals") or 0 for c in cs),
            "output_tokens_per_message": sum(c.get("output_tokens") or 0 for c in cs)
            / max(1, messages),
            "top1_by_year": {b: _share([r["rank"] == 0 for r in rs
                                        if year_bin(years[r["index"]]) == b])
                             for b in sorted({year_bin(y) for y in years.values()})},
            "top1_by_publisher": {p: _share([r["rank"] == 0 for r in rs
                                             if publishers[r["index"]] == p])
                                  for p in sorted(set(publishers.values()))},
        }
    rng = random.Random(CFG["bootstrap_seed"])
    picks: dict[str, Any] = {}
    for pattern in PATTERNS:
        p = pick(cells, pattern)
        if p is None:
            picks[pattern] = None
            continue
        hits = [r["rank"] is not None and r["rank"] < CFG["pick_k"] for r in rows[p]]
        lo, hi = bootstrap(hits, rng)
        picks[pattern] = {"cell": p, "gold_in_pick_k": cells[p]["gold_in"][str(CFG["pick_k"])],
                          "interval": [lo, hi]}
    half = picks.get("half")
    verdict = None
    if half:
        g, (lo, hi) = half["gold_in_pick_k"], half["interval"]
        verdict = ("ambiguous" if lo < CFG["threshold"] <= hi else
                   "full" if g >= CFG["threshold"] else "three_grids")
    return {"cells": cells, "picks": picks, "early_stop": verdict}


def _share(xs: Sequence[bool]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def run(clues: Mapping[int, CryptoniteClue], backend: Instrument) -> dict[str, Any]:
    costs: list[tuple[str, Cost]] = []
    rec = recording(backend, costs)
    tasks = [(i, m, kind, pat) for m in CFG["proposers"] for kind in PROMPT_KINDS
             for pat in PATTERNS for i in clues]
    with ThreadPoolExecutor(max_workers=PARAMS["workers"]) as pool:
        out = list(pool.map(lambda t: (cell_name(*t[1:]), one(clues[t[0]], t[0], *t[1:], rec)),
                            tasks))
    rows: dict[str, list[dict[str, Any]]] = {}
    for name, r in out:
        rows.setdefault(name, []).append(r)
    return summarise(rows, costs, {i: c.date.year for i, c in clues.items()},
                     {i: c.publisher for i, c in clues.items()})


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m ximenes.proposers")
    p.add_argument("--n", type=int, default=None, help="first n of the sample (smoke test)")
    p.add_argument("--backend", choices=("anthropic", "stub"), default="anthropic")
    p.add_argument("--log", default=None, help="stub: the run log to replay")
    p.add_argument("--max-usd", type=float, default=CFG["cap_usd"])
    p.add_argument("--runs-dir", default="runs")
    args = p.parse_args(argv)
    population = load_cryptonite("test")
    indices = sample_clues(population)[:args.n]
    started = datetime.now(UTC)
    run_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}-proposers-{args.backend}-{uuid.uuid4().hex}"
    runs = pathlib.Path(args.runs_dir)
    log_path = runs / f"{run_id}.jsonl"
    base: Instrument = (stub_backend(pathlib.Path(args.log)) if args.backend == "stub"
                        else budgeted(anthropic_backend(), args.max_usd))
    result = run({i: population[i] for i in indices}, logged(base, log_path))
    out = {"run_id": run_id, "run_date": started.date().isoformat(), "n": len(indices),
           "indices": list(indices), "replayed_from": args.log, "log": str(log_path),
           "spend_usd": sum(v["usd_per_clue"] * v["n"] for v in result["cells"].values()),
           **result}
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{run_id}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({"run_id": run_id, "spend_usd": out["spend_usd"], "picks": out["picks"],
                      "early_stop": out["early_stop"],
                      "cells": {k: {"gold_in": v["gold_in"], "usd_per_clue": v["usd_per_clue"]}
                                for k, v in out["cells"].items()}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
