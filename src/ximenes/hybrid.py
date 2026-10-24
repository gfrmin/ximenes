"""Brief 016: the hybrid. Direct answers, repaired by the grid.

Arm (a), direct: 015's D1 call (`direct-grid-v1`, Opus high), one per grid.
Arm (b), hybrid: the same call's answers as round 1, each with a probability
from a calibration map of D's stated confidence (fitted on 015's 40 dev
grids), OTHER = 1 - that; BP as in 014's frontier_calibrated (commit at
marginal >= tau, nothing clamped by itself); then escalation: the
uncommitted slot with the most known letters gets one Opus-high top-5 call
(015 Stage A arm 2) with its pattern, its candidates entering with 014's
fitted vote posterior; BP again. Stops when every slot is committed, two
passes add nothing, or the budget is spent. Submits the MAP.

    python -m ximenes.hybrid split          # writes nothing; counts
    python -m ximenes.hybrid fit-map        # data/hybrid-d-calibration.json (from 015's D1 run)
    python -m ximenes.hybrid run [--smoke]  # both arms; --smoke = 014's grid #1
    python -m ximenes.hybrid summary
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
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from . import posterior as post
from .bp import OTHER, Var, committed, map_assignment, prior_with_other
from .clue import normalise
from .data import DATA, CryptoniteClue, format_enumeration
from .direct import CFG as DIRECT
from .direct import answers_of, puzzle_text, score_grid
from .eval import PARAMS, ece_of
from .gridsolve import fits, load_grid, pattern_of
from .instruments import Instrument, propose_top, solve_grid
from .policy import GridRun, Tables, _pseudo
from .residual import ARMS, beta_cdf, p_greater

CFG = PARAMS["hybrid"]
MAP_FILE = DATA / "hybrid-d-calibration.json"


# --- the grid split -------------------------------------------------------------------------


def never_read() -> list[str]:
    """012's daily-cryptic grids minus every grid 013, 014 or 015 read."""
    from .e2e import grids, split
    from .last_slots import reserve_split

    keep = grids()[0]
    s = split(keep)
    read = set(s["evaluation"]) | set(s["fit"]) | set(reserve_split())
    return sorted(p.stem for p in keep if p.stem not in read)


def hybrid_split(seed: int = CFG["seed"]) -> list[str]:
    """CFG["grids"] never-read grids stratified by publisher (largest
    remainder, as in 013); all of them if fewer remain."""
    pool = never_read()
    if len(pool) <= CFG["grids"]:
        return pool
    by_pub: dict[str, list[str]] = {}
    for n in pool:
        by_pub.setdefault(n.split("-")[0], []).append(n)
    exact = {k: CFG["grids"] * len(v) / len(pool) for k, v in sorted(by_pub.items())}
    quota = {k: int(x) for k, x in exact.items()}
    for k in sorted(exact, key=lambda k: (quota[k] - exact[k], k))[
            :CFG["grids"] - sum(quota.values())]:
        quota[k] += 1
    rng = random.Random(seed)
    return sorted(n for k, v in sorted(by_pub.items()) for n in rng.sample(v, quota[k]))


# --- the calibration map of D's stated confidence ------------------------------------------


def map_rows(d1_run: Mapping[str, Any]) -> list[tuple[str, dict[str, Any], dict[str, float], bool]]:
    """013's logistic rows from a D1 run: one per slot with a stated
    confidence; slot ids carry the grid so the CV groups by grid."""
    return [(f"{g['puzzle']}|{i}", {}, {"confidence": float(c)}, bool(y))
            for g in d1_run["grids"] if "unfinished" not in g
            for i, (c, y) in enumerate(g["calibration"])]


def fit_map(d1_run: Mapping[str, Any]) -> dict[str, Any]:
    from .e2e import fit_logistic_by_grid

    rows = map_rows(d1_run)
    return {**fit_logistic_by_grid(rows, CFG["map_features"]), "fitted_on": d1_run["run_id"],
            "n_slots": len(rows), "n_grids": len({r[0].split("|")[0] for r in rows})}


def calibrated(m: Mapping[str, Any], confidence: float | None) -> float:
    return post.predict_logistic(dict(m), {"confidence": confidence or 0.0})


# --- arm (b) ---------------------------------------------------------------------------------


class Hybrid(GridRun):
    """Round 1 is D's answers (set before GridRun builds its slots); BP and
    commits are GridRun's; `variables` puts D's calibrated answer beside the
    escalation candidates."""

    def __init__(self, name: str, grid: Any, clues: dict[str, CryptoniteClue],
                 backend: Instrument, totals: list[float], tables: Tables,
                 d_answers: Mapping[str, tuple[str, float | None]], cal: Mapping[str, Any]
                 ) -> None:
        self.d = dict(d_answers)
        self.cal = cal
        self.extra: dict[str, list[tuple[str, float]]] = {}
        models = {"proposer": "", "formaliser": "", "judge": ""}
        super().__init__(name, grid, clues, backend, totals, tables, models)

    def _round1(self, clue: CryptoniteClue, slot: Any) -> list[tuple[str, float]]:
        from .gridsolve import slot_key

        a, c = self.d.get(slot_key(slot), ("", None))
        return [(a, calibrated(self.cal, c))] if len(a) == slot.length else []

    def variables(self) -> dict[str, Var]:
        out = {}
        for k, s in self.s.items():
            if k in self.commits:
                out[k] = committed(self.commits[k])
                continue
            extra = self.extra.get(k, [])
            if not extra:  # round 1 only: D's answer at its calibrated p, OTHER = 1 - p
                out[k] = Var(tuple(a for a, _p in s.votes), (*(p for _a, p in s.votes),
                                                              1 - sum(p for _a, p in s.votes)))
                continue
            pseudo = [_pseudo(a, sh, r) for r, (a, sh) in enumerate(extra)]
            ps = {h["answer"]: post.posterior(self.t.vote, h, pseudo[:i] + pseudo[i + 1:])
                  for i, h in enumerate(pseudo)}
            for a, p in s.votes:
                ps[a] = max(p, ps.get(a, 0.0))
            words = sorted(ps, key=lambda w: -ps[w])
            out[k] = Var(tuple(words), prior_with_other([ps[w] for w in words],
                                                        PARAMS["bp"]["floor_other"]))
        return out

    def escalate(self, budget: float) -> str:
        """014's persistence order, one Opus-high top-5 call per slot visit."""
        arm = ARMS[CFG["escalation_arm"]]
        idle = 0
        while True:
            todo = [k for k in self.s if k not in self.commits]
            if not todo:
                return "all_committed"
            letters = self._letters()
            order = sorted(todo, key=lambda k: (pattern_of(self.s[k].slot, letters).count("?"), k))
            added = 0
            for k in order:
                if self.totals[0] >= budget:
                    return "budget"
                if k in self.commits:
                    continue
                s = self.s[k]
                pattern = pattern_of(s.slot, self._letters())
                out = propose_top(s.clue.text, format_enumeration(s.clue.enumeration), pattern,
                                  arm["n"], arm["model"], arm["effort"], arm["max_tokens"],
                                  backend=self.backend)
                seen: dict[str, float] = {}
                for c in out["candidates"]:
                    a = normalise(str(c.get("answer", "")))
                    if len(a) == s.slot.length and fits(a, pattern) and a not in seen:
                        seen[a] = float(c.get("share") or 0.0)
                old = dict(self.extra.get(k, []))
                merged = {a: max(old.get(a, 0.0), sh) for a, sh in {**old, **seen}.items()}
                new = set(seen) - set(old) - {a for a, _p in s.votes}
                self.extra[k] = sorted(merged.items(), key=lambda kv: (-kv[1], kv[0]))
                added += len(new)
                s.moves += 1
                self.refresh("escalate", k)
            idle = 0 if added else idle + 1
            if idle >= CFG["idle_passes"]:
                return "no_new_candidates"

    def _letters(self) -> dict[tuple[int, int], str]:
        return {c: self.commits[o][i] for o in self.commits
                for i, c in enumerate(self.s[o].slot.cells)}

    def submission(self) -> dict[str, str]:
        vs = self.variables()
        final = map_assignment(vs, self.edges)
        out = {}
        for k, v in vs.items():
            w = final[k]
            if w is OTHER and v.words:
                w = v.words[max(range(len(v.words)), key=lambda i: self.marg[k][i])]
            out[k] = w or ""
        return out


def _tables() -> Tables:
    from .e2e import e2e_tables

    t, _gain = e2e_tables()
    return Tables(t.vote, t.vote, t.other_vote, t.other_vote)


def one_grid(name: str, path: pathlib.Path, backend: Instrument, totals: list[float],
             cal: Mapping[str, Any]) -> dict[str, Any]:
    grid, clues = load_grid(path)
    gold = {k: normalise(c.answer) for k, c in clues.items()}
    cfg = DIRECT["arms"]["D1"]
    clue_lines, grid_lines = puzzle_text(grid, clues)
    out = solve_grid(clue_lines, grid_lines, cfg["model"], cfg["effort"], cfg["max_tokens"],
                     backend=backend)
    d = answers_of(out, grid)
    direct = {**score_grid(d, grid, gold), "usd": totals[0], "stop_reason": out.get("_stop_reason")}
    direct["calibrated"] = [[calibrated(cal, c), y] for c, y in direct["calibration"]]
    g = Hybrid(name, grid, clues, backend, totals, _tables(), d, cal)
    stop = g.escalate(CFG["budget_usd"])
    sub = g.submission()
    hyb = score_grid({k: (w, None) for k, w in sub.items()}, grid, gold)
    d_ans = {k: d.get(k, ("", None))[0] for k in gold}
    overturned = {
        "right_to_wrong": sum(d_ans[k] == gold[k] and sub[k] != gold[k] for k in gold),
        "wrong_to_right": sum(d_ans[k] != gold[k] and sub[k] == gold[k] for k in gold),
        "wrong_to_other_wrong": sum(d_ans[k] != gold[k] and sub[k] not in (gold[k], d_ans[k])
                                    for k in gold)}
    from .e2e import slot_confidences

    readouts = {str(b): _at(g.checkpoints, b) for b in CFG["readouts"]}
    return {"puzzle": name, "direct": direct,
            "hybrid": {**hyb, "usd": totals[0], "stop": stop, "overturned": overturned,
                       "readouts": readouts,
                       "slot_confidences": slot_confidences({"grids": [
                           {"checkpoints": g.checkpoints}]}),
                       "checkpoints": g.checkpoints}}


def _at(checkpoints: Sequence[Mapping[str, Any]], budget: float) -> dict[str, Any]:
    from .policy import score_at

    c = score_at(checkpoints, budget)
    return {"usd": c["usd"], "clues": c["clues_correct"],
            "fully_correct": c["letters_correct"] == 1}


# --- runs and the summary ---------------------------------------------------------------------


def run(names: Sequence[str], args: argparse.Namespace, smoke: bool) -> dict[str, Any]:
    from .e2e import grids
    from .policy import _backend

    paths = {p.stem: p for p in grids()[0]}
    cal = json.loads(MAP_FILE.read_text())
    started = datetime.now(UTC)
    run_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}-hybrid-{args.backend}-{uuid.uuid4().hex}"
    runs = pathlib.Path(args.runs_dir)

    def safe(name: str) -> dict[str, Any]:
        backend, totals, _memo = _backend(args, runs / f"{run_id}.jsonl")  # meter per grid
        try:
            return one_grid(name, paths[name], backend, totals, cal)
        except Exception as e:  # noqa: BLE001 - recorded, never silently dropped
            return {"puzzle": name, "unfinished": f"{type(e).__name__}: {e}"}

    with ThreadPoolExecutor(max_workers=CFG["grid_workers"]) as pool:
        out = list(pool.map(safe, names))
    doc = {"run_id": run_id, "smoke": smoke, "params": CFG, "grids": out}
    (runs / f"{run_id}.json").write_text(json.dumps(doc, indent=1))
    return doc


def p_paired(only_b: int, only_a: int) -> float:
    """P(theta > 1/2) for theta ~ Beta(1 + only_b, 1 + only_a)."""
    return 1 - beta_cdf(1 / (1 + 1), 1 + only_b, 1 + only_a)


def summary(doc: Mapping[str, Any]) -> dict[str, Any]:
    done = [g for g in doc["grids"] if "unfinished" not in g]
    out: dict[str, Any] = {"grids": len(doc["grids"]), "unfinished": len(doc["grids"]) - len(done)}
    for arm in ("direct", "hybrid"):
        gs = [g[arm] for g in done]
        out[arm] = {"fully_correct": sum(g["fully_correct"] for g in gs),
                    "clues": sum(g["clues_right"] for g in gs)
                    / max(1, sum(g["slots"] for g in gs)),
                    "usd_per_grid": sum(g["usd"] for g in gs) / max(1, len(gs)),
                    "conflicts_per_grid": sum(g["conflicts"] for g in gs) / max(1, len(gs))}
    a = {g["puzzle"]: g["direct"]["fully_correct"] for g in done}
    b = {g["puzzle"]: g["hybrid"]["fully_correct"] for g in done}
    only_b, only_a = sum(b[k] and not a[k] for k in a), sum(a[k] and not b[k] for k in a)
    out["paired"] = {"both": sum(a[k] and b[k] for k in a), "only_direct": only_a,
                     "only_hybrid": only_b, "neither": sum(not a[k] and not b[k] for k in a),
                     "p_theta_gt_half": p_paired(only_b, only_a),
                     "p_independent_beta": p_greater(sum(b.values()), len(b),
                                                     sum(a.values()), len(a))}
    for b_ in CFG["readouts"]:
        r = [g["hybrid"]["readouts"][str(b_)] for g in done]
        out[f"hybrid_at_{b_}"] = {"fully_correct": sum(x["fully_correct"] for x in r),
                                  "clues": sum(x["clues"] for x in r) / max(1, len(r))}
    raw = [c for g in done for c in g["direct"]["calibration"]]
    cal = [c for g in done for c in g["direct"]["calibrated"]]
    hyb = [(m, y) for g in done for m, y, _c in g["hybrid"]["slot_confidences"]]
    out["ece"] = {name: ece_of([c for c, _y in xs], [bool(y) for _c, y in xs], PARAMS["bins"])[0]
                  for name, xs in (("direct_stated", raw), ("direct_calibrated", cal),
                                   ("hybrid_marginals", hyb)) if xs}
    out["overturned"] = dict(sum((Counter(g["hybrid"]["overturned"]) for g in done), Counter()))
    out["stops"] = dict(Counter(g["hybrid"]["stop"] for g in done))
    rule = CFG["decision"]
    p = out["paired"]["p_theta_gt_half"]
    out["decision"] = ("hybrid_is_the_solver" if p >= rule["hybrid_wins"] else
                       "direct_is_the_solver" if p <= rule["direct_wins"] else "lead_chooses")
    return out


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m ximenes.hybrid")
    p.add_argument("step", choices=("split", "fit-map", "run", "summary"))
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--run", default=None, help="fit-map: the D1 run JSON; summary: a hybrid run")
    p.add_argument("--backend", choices=("anthropic", "stub"), default="anthropic")
    p.add_argument("--log", nargs="*", default=[])
    p.add_argument("--offline", action="store_true")
    p.add_argument("--max-usd", type=float, default=CFG["cap_usd"])
    p.add_argument("--runs-dir", default="runs")
    args = p.parse_args(argv)
    if args.step == "split":
        names = hybrid_split()
        print(json.dumps({"never_read": len(never_read()), "n": len(names),
                          "by_publisher": dict(Counter(n.split("-")[0] for n in names))}))
        return 0
    if args.step == "fit-map":
        m = fit_map(json.loads(pathlib.Path(args.run or CFG["map_run"]).read_text()))
        MAP_FILE.write_text(json.dumps({"source": "fitted by `python -m ximenes.hybrid fit-map` "
                                        "on brief 015's D1 run over the 40 dev grids "
                                        "(briefs/016), before any 016 grid was read", **m},
                                       indent=1) + "\n")
        print(json.dumps({k: m[k] for k in ("intercept", "coef", "l2", "n_slots", "n_grids")}))
        return 0
    if args.step == "summary":
        print(json.dumps(summary(json.loads(pathlib.Path(args.run).read_text())), indent=1))
        return 0
    from .last_slots import reserve_split

    names = [reserve_split()[0]] if args.smoke else hybrid_split()
    if not args.smoke and names != CFG["grid_list"]:
        raise SystemExit("the seeded split differs from data/eval.json's pinned grid_list")
    doc = run(names, args, args.smoke)
    print(json.dumps({"run_id": doc["run_id"], **({"smoke": [
        {k: g.get(k) for k in ("puzzle", "unfinished")} | (
            {"usd": g["hybrid"]["usd"], "direct_usd": g["direct"]["usd"],
             "stop": g["hybrid"]["stop"]} if "hybrid" in g else {})
        for g in doc["grids"]]} if args.smoke else summary(doc))}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
