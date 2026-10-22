"""Brief 014: close the last slots, paired against the frontier baseline.

Both policies get persistent re-proposal: once the policy has no move left
and spend is under the budget, re-propose the uncommitted slot with the most
known letters, with its full current pattern, escalating k on repeats, then
the Opus `list` prompt with the pattern. Stop when every slot is committed,
the budget is spent, or two passes over the uncommitted slots add no new
candidate. Evaluated on 20 fresh grids from 013's reserve.

    python -m ximenes.last_slots split
    python -m ximenes.last_slots evaluate --policy full|frontier|frontier_calibrated [--n N]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys
import uuid
from collections import Counter
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from .data import format_enumeration
from .e2e import CFG as E2E
from .e2e import FrontierRun, e2e_tables, final_slots, grids, split
from .eval import PARAMS
from .gridsolve import fits, load_grid, pattern_of
from .instruments import SETTINGS, propose_list, propose_pattern
from .policy import GridRun, Tables, _backend, load_tables
from .proposers import parse_list

CFG = PARAMS["last_slots"]


def reserve_split(seed: int = CFG["seed"]) -> list[str]:
    """CFG["eval_grids"] grids from 013's reserve, stratified by publisher
    (largest remainder), disjoint from 013's evaluation and fit grids."""
    reserved = split(grids()[0])["reserved"]
    by_pub: dict[str, list[str]] = {}
    for n in sorted(reserved):
        by_pub.setdefault(n.split("-")[0], []).append(n)
    exact = {k: CFG["eval_grids"] * len(v) / len(reserved) for k, v in sorted(by_pub.items())}
    quota = {k: int(x) for k, x in exact.items()}
    for k in sorted(exact, key=lambda k: (quota[k] - exact[k], k))[
            :CFG["eval_grids"] - sum(quota.values())]:
        quota[k] += 1
    rng = random.Random(seed)
    return sorted(n for k, v in sorted(by_pub.items()) for n in rng.sample(v, quota[k]))


class Persistent:
    """Mixin for GridRun and FrontierRun: the persistent re-proposal loop.
    `add_new` differs: the full solver formalises new candidates; the
    baseline merges them into the proposer's shares."""

    def persist(self, budget: float) -> str:
        g: Any = self
        repeats: Counter[str] = Counter()
        idle_passes = 0
        while True:
            todo = [k for k in g.s if k not in g.commits and g.s[k].votes]
            if not todo:
                return "all_committed"
            letters = {c: g.commits[o][i] for o in g.commits
                       for i, c in enumerate(g.s[o].slot.cells)}
            order = sorted(todo, key=lambda k: (pattern_of(g.s[k].slot, letters).count("?"), k))
            added = 0
            for k in order:
                if g.totals[0] >= budget:
                    return "budget"
                if k in g.commits:
                    continue
                letters = {c: g.commits[o][i] for o in g.commits
                           for i, c in enumerate(g.s[o].slot.cells)}
                pattern = pattern_of(g.s[k].slot, letters)
                answers = self._ask(k, pattern, repeats[k])
                repeats[k] += 1
                added += self.add_new(k, answers, pattern)
                g.s[k].moves += 1
                g.refresh("persist", k)
            idle_passes = 0 if added else idle_passes + 1
            if idle_passes >= CFG["idle_passes"]:
                return "no_new_candidates"

    def _ask(self, k: str, pattern: str, repeat: int) -> list[tuple[str, float]]:
        g: Any = self
        s = g.s[k]
        rp = E2E["proposer"]["repropose"]
        enum = format_enumeration(s.clue.enumeration)
        ks = CFG["ks"]
        if repeat < len(ks):
            samples = propose_pattern(s.clue.text, enum, pattern, ks[repeat], rp["model"],
                                      backend=g.backend, fmt=rp["format"])
            return [(a, sh) for a, sh in g._votes(samples, s.clue, s.slot) if fits(a, pattern)]
        r1 = E2E["proposer"]["round1"]
        listed = parse_list(propose_list(s.clue.text, enum, pattern, r1["model"],
                                         backend=g.backend, fmt=r1["format"]))
        return [(a, sh) for a, sh in g._listed(listed, s.clue, s.slot) if fits(a, pattern)]

    def add_new(self, k: str, answers: list[tuple[str, float]], pattern: str) -> int:
        raise NotImplementedError


class PersistentSolver(Persistent, GridRun):
    def add_new(self, k: str, answers: list[tuple[str, float]], pattern: str) -> int:
        s = self.s[k]
        known = {h["answer"] for h in s.cands}
        new = [(a, sh) for a, sh in answers if a not in known][:PARAMS["candidates"]]
        s.cands += [self._formalise(s, a, sh, len(s.cands) + i) for i, (a, sh) in enumerate(new)]
        s.votes += [(a, sh) for a, sh in new if a not in dict(s.votes)]
        s.solved = True
        return len(new)


class PersistentFrontier(Persistent, FrontierRun):
    def add_new(self, k: str, answers: list[tuple[str, float]], pattern: str) -> int:
        s = self.s[k]
        old = {a: sh for a, sh in s.votes if fits(a, pattern)}
        new = dict(answers)
        merged = {a: (old.get(a, 0.0) + new.get(a, 0.0)) / (1 + 1) for a in {*old, *new}}
        s.votes = sorted(merged.items(), key=lambda kv: (-kv[1], kv[0]))
        return len(set(new) - set(old))


class CalibratedFrontier(PersistentFrontier):
    """fable's third arm: the frontier baseline with priors from 013's fitted
    vote-only posterior and OTHER table (no verifier features, no formaliser,
    no judges): brief 005's vote domain, i.e. the top-m votes."""

    def variables(self) -> dict[str, Any]:
        return GridRun.variables(self)


def evaluate(names: Sequence[str], policy: str, args: argparse.Namespace) -> dict[str, Any]:
    paths = {p.stem: p for p in grids()[0]}
    started = datetime.now(UTC)
    run_id = (f"{started.strftime('%Y%m%dT%H%M%SZ')}-last-slots-{policy}-{args.backend}-"
              f"{uuid.uuid4().hex}")
    runs = pathlib.Path(args.runs_dir)
    log_path = runs / f"{run_id}.jsonl"
    models = {"proposer": SETTINGS["solve_models"]["proposer"],
              "formaliser": SETTINGS["solve_models"]["formaliser"],
              "judge": SETTINGS["judges"]["model"]}
    tables, gain = e2e_tables()

    def one(name: str) -> dict[str, Any]:
        grid, clues = load_grid(paths[name])
        backend, totals, memo = _backend(args, log_path)
        budget = CFG["budget_usd"]
        if policy == "full":
            g: Any = PersistentSolver(name, grid, clues, backend, totals, tables, models,
                                      warm=memo, proposer=E2E["proposer"])
            g.run("voc", gain, gain["rho"]["rho"], budget)
        elif policy == "frontier":
            g = PersistentFrontier(name, grid, clues, backend, totals, load_tables(), models,
                                   proposer=E2E["proposer"])
            g.frontier(budget)
        else:
            vote_only = Tables(tables.vote, tables.vote, tables.other_vote, tables.other_vote)
            g = CalibratedFrontier(name, grid, clues, backend, totals, vote_only, models,
                                   proposer=E2E["proposer"])
            g.frontier(budget)
        stop = g.persist(budget)
        return {"puzzle": name, "checkpoints": g.checkpoints, "usd": g.totals[0],
                "stop": stop, "slots": final_slots(g), "budget": budget,
                "fully_correct": g.checkpoints[-1]["letters_correct"] == 1}

    with ThreadPoolExecutor(max_workers=max(1, min(len(names), E2E["grid_workers"]))) as pool:
        out = list(pool.map(one, names))
    doc = {"run_id": run_id, "policy": policy, "log": str(log_path), "grids": out,
           "params": CFG, "proposer": E2E["proposer"]}
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{run_id}.json").write_text(json.dumps(doc, indent=1))
    return doc


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m ximenes.last_slots")
    p.add_argument("step", choices=("split", "evaluate"))
    p.add_argument("--policy", choices=("full", "frontier", "frontier_calibrated"),
                   default="full")
    p.add_argument("--n", type=int, default=None)
    p.add_argument("--backend", choices=("anthropic", "stub"), default="anthropic")
    p.add_argument("--log", nargs="*", default=[])
    p.add_argument("--offline", action="store_true")
    p.add_argument("--max-usd", type=float, default=CFG["cap_usd"])
    p.add_argument("--runs-dir", default="runs")
    args = p.parse_args(argv)
    names = reserve_split()
    if args.step == "split":
        print(json.dumps({"n": len(names), "by_publisher": dict(Counter(
            n.split("-")[0] for n in names))}))
        return 0
    doc = evaluate(names[:args.n], args.policy, args)
    print(json.dumps({"run_id": doc["run_id"], "usd": [g["usd"] for g in doc["grids"]],
                      "fully_correct": sum(g["fully_correct"] for g in doc["grids"]),
                      "stops": dict(Counter(g["stop"] for g in doc["grids"]))}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
