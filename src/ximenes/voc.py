"""Brief 005: the slot prior (OTHER from val), move prices, the gain model, and
the value-of-computation chooser. Pure functions over recorded state; the
loop that runs them is in gridsolve.
"""

from __future__ import annotations

import json
import pathlib
from collections.abc import Sequence
from typing import Any

from .data import DATA
from .eval import PARAMS
from .posterior import BANDS, FitOnTest, _solve, band, posterior

OTHER_PRIOR = DATA / "other-prior.json"


# --- 1. OTHER from val ------------------------------------------------------------------


def fit_other_prior(run: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    """P(gold outside the candidates | band of the top posterior), from a val
    solve run. Refuses test (D7)."""
    if run.get("set") == "test":
        raise FitOnTest("the OTHER prior is fitted on val only")
    counts = {b: [0, 0] for b in range(len(BANDS))}  # band -> [n, outside]
    for item in run["items"]:
        cands = item["candidates"]
        ps = [posterior(model, h, cands[:i] + cands[i + 1:]) for i, h in enumerate(cands)]
        b = band(max(ps)) if ps else 0
        counts[b][0] += 1
        counts[b][1] += int(not any(h["answer"] == item["answer"] for h in cands))
    rows: list[dict[str, Any]] = []
    for b, (n, out) in sorted(counts.items()):
        # an empty band inherits the band below it (no evidence either way);
        # the lowest band, if empty, is all OTHER
        p = out / n if n else (rows[-1]["p_other"] if rows else 1.0)
        rows.append({"band": b, "lo": BANDS[b], "n": n, "outside": out,
                     "p_other": p, "p_inside": 1 - p})
    return {"fitted_on": run["run_id"], "model": model["model"], "bands": BANDS, "rows": rows}


def load_other_prior() -> dict[str, Any]:
    return json.loads(pathlib.Path(OTHER_PRIOR).read_text())


def slot_prior(posteriors: Sequence[float], table: dict[str, Any]) -> tuple[float, ...]:
    """Candidates share 1 - P(OTHER | band of max posterior) in proportion to
    their posteriors; OTHER takes the rest. No candidates: all OTHER."""
    if not posteriors:
        return (1.0,)
    p_other = table["rows"][band(max(posteriors))]["p_other"]
    total = sum(posteriors)
    share = [(p / total if total else 1.0 / len(posteriors)) * (1 - p_other) for p in posteriors]
    return (*share, p_other)


# --- 2-3. moves, features, the gain model ------------------------------------------------

VOC = PARAMS["voc"]
MOVE_FEATURES = {
    # before formalising, only what the votes and the grid say (fable, 0aa84b7)
    "solve": ("top_vote_share", "vote_margin", "length", "committed_crossers",
              "pattern_density", "round"),
    "formalise_more": ("max_marginal", "other_mass", "committed_crossers", "pattern_density",
                       "round", "n_candidates"),
    "repropose": ("max_marginal", "other_mass", "committed_crossers", "pattern_density",
                  "round", "n_candidates"),
}
GAIN_MODEL = DATA / "gain-model.json"


class FitOnEvaluation(ValueError):
    """The gain model is fitted on fit-seed grids only (D7)."""


def _ridge(xs: list[list[float]], ys: list[float], l2: float) -> list[float]:
    zs = [[1.0, *row] for row in xs]
    n = len(zs[0])
    a = [[sum(z[i] * z[j] for z in zs) + (l2 if i == j and i else 0.0) for j in range(n)]
         for i in range(n)]
    b = [sum(z[i] * y for z, y in zip(zs, ys, strict=True)) for i in range(n)]
    return _solve(a, b)


def _predict(w: Sequence[float], x: Sequence[float]) -> float:
    return w[0] + sum(a * b for a, b in zip(w[1:], x, strict=True))


def fit_gain(events: Sequence[dict[str, Any]], seed: int) -> dict[str, Any]:
    """Per move kind: ridge regression of Δ(max marginal) on the kind's
    pre-registered features (L2 by CV grouped by grid), and the mean price."""
    if seed == VOC["eval_seed"]:
        raise FitOnEvaluation("the gain model is fitted on fit-seed grids only")
    out: dict[str, Any] = {"fit_seed": seed, "kinds": {}}
    for kind, feats in MOVE_FEATURES.items():
        ev = [e for e in events if e["kind"] == kind]
        if not ev:
            continue
        grids = sorted({e["grid"] for e in ev})

        def cv(l2: float, ev: list[dict[str, Any]] = ev, feats: tuple[str, ...] = feats,
               grids: list[str] = grids) -> float:
            err = 0.0
            for g in grids:
                train = [e for e in ev if e["grid"] != g]
                test = [e for e in ev if e["grid"] == g]
                if not train:
                    return float("inf")
                w = _ridge([[e["features"][f] for f in feats] for e in train],
                           [e["delta"] for e in train], l2)
                residuals = [_predict(w, [e["features"][f] for f in feats]) - e["delta"]
                             for e in test]
                err += sum(r * r for r in residuals)
            return err / len(ev)

        scores = {l2: cv(l2) for l2 in VOC["ridge_grid"]}
        l2 = min(scores, key=lambda k: scores[k])
        w = _ridge([[e["features"][f] for f in feats] for e in ev], [e["delta"] for e in ev], l2)
        out["kinds"][kind] = {
            "features": list(feats), "l2": l2, "weights": w, "n": len(ev),
            "cv_mse": scores[l2], "mean_delta": sum(e["delta"] for e in ev) / len(ev),
            "price_usd": sum(e["usd"] for e in ev) / len(ev),
            "price_seconds": sum(e["seconds"] for e in ev) / len(ev),
        }
    return out


def predicted_gain(model: dict[str, Any], kind: str, features: dict[str, float]) -> float:
    k = model["kinds"][kind]
    return _predict(k["weights"], [features[f] for f in k["features"]])


# --- 4. the chooser (pure) ---------------------------------------------------------------


def choose(moves: Sequence[tuple[str, str, dict[str, float]]], model: dict[str, Any],
           rho: float, budget_left: float) -> tuple[str, str] | None:
    """The myopic VOC rule (Hay et al. 2012): among available (kind, slot,
    features), take the largest predicted gain / price; None (submit) when the
    best ratio is below rho or no affordable move is left."""
    best, best_ratio = None, rho
    for kind, slot, feats in moves:
        if kind not in model["kinds"]:
            continue
        price = model["kinds"][kind]["price_usd"]
        if price > budget_left:
            continue
        ratio = predicted_gain(model, kind, feats) / price if price else float("inf")
        if ratio >= best_ratio and (best is None or ratio > best_ratio):
            best, best_ratio = (kind, slot), ratio
    return best


def preregister_rho(events: Sequence[dict[str, Any]], model: dict[str, Any],
                    proposal_cost: dict[str, float], target: float) -> dict[str, Any]:
    """ρ such that, on the fit grids, taking moves in order of predicted ratio
    until spend reaches the target, the median grid stops at that ratio."""
    per_grid = []
    for g in sorted({e["grid"] for e in events}):
        ev = sorted((e for e in events if e["grid"] == g and e["kind"] in model["kinds"]),
                    key=lambda e: -predicted_gain(model, e["kind"], e["features"])
                    / model["kinds"][e["kind"]]["price_usd"])
        spend, ratio = proposal_cost.get(g, 0.0), None
        for e in ev:
            ratio = predicted_gain(model, e["kind"], e["features"]) / model["kinds"][e["kind"]][
                "price_usd"]
            spend += e["usd"]
            if spend >= target:
                break
        per_grid.append(ratio if ratio is not None else 0.0)
    per_grid.sort()
    mid = len(per_grid) >> 1
    rho = per_grid[mid] if len(per_grid) & 1 else (per_grid[mid - 1] + per_grid[mid]) / (1 + 1)
    return {"rho": rho, "per_grid": per_grid, "target_spend": target}


# --- brief 006: calibrating the post-BP marginal ---------------------------------------

MARGINAL_CALIBRATION = DATA / "marginal-calibration.json"


def fit_marginal_calibration(run: dict[str, Any]) -> dict[str, Any]:
    """Monotone map g(marginal) by pool-adjacent-violators on each slot's top
    candidate at its grid's final checkpoint (one row per slot). Fit-seed
    grids only (D7)."""
    from .posterior import _pav

    if run.get("grids_seed") == VOC["eval_seed"] or run.get("grids_seed") != VOC["fit_seed"]:
        raise FitOnEvaluation("the marginal calibration is fitted on fit-seed grids only")
    pts = sorted((m, bool(y)) for g in run["grids"]
                 for m, y, _c in g["checkpoints"][-1]["slot_tops"].values())
    fitted = _pav([float(y) for _m, y in pts], [1.0] * len(pts))
    blocks: list[dict[str, Any]] = []
    for (m, y), p in zip(pts, fitted, strict=True):
        if blocks and blocks[-1]["calibrated"] == p:
            b = blocks[-1]
            b["hi"], b["count"], b["correct"] = m, b["count"] + 1, b["correct"] + int(y)
        else:
            blocks.append({"lo": m, "hi": m, "count": 1, "correct": int(y), "calibrated": p})
    return {"fit_seed": run["grids_seed"], "fitted_on": run["run_id"], "n_slots": len(pts),
            "blocks": blocks}


def calibrated(marginal: float, table: dict[str, Any]) -> float:
    """g(marginal): the step function of the PAV blocks (below the first block:
    its value; between blocks: the lower block's)."""
    value = table["blocks"][0]["calibrated"]
    for b in table["blocks"]:
        if marginal >= b["lo"]:
            value = b["calibrated"]
    return value


def commit_rule(marginal: float, table: dict[str, Any] | None, tau: float) -> bool:
    """Brief 006's rule: commit if g(marginal) >= tau; table None = 005's rule."""
    return (marginal if table is None else calibrated(marginal, table)) >= tau
