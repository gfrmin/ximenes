"""Brief 017: harder puzzles. Opus asked directly (015's D1, unchanged) on
post-cutoff Times dailies (Times for the Times) and Telegraph Toughies (Big
Dave's), harvested under 012's protocol.

    python -m ximenes.hard split              # counts per publisher
    python -m ximenes.hard run --smoke        # one grid per publisher
    python -m ximenes.hard run                # the pinned list (paid)
    python -m ximenes.hard summary --run runs/<run>.json
    python -m ximenes.hard hybrid --log runs/<direct run>.jsonl   # arm (b), lead's ee33af0
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys
import uuid
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from .direct import run as run_direct
from .eval import PARAMS, ece_of
from .residual import beta_interval

CFG = PARAMS["hard"]


def paths() -> dict[str, pathlib.Path]:
    from .e2e import grids

    return {p.stem: p for p in grids(publishers=CFG["publishers"])[0]}


def hard_split(seed: int = CFG["seed"]) -> list[str]:
    """Up to CFG["per_publisher"] grids per publisher, sampled by the seed."""
    by_pub: dict[str, list[str]] = {}
    for n in sorted(paths()):
        by_pub.setdefault(n.split("-")[0], []).append(n)
    rng = random.Random(seed)
    return sorted(n for k in CFG["publishers"] for n in
                  rng.sample(by_pub.get(k, []), min(CFG["per_publisher"], len(by_pub.get(k, [])))))


def smoke_names(seed: int = CFG["smoke_seed"]) -> list[str]:
    """One grid per publisher, from outside the pinned list where one is
    left; else the publisher's first pinned grid (its result is never
    printed, and the run replays the same call)."""
    pinned = set(CFG["grid_list"])
    rng = random.Random(seed)
    out = []
    for k in CFG["publishers"]:
        rest = sorted(n for n in paths() if n.startswith(k + "-") and n not in pinned)
        mine = sorted(n for n in pinned if n.startswith(k + "-"))
        if rest or mine:
            out.append(rng.choice(rest) if rest else mine[0])
    return out


def _arm(gs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    done = [g for g in gs if "unfinished" not in g]
    fc = sum(g["fully_correct"] for g in done)
    cal = [c for g in done for c in g["calibration"]]
    return {"grids": len(gs), "unfinished": len(gs) - len(done), "fully_correct": fc,
            "interval": beta_interval(fc, len(done)),
            "clues": sum(g["clues_right"] for g in done) / max(1, sum(g["slots"] for g in done)),
            "conflicts_per_grid": sum(g["conflicts"] for g in done) / max(1, len(done)),
            "ece": ece_of([c for c, _y in cal], [bool(y) for _c, y in cal], PARAMS["bins"])[0]
            if cal else None,
            "wrong_slots_per_imperfect_grid": sorted(g["slots"] - g["clues_right"]
                                                     for g in done if not g["fully_correct"]),
            "wrong_with_stated_ge_high": sum(c >= CFG["high_confidence"] and not y
                                             for g in done for c, y in g["calibration"]),
            "stop_reasons": dict(Counter(str(g.get("stop_reason")) for g in done))}


def summary(doc: Mapping[str, Any]) -> dict[str, Any]:
    gs = doc["grids"]
    out = {"pooled": _arm(gs), "usd": doc["usd"], "usd_per_grid": doc["usd"] / max(1, len(gs)),
           "by_publisher": {k: _arm([g for g in gs if g["puzzle"].startswith(k + "-")])
                            for k in CFG["publishers"]}}
    lo, hi = out["pooled"]["interval"]
    rule = CFG["decision"]
    out["decision"] = ("direct_holds" if lo >= rule["holds_lower"] else
                       "direct_falls_off" if hi < rule["falls_upper"] else "no_claim")
    return out


def main(argv: Sequence[str] | None = None) -> int:
    from .policy import _backend

    p = argparse.ArgumentParser(prog="python -m ximenes.hard")
    p.add_argument("step", choices=("split", "run", "summary", "hybrid"))
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--run", default=None)
    p.add_argument("--n", type=int, default=None, help="per publisher, if the smoke says cut")
    p.add_argument("--backend", choices=("anthropic", "stub"), default="anthropic")
    p.add_argument("--log", nargs="*", default=[])
    p.add_argument("--offline", action="store_true")
    p.add_argument("--max-usd", type=float, default=CFG["cap_usd"])
    p.add_argument("--runs-dir", default="runs")
    args = p.parse_args(argv)
    if args.step == "split":
        names = hard_split()
        print(json.dumps({"available": dict(Counter(n.split("-")[0] for n in paths())),
                          "n": len(names), "by_publisher": dict(Counter(
                              n.split("-")[0] for n in names))}))
        return 0
    if args.step == "summary":
        print(json.dumps(summary(json.loads(pathlib.Path(args.run).read_text())), indent=1))
        return 0
    if args.step == "hybrid":  # arm (b): 016's hybrid unchanged, the direct calls replayed
        from . import hybrid

        names = hard_split()
        if names != CFG["grid_list"]:
            raise SystemExit("the seeded split differs from data/eval.json's pinned grid_list")
        doc = hybrid.run(names, args, False, paths())
        print(json.dumps({"run_id": doc["run_id"], **hybrid.summary(doc),
                          "by_publisher": {k: hybrid.summary(
                              {"grids": [g for g in doc["grids"]
                                         if g["puzzle"].startswith(k + "-")]})
                              for k in CFG["publishers"]}}, indent=1))
        return 0
    if args.smoke:
        names = smoke_names()
    else:
        names = hard_split()
        if names != CFG["grid_list"]:
            raise SystemExit("the seeded split differs from data/eval.json's pinned grid_list")
        if args.n is not None:
            names = [n for k in CFG["publishers"]
                     for n in [m for m in names if m.startswith(k + "-")][:args.n]]
    runs = pathlib.Path(args.runs_dir)
    started = datetime.now(UTC)
    run_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}-hard-{args.backend}-{uuid.uuid4().hex}"
    backend, totals, _memo = _backend(args, runs / f"{run_id}.jsonl")
    out = run_direct("D1", [("017", n) for n in names], backend, paths())
    doc = {"run_id": run_id, "smoke": args.smoke, "usd": totals[0], "grids": out}
    (runs / f"{run_id}.json").write_text(json.dumps(doc, indent=1))
    if args.smoke:  # cost only: the smoke grids are outside the pinned list
        print(json.dumps({"run_id": run_id, "usd": totals[0], "grids": len(out),
                          "unfinished": sum("unfinished" in g for g in out)}))
    else:
        print(json.dumps({"run_id": run_id, **summary(doc)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
