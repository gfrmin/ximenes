"""Brief 013: the end-to-end grid solver on post-cutoff grids.

Split (D7 as amended): brief 012's unique daily-cryptic grids, after the
row invariants, are split by one seed into evaluation grids (stratified by
publisher), fit grids, and the rest reserved. Fit grids only refit the slot
posterior, the OTHER tables and the gain model for 011's proposer; those
tables are committed before any evaluation grid is read.

    python -m ximenes.e2e split                 # counts only
    python -m ximenes.e2e fit [--n N]           # fit policy on the fit grids (paid)
    python -m ximenes.e2e refit --run runs/<fit run>.json   # writes data/e2e-*.json
    python -m ximenes.e2e evaluate [--n N]      # VOC at the budget on evaluation grids (paid)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import re
import sys
import uuid
from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from . import posterior as post
from .bp import Var, committed, prior_with_other
from .clue import normalise
from .data import DATA, format_enumeration, split_clue
from .eval import PARAMS, postcutoff_grids
from .gridsolve import fits, load_grid, pattern_of
from .instruments import SETTINGS, propose_pattern
from .policy import GridRun, Tables, _backend, load_tables
from .voc import fit_gain, fit_other_prior, preregister_rho

CFG = PARAMS["e2e"]
MODEL = CFG["proposer"]["repropose"]["model"]
TABLE_FILES = {"full": DATA / "e2e-posterior.json", "vote": DATA / "e2e-posterior-vote.json",
               "other": DATA / "e2e-other-prior.json",
               "other_vote": DATA / "e2e-other-prior-vote.json",
               "gain": DATA / "e2e-gain-model.json"}
_MARKER = re.compile(r"\b\d+\s*(?:a|d|ac|dn|across|down)\b", re.IGNORECASE)
_INNER_ENUM = re.compile(r"\(\s*\d+(?:\s*[,\-]\s*\d+)*\s*\)")


class FitOnEvaluation(ValueError):
    """The e2e tables are fitted on fit grids only (D7)."""


# --- data -------------------------------------------------------------------------------


def row_ok(row: Mapping[str, Any]) -> bool:
    """fable's parser invariants (QUESTIONS § 012): the clue ends with an
    enumeration whose length is the answer's, has at least two words, holds
    no second enumeration (a clue cut at an inner bracket) and no other
    clue's number-and-direction marker (a merge)."""
    try:
        text, enum = split_clue(row["clue"])
    except ValueError:
        return False
    return (enum.length == len(normalise(row["answer"])) and len(text.split()) > 1
            and not _INNER_ENUM.search(text) and not _MARKER.search(text))


def grids(model: str = MODEL) -> tuple[list[pathlib.Path], Counter[str]]:
    """Daily-cryptic grids whose every row passes the invariants, and the
    count of dropped grids by publisher."""
    keep, dropped = [], Counter()
    for f in postcutoff_grids(allow_postcutoff=True, model=model):
        pub = f.name.split("-")[0]
        if pub not in CFG["publishers"]:
            continue
        rows = json.loads(f.read_text())["clues"]
        if all(row_ok(r) for r in rows):
            keep.append(f)
        else:
            dropped[pub] += 1
    return keep, dropped


def split(paths: Sequence[pathlib.Path], seed: int = CFG["split_seed"]) -> dict[str, list[str]]:
    """Evaluation grids stratified by publisher (largest remainder), then fit
    grids from the rest, the remainder reserved. Deterministic in the seed."""
    rng = random.Random(seed)
    by_pub: dict[str, list[str]] = {}
    for p in sorted(paths):
        by_pub.setdefault(p.name.split("-")[0], []).append(p.stem)
    total = sum(len(v) for v in by_pub.values())
    exact = {k: CFG["eval_grids"] * len(v) / total for k, v in sorted(by_pub.items())}
    quota = {k: int(x) for k, x in exact.items()}
    for k in sorted(exact, key=lambda k: (quota[k] - exact[k], k))[
            :CFG["eval_grids"] - sum(quota.values())]:
        quota[k] += 1
    shuffled = {k: rng.sample(v, len(v)) for k, v in sorted(by_pub.items())}
    evaluation = sorted(n for k, v in shuffled.items() for n in v[:quota[k]])
    rest = sorted(n for k, v in shuffled.items() for n in v[quota[k]:])
    fit = sorted(rng.sample(rest, min(CFG["fit_grids"], len(rest))))
    return {"evaluation": evaluation, "fit": fit,
            "reserved": sorted(set(rest) - set(fit))}


# --- refits -----------------------------------------------------------------------------


def items(run: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Solve-run-shaped items from a grid run: one per solved slot, its
    candidates and gold; slot ids carry the grid so folds group by grid."""
    return [it for g in run["grids"] for it in g["items"]]


def _grid_of(slot: str) -> str:
    return slot.split("|")[0]


def fit_logistic_by_grid(data: Sequence[tuple[str, dict[str, Any], dict[str, float], bool]],
                         features: Sequence[str]) -> dict[str, Any]:
    """003's logistic with L2 chosen by leave-one-grid-out log-loss."""
    grid_ids = sorted({_grid_of(d[0]) for d in data})

    def cv(l2: float) -> float:
        ps, ys = [], []
        for g in grid_ids:
            train = [d for d in data if _grid_of(d[0]) != g]
            test = [d for d in data if _grid_of(d[0]) == g]
            m = post.fit_logistic(train, l2, features)
            ps += [post.predict_logistic(m, f) for _s, _h, f, _y in test]
            ys += [y for *_r, y in test]
        return post.log_loss(ps, ys)

    scores = {l2: cv(l2) for l2 in post.P["l2_grid"]}
    l2 = min(scores, key=lambda k: scores[k])
    return {**post.fit_logistic(data, l2, features), "cv_log_loss": scores[l2],
            "cv_by_l2": {str(k): v for k, v in scores.items()}, "cv": "leave one grid out"}


def refit(run: Mapping[str, Any], evaluation: Sequence[str]) -> dict[str, dict[str, Any]]:
    """All five e2e tables from a fit run; refuses a run touching an
    evaluation grid."""
    names = {g["puzzle"] for g in run["grids"]}
    if names & set(evaluation):
        both = sorted(names & set(evaluation))
        raise FitOnEvaluation(f"fit run includes evaluation grids: {both}")
    its = items(run)
    solve_run = {"run_id": run["run_id"], "set": "e2e-fit", "items": its}
    data = post.rows(solve_run)
    full = fit_logistic_by_grid(data, post.FEATURES)
    vote = fit_logistic_by_grid(data, post.VOTE_FEATURES)
    events = [e for g in run["grids"] for e in g["events"]]
    gain = fit_gain(events, CFG["split_seed"])
    gain["rho"] = preregister_rho(events, gain, {g["puzzle"]: g["proposal_usd"]
                                                 for g in run["grids"]}, CFG["target_spend"])
    meta = {"fitted_on": run["run_id"], "fit_grids": sorted(names), "n_slots": len(its)}
    return {"full": {**full, **meta}, "vote": {**vote, **meta},
            "other": {**fit_other_prior(solve_run, full), **meta},
            "other_vote": {**fit_other_prior(solve_run, vote), **meta},
            "gain": {**gain, **meta}}


def e2e_tables() -> tuple[Tables, dict[str, Any]]:
    t = {k: json.loads(v.read_text()) for k, v in TABLE_FILES.items()}
    return Tables(t["full"], t["vote"], t["other"], t["other_vote"]), t["gain"]


# --- the frontier-only baseline (brief 013 item 5) ------------------------------------------


class FrontierRun(GridRun):
    """Opus proposes every slot and re-proposes with crossing letters; BP over
    the proposer's own shares (OTHER at brief 004's floor) commits at tau.
    No formaliser, no judges, no fitted posterior."""

    def variables(self) -> dict[str, Var]:
        out = {}
        for k, s in self.s.items():
            if k in self.commits:
                out[k] = committed(self.commits[k])
            else:
                words = tuple(a for a, _sh in s.votes)
                out[k] = Var(words, prior_with_other([sh for _a, sh in s.votes],
                                                     PARAMS["bp"]["floor_other"]))
        return out

    def frontier(self, budget: float) -> None:
        """Re-propose uncommitted slots whose letter pattern has grown, most
        committed crossers first, until no such slot is left or the spend
        reaches the budget."""
        rp = CFG["proposer"]["repropose"]
        while self.totals[0] < budget:
            letters = {c: self.commits[o][i] for o in self.commits
                       for i, c in enumerate(self.s[o].slot.cells)}
            todo = sorted((k for k, s in self.s.items() if k not in self.commits
                           and pattern_of(s.slot, letters).count("?")
                           < s.seen_pattern.count("?")),
                          key=lambda k: (-sum(o in self.commits for o in self.crossers[k]), k))
            if not todo:
                return
            k = todo[0]
            s = self.s[k]
            pattern = pattern_of(s.slot, letters)
            s.seen_pattern = pattern
            samples = propose_pattern(s.clue.text, format_enumeration(s.clue.enumeration),
                                      pattern, rp["k"], rp["model"], backend=self.backend,
                                      fmt=rp["format"])
            new = dict(self._votes(samples, s.clue, s.slot))
            old = {a: sh for a, sh in s.votes if fits(a, pattern)}
            merged = {a: (old.get(a, 0.0) + new.get(a, 0.0)) / (1 + 1) for a in {*old, *new}}
            s.votes = sorted(merged.items(), key=lambda kv: (-kv[1], kv[0]))
            s.moves += 1
            self.refresh("repropose", k)


def run_frontier(names: Sequence[str], budgets: Mapping[str, float],
                 args: argparse.Namespace) -> dict[str, Any]:
    paths = {p.stem: p for p in grids()[0]}
    started = datetime.now(UTC)
    run_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}-e2e-frontier-{args.backend}-{uuid.uuid4().hex}"
    runs = pathlib.Path(args.runs_dir)
    log_path = runs / f"{run_id}.jsonl"
    models = {"proposer": SETTINGS["solve_models"]["proposer"],
              "formaliser": SETTINGS["solve_models"]["formaliser"],
              "judge": SETTINGS["judges"]["model"]}

    def one(name: str) -> dict[str, Any]:
        grid, clues = load_grid(paths[name])
        backend, totals, _memo = _backend(args, log_path)
        g = FrontierRun(name, grid, clues, backend, totals, load_tables(), models,
                        proposer=CFG["proposer"])
        g.frontier(budgets[name])
        return {"puzzle": name, "checkpoints": g.checkpoints, "usd": g.totals[0],
                "budget": budgets[name], "slots": final_slots(g),
                "fully_correct": g.checkpoints[-1]["letters_correct"] == 1}

    with ThreadPoolExecutor(max_workers=max(1, min(len(names), CFG["grid_workers"]))) as pool:
        out = list(pool.map(one, names))
    doc = {"run_id": run_id, "policy": "frontier", "log": str(log_path), "grids": out,
           "proposer": CFG["proposer"]}
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{run_id}.json").write_text(json.dumps(doc, indent=1))
    return doc


# --- free ablations from the evaluation logs (brief 013 item 4) ---------------------------


def _cells_score(sub: Mapping[str, str | None], g: GridRun) -> dict[str, Any]:
    from .regimes import score

    cells = {k: s.slot.cells for k, s in g.s.items()}
    return score(sub, g.gold, cells)


def ablate(ev: Mapping[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    """Rebuild each evaluation grid's final state by replaying its moves from
    the log (no new calls), then score (a) the proposer's first candidate per
    slot, no verifier and no BP; (b) BP over the same final candidates with
    the vote-only posterior (no verifier features); (c) the full solver."""
    from .bp import OTHER, map_assignment

    paths = {p.stem: p for p in grids()[0]}
    tables, gain = e2e_tables()
    vote_only = Tables(tables.vote, tables.vote, tables.other_vote, tables.other_vote)
    models = {"proposer": SETTINGS["solve_models"]["proposer"],
              "formaliser": SETTINGS["solve_models"]["formaliser"],
              "judge": SETTINGS["judges"]["model"]}
    out = []
    for gdoc in ev["grids"]:
        grid, clues = load_grid(paths[gdoc["puzzle"]])
        backend, totals, memo = _backend(args, pathlib.Path(args.runs_dir) / "ablate.jsonl")
        g = GridRun(gdoc["puzzle"], grid, clues, backend, totals, tables, models, warm=memo,
                    proposer=CFG["proposer"])
        moves = [(c["move"], c["slot"]) for c in gdoc["checkpoints"]
                 if c["move"] in ("solve", "formalise_more", "repropose")]
        g.run("replay_moves", moves=moves)
        first = {k: (s.votes[0][0] if s.votes else None) for k, s in g.s.items()}
        g.t, g.commits = vote_only, {}
        g.refresh("ablate", None)
        vs = g.variables()
        final = map_assignment(vs, g.edges)
        bp = {k: (final[k] if final[k] is not OTHER else
                  (v.words[max(range(len(v.words)), key=lambda i: g.marg[k][i])]
                   if v.words else None)) for k, v in vs.items()}
        full = {k: v["submitted"] for k, v in gdoc["slots"].items()}
        out.append({"puzzle": gdoc["puzzle"], "first": _cells_score(first, g),
                    "bp_vote_only": _cells_score(bp, g), "full": _cells_score(full, g)})
    return {"grids": out}


# --- runs -------------------------------------------------------------------------------


def slot_items(g: GridRun) -> list[dict[str, Any]]:
    return [{"slot": f"{g.name}|{k}", "answer": g.gold[k], "candidates": s.cands}
            for k, s in g.s.items() if s.solved]


def final_slots(g: GridRun) -> dict[str, dict[str, Any]]:
    """Per slot: what would be submitted, committed?, status, right?, and
    whether every crosser is committed (for D9's classes)."""
    from .bp import OTHER, map_assignment

    vs = g.variables()
    final = map_assignment(vs, g.edges)
    out = {}
    for k, v in vs.items():
        w = final[k]
        if w is OTHER and v.words:
            w = v.words[max(range(len(v.words)), key=lambda i: g.marg[k][i])]
        h = next((h for h in g.s[k].cands if h["answer"] == w), None)
        committed = k in g.commits
        status = h["status"] if h else "none"
        right = w == g.gold[k]
        crossers = all(o in g.commits for o in g.crossers[k])
        cls = ("proven" if committed and status == "Ok" and crossers else
               "quarantined" if committed else "guessed")
        out[k] = {"submitted": w, "right": right, "committed": committed, "status": status,
                  "class": cls}
    return out


def run_grids(names: Sequence[str], policy: str, args: argparse.Namespace,
              tables: Tables, gain: dict[str, Any] | None) -> dict[str, Any]:
    paths = {p.stem: p for p in grids()[0]}
    started = datetime.now(UTC)
    run_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}-e2e-{policy}-{args.backend}-{uuid.uuid4().hex}"
    runs = pathlib.Path(args.runs_dir)
    log_path = runs / f"{run_id}.jsonl"
    models = {"proposer": SETTINGS["solve_models"]["proposer"],
              "formaliser": SETTINGS["solve_models"]["formaliser"],
              "judge": SETTINGS["judges"]["model"]}
    def one(name: str) -> dict[str, Any]:
        grid, clues = load_grid(paths[name])
        backend, totals, memo = _backend(args, log_path)  # fresh meter, memo and cap per grid
        g = GridRun(name, grid, clues, backend, totals, tables, models, warm=memo,
                    proposer=CFG["proposer"])
        g.run(policy, gain, gain["rho"]["rho"] if gain else 0.0,
              CFG["budget_usd"] if policy == "voc" else float("inf"))
        print(json.dumps({"grid": name, "usd": g.totals[0],
                          "clues": g.checkpoints[-1]["clues_correct"]}), file=sys.stderr)
        return {"puzzle": name, "checkpoints": g.checkpoints, "events": g.events,
                "proposal_usd": g.checkpoints[0]["usd"], "items": slot_items(g),
                "slots": final_slots(g), "usd": g.totals[0],
                "fully_correct": g.checkpoints[-1]["letters_correct"] == 1}

    # grids are independent: run them side by side (each grid's moves stay in order)
    with ThreadPoolExecutor(max_workers=max(1, min(len(names), CFG["grid_workers"]))) as pool:
        out = list(pool.map(one, names))
    doc = {"run_id": run_id, "policy": policy, "log": str(log_path), "grids": out,
           "proposer": CFG["proposer"], "budget_usd": CFG["budget_usd"]}
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{run_id}.json").write_text(json.dumps(doc, indent=1))
    return doc


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m ximenes.e2e")
    p.add_argument("step", choices=("split", "fit", "refit", "evaluate", "frontier",
                                         "ablate"))
    p.add_argument("--n", type=int, default=None, help="first n grids of the set")
    p.add_argument("--run", default=None,
                   help="refit: the fit run JSON; frontier: the evaluation run (spend to match)")
    p.add_argument("--backend", choices=("anthropic", "stub"), default="anthropic")
    p.add_argument("--log", nargs="*", default=[])
    p.add_argument("--offline", action="store_true")
    p.add_argument("--max-usd", type=float, default=CFG["cap_usd"])
    p.add_argument("--runs-dir", default="runs")
    args = p.parse_args(argv)
    keep, dropped = grids()
    sets = split(keep)
    if args.step == "split":
        print(json.dumps({"kept": len(keep), "dropped_by_invariants": dict(dropped),
                          **{k: len(v) for k, v in sets.items()},
                          "evaluation_by_publisher": dict(Counter(
                              n.split("-")[0] for n in sets["evaluation"]))}))
    elif args.step == "fit":
        doc = run_grids(sets["fit"][:args.n], "fit", args, load_tables(), None)
        print(json.dumps({"run_id": doc["run_id"], "usd": sum(g["usd"] for g in doc["grids"])}))
    elif args.step == "refit":
        tables = refit(json.loads(pathlib.Path(args.run).read_text()), sets["evaluation"])
        for k, t in tables.items():
            TABLE_FILES[k].write_text(json.dumps(
                {"source": f"fitted by `python -m ximenes.e2e refit` on brief 013's fit grids "
                           f"(run {t['fitted_on']}); never on evaluation grids", **t},
                indent=1) + "\n")
    elif args.step == "ablate":
        res = ablate(json.loads(pathlib.Path(args.run).read_text()), args)
        out_path = pathlib.Path(args.runs_dir) / "013-ablations.json"
        out_path.write_text(json.dumps(res, indent=1))
        mean = {m: {k: sum(g[m][k] for g in res["grids"]) / len(res["grids"])
                    for k in ("clues", "letters")} for m in ("first", "bp_vote_only", "full")}
        print(json.dumps(mean))
    elif args.step == "frontier":
        ev = json.loads(pathlib.Path(args.run).read_text())
        spend = sorted(g["usd"] for g in ev["grids"])
        median = (spend[(len(spend) - 1) >> 1] + spend[len(spend) >> 1]) / (1 + 1)
        names = [g["puzzle"] for g in ev["grids"]]
        doc = run_frontier(names, dict.fromkeys(names, median), args)
        print(json.dumps({"run_id": doc["run_id"], "median_matched": median,
                          "usd": [g["usd"] for g in doc["grids"]],
                          "fully_correct": sum(g["fully_correct"] for g in doc["grids"])}))
    else:
        tables, gain = e2e_tables()
        doc = run_grids(sets["evaluation"][:args.n], "voc", args, tables, gain)
        print(json.dumps({"run_id": doc["run_id"], "grids": len(doc["grids"]),
                          "usd": [g["usd"] for g in doc["grids"]],
                          "fully_correct": sum(g["fully_correct"] for g in doc["grids"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
