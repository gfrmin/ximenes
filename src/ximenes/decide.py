"""Brief 003: the decision layer. Acts as life-agent defines them, with the
game's scoring: a point answer, a set of answers, or abstention, at a stated
threshold τ (never tuned; the report shows the curve over a fixed grid).

    python -m ximenes.decide fit --val runs/<val-solve>.json
    python -m ximenes.decide evaluate --test runs/<test-solve>.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections.abc import Sequence
from typing import Any

from .eval import PARAMS, _bin_json, ece_of, risk_coverage
from .posterior import TABLES, fit, load, posterior

TAUS: list[float] = PARAMS["posterior"]["taus"]


def act(posteriors: Sequence[float], tau: float) -> dict[str, Any]:
    """Pure: given the candidates' posteriors (any order), return
    point (the top candidate, if P >= tau), set (the shortest prefix by P with
    mass >= tau), or abstain (no prefix reaches tau)."""
    order = sorted(range(len(posteriors)), key=lambda i: -posteriors[i])
    mass = 0.0
    for size, i in enumerate(order, start=1):
        mass += posteriors[i]
        if mass >= tau:
            return {"act": "point" if size == 1 else "set", "members": order[:size],
                    "mass": mass}
    return {"act": "abstain", "members": [], "mass": mass}


def scored_items(run: dict[str, Any], model: dict[str, Any]) -> list[dict[str, Any]]:
    """Per clue: candidates' posteriors, the top candidate, and correctness."""
    out = []
    for item in run["items"]:
        cands = item["candidates"]
        ps = [posterior(model, h, cands[:i] + cands[i + 1:]) for i, h in enumerate(cands)]
        correct = [h["answer"] == item["answer"] for h in cands]
        top = max(range(len(ps)), key=lambda i: ps[i]) if ps else None
        out.append({"slot": item["slot"], "posteriors": ps, "correct": correct,
                    "top_p": ps[top] if top is not None else 0.0,
                    "top_correct": correct[top] if top is not None else False,
                    "vote_top_share": item["vote_top_share"],
                    "vote_correct": item["vote_top"] == item["answer"],
                    "rule002_verified": item["verified_lenient"],
                    "rule002_correct": item["correct"]})
    return out


def tau_table(items: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    n = len(items)
    for tau in TAUS:
        acts = [act(x["posteriors"], tau) for x in items]
        point = [(a, x) for a, x in zip(acts, items, strict=True) if a["act"] == "point"]
        sets = [(a, x) for a, x in zip(acts, items, strict=True) if a["act"] == "set"]
        rows.append({
            "tau": tau,
            "point_coverage": len(point) / n,
            "point_accuracy": sum(x["correct"][a["members"][0]] for a, x in point) / len(point)
            if point else None,
            "set_rate": len(sets) / n,
            "set_mean_size": sum(len(a["members"]) for a, _ in sets) / len(sets) if sets else None,
            "set_truth_inside": sum(any(x["correct"][i] for i in a["members"]) for a, x in sets)
            / len(sets) if sets else None,
            "abstain_rate": sum(a["act"] == "abstain" for a in acts) / n,
        })
    return rows


def evaluate(run: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    items = scored_items(run, model)
    n_bins = PARAMS["bins"]
    ece, bins = ece_of([x["top_p"] for x in items], [x["top_correct"] for x in items], n_bins)
    rc = risk_coverage([x["top_p"] for x in items], [x["top_correct"] for x in items])
    rc_vote = risk_coverage([x["vote_top_share"] for x in items],
                            [x["vote_correct"] for x in items])
    v002 = [x for x in items if x["rule002_verified"]]
    return {
        "model": model["model"], "n": len(items), "ece": ece,
        "bins": [_bin_json(b) for b in bins],
        "risk_coverage": rc, "risk_coverage_vote": rc_vote,
        "rule002_point": {"coverage": len(v002) / len(items),
                          "accuracy": sum(x["rule002_correct"] for x in v002) / len(v002)},
        "taus": tau_table(items),
    }


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m ximenes.decide")
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit", help="fit both posteriors on a val solve run; commit the tables")
    f.add_argument("--val", required=True)
    e = sub.add_parser("evaluate", help="score a (test) solve run with the committed tables")
    e.add_argument("--test", required=True)
    e.add_argument("--out", default=None)
    args = p.parse_args(argv)
    if args.cmd == "fit":
        run = json.loads(pathlib.Path(args.val).read_text())
        models = fit(run["set"], run)
        for which, model in models.items():
            source = (f"fitted by `python -m ximenes.decide fit` on val solve run {run['run_id']} "
                      "(briefs/003-calibration.md); never on test")
            pathlib.Path(TABLES[which]).write_text(
                json.dumps({"source": source, **model}, indent=1) + "\n")
        print(json.dumps({k: m["cv_log_loss"] for k, m in models.items()}["binned"]))
        return 0
    run = json.loads(pathlib.Path(args.test).read_text())
    out = {which: evaluate(run, load(which)) for which in TABLES}
    out["chosen"] = load("binned")["chosen"]
    text = json.dumps(out, indent=1)
    if args.out:
        pathlib.Path(args.out).write_text(text + "\n")
    print(json.dumps({k: {"ece": v["ece"], "tau_0.9": [t for t in v["taus"] if t["tau"] == PARAMS[
        "posterior"]["headline_tau"]]} for k, v in out.items() if k != "chosen"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
