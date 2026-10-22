"""Brief 003: P(candidate is correct | features), fitted on val only.

Two auditable models over the pre-registered features (briefs/003): M1, a
binned table monotone-smoothed within status, and M2, an L2 logistic
regression. Both are fitted on a val solve run and committed as data tables;
the test run is only ever *scored*. `fit` refuses the test split.
"""

from __future__ import annotations

import json
import math
import pathlib
from collections.abc import Sequence
from typing import Any

from .data import DATA
from .eval import PARAMS

P = PARAMS["posterior"]
BANDS: list[float] = P["bands"]
FEATURES = (
    "is_ok", "is_quarantine", "definition_score", "definition_missing", "min_leaf_score",
    "min_leaf_missing", "n_oracle_leaves", "unreviewed_table", "vote_share",
    "is_vote_winner", "candidate_rank", "margin",
)
LEAF_REASONS = frozenset({"synonym", "homophone", "indicator"})
DEF_REASONS = frozenset({"double_def", "cryptic_def"})


class FitOnTest(ValueError):
    """Fitting on the test split is refused by construction (briefs/003)."""


# --- features ------------------------------------------------------------------------


def _definition_score(h: dict[str, Any]) -> float | None:
    d = h["scores"].get("definition")
    if d and d.get("status") == "judged" and d.get("score") is not None:
        return float(d["score"])
    dd = [lf["score"] for lf in h["scores"]["leaves"]
          if lf["reason"] in DEF_REASONS and lf["score"] is not None]
    return min(dd) if dd else None


def _leaf_score(h: dict[str, Any]) -> float | None:
    s = [lf["score"] for lf in h["scores"]["leaves"]
         if lf["reason"] in LEAF_REASONS and lf["score"] is not None]
    return min(s) if s else None


def features(h: dict[str, Any], others: Sequence[dict[str, Any]]) -> dict[str, float]:
    """The pre-registered features of one candidate (Hyp record); missing scores
    are a flag plus 0, never imputed."""
    ds, ls = _definition_score(h), _leaf_score(h)
    own = h["scores"]["min_score"] or 0.0
    best_other = max((o["scores"]["min_score"] or 0.0 for o in others), default=0.0)
    return {
        "is_ok": float(h["status"] == "Ok"),
        "is_quarantine": float(h["status"] == "Quarantine"),
        "definition_score": ds or 0.0,
        "definition_missing": float(ds is None),
        "min_leaf_score": ls or 0.0,
        "min_leaf_missing": float(ls is None),
        "n_oracle_leaves": float(len(h["scores"]["leaves"])),
        "unreviewed_table": float("table_unreviewed" in h["reasons"]),
        "vote_share": float(h["vote_share"]),
        "is_vote_winner": float(h["candidate_rank"] == 0),
        "candidate_rank": float(h["candidate_rank"]),
        "margin": own - best_other,
    }


ATTESTED_FEATURES = (*FEATURES, "syn_attested_share", "syn_unattested_n",
                     "min_leaf_score_unattested", "syn_none", "unattested_missing")


def features_attested(h: dict[str, Any], others: Sequence[dict[str, Any]]) -> dict[str, float]:
    """Brief 008: 003's features plus synonym attestation (missing = flag + 0)."""
    syn = [c for c in h["prov"]["oracle_calls"] if c["reason"] == "synonym"]
    unatt = [c for c in syn if not c.get("attested")]
    scores = [c["score"] for c in unatt if c["score"] is not None]
    return {
        **features(h, others),
        "syn_attested_share": (len(syn) - len(unatt)) / len(syn) if syn else 0.0,
        "syn_unattested_n": float(len(unatt)),
        "min_leaf_score_unattested": min(scores) if scores else 0.0,
        "syn_none": float(not syn),
        "unattested_missing": float(not scores),
    }


def _features_for(model_features: Sequence[str]):  # noqa: ANN202
    return features_attested if "syn_attested_share" in model_features else features


def rows(run: dict[str, Any], attested: bool = False
         ) -> list[tuple[str, dict[str, Any], dict[str, float], bool]]:
    """(slot, hyp, features, correct) for every candidate of every clue."""
    feat = features_attested if attested else features
    out = []
    for item in run["items"]:
        cands = item["candidates"]
        for i, h in enumerate(cands):
            out.append((item["slot"], h, feat(h, cands[:i] + cands[i + 1:]),
                        h["answer"] == item["answer"]))
    return out


# --- M1: binned, monotone within status -------------------------------------------------


def band(x: float | None) -> int:
    """Band index for a score; a missing score (nothing to judge) is the top band."""
    if x is None:
        return len(BANDS) - 1
    return max(i for i, lo in enumerate(BANDS) if x >= lo)


def cell(h: dict[str, Any]) -> tuple[str, int, int]:
    return h["status"], band(_leaf_score(h)), band(_definition_score(h))


def _pav(values: list[float], weights: list[float]) -> list[float]:
    """Pool-adjacent-violators: the weighted non-decreasing fit."""
    blocks: list[list[float]] = []  # [value, weight, size]
    for v, w in zip(values, weights, strict=True):
        blocks.append([v, w, 1])
        while len(blocks) > 1 and blocks[-1 - 1][0] > blocks[-1][0]:
            v2, w2, n2 = blocks.pop()
            v1, w1, n1 = blocks.pop()
            blocks.append([(v1 * w1 + v2 * w2) / (w1 + w2), w1 + w2, n1 + n2])
    return [b[0] for b in blocks for _ in range(int(b[-1]))]


def fit_binned(data: Sequence[tuple[str, dict[str, Any], dict[str, float], bool]]
               ) -> dict[str, Any]:
    counts: dict[tuple[str, int, int], list[int]] = {}
    for _slot, h, _f, y in data:
        c = counts.setdefault(cell(h), [0, 0])
        c[0] += 1
        c[1] += int(y)
    table = []
    for status in sorted({k[0] for k in counts}):
        keys = sorted((k for k in counts if k[0] == status),
                      key=lambda k: (min(k[1], k[-1]), max(k[1], k[-1]), k[1]))
        raw = [counts[k][1] / counts[k][0] for k in keys]
        smooth = _pav(raw, [float(counts[k][0]) for k in keys])
        table += [{"status": k[0], "leaf_band": k[1], "definition_band": k[-1],
                   "n": counts[k][0], "correct": counts[k][1], "p": p}
                  for k, p in zip(keys, smooth, strict=True)]
    status_rate = {s: sum(r["correct"] for r in table if r["status"] == s)
                   / sum(r["n"] for r in table if r["status"] == s)
                   for s in {r["status"] for r in table}}
    return {"model": "binned", "bands": BANDS, "cells": table, "status_rate": status_rate}


def predict_binned(model: dict[str, Any], h: dict[str, Any]) -> float:
    status, lb, db = cell(h)
    for r in model["cells"]:
        if (r["status"], r["leaf_band"], r["definition_band"]) == (status, lb, db):
            return r["p"]
    return model["status_rate"].get(status, 0.0)  # an unseen cell: its status's rate


# --- M2: L2 logistic regression (Newton) --------------------------------------------------


def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        for r in range(n):
            if r != c and m[c][c]:
                f = m[r][c] / m[c][c]
                m[r] = [x - f * y for x, y in zip(m[r], m[c], strict=True)]
    return [m[i][-1] / m[i][i] for i in range(n)]


def _sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))


def _standardise(xs: list[list[float]]) -> tuple[list[float], list[float]]:
    n = len(xs)
    mean = [sum(col) / n for col in zip(*xs, strict=True)]
    sd = [math.sqrt(sum((x - mu) * (x - mu) for x in col) / n) or 1.0
          for col, mu in zip(zip(*xs, strict=True), mean, strict=True)]
    return mean, sd


VOTE_FEATURES = ("vote_share", "candidate_rank", "is_vote_winner")


def fit_logistic(data: Sequence[tuple[str, dict[str, Any], dict[str, float], bool]],
                 l2: float, features: Sequence[str] = FEATURES) -> dict[str, Any]:
    xs = [[f[k] for k in features] for _s, _h, f, _y in data]
    ys = [float(y) for *_rest, y in data]
    mean, sd = _standardise(xs)
    zs = [[1.0] + [(x - mu) / s for x, mu, s in zip(row, mean, sd, strict=True)] for row in xs]
    w = [0.0] * len(zs[0])
    for _ in range(P["newton_iters"]):
        ps = [_sigmoid(sum(a * b for a, b in zip(w, z, strict=True))) for z in zs]
        grad = [sum((p - y) * z[j] for p, y, z in zip(ps, ys, zs, strict=True))
                + l2 * w[j] * (j > 0) for j in range(len(w))]
        hess = [[sum(p * (1 - p) * z[i] * z[j] for p, z in zip(ps, zs, strict=True))
                 + (l2 if i == j and i > 0 else 0.0) for j in range(len(w))] for i in range(len(w))]
        step = _solve(hess, grad)
        w = [a - b for a, b in zip(w, step, strict=True)]
        if max(map(abs, step)) < P["tol"]:
            break
    return {"model": "logistic", "features": list(features), "l2": l2, "mean": mean, "sd": sd,
            "intercept": w[0], "coef": dict(zip(features, w[1:], strict=True))}


def predict_logistic(model: dict[str, Any], f: dict[str, float]) -> float:
    z = model["intercept"] + sum(
        model["coef"][k] * (f[k] - mu) / s
        for k, mu, s in zip(model["features"], model["mean"], model["sd"], strict=True))
    return _sigmoid(z)


# --- fitting, cross-validation, choice ------------------------------------------------------


def log_loss(ps: Sequence[float], ys: Sequence[bool]) -> float:
    c = P["clip"]
    return -sum(math.log(min(1 - c, max(c, p))) if y else math.log(min(1 - c, max(c, 1 - p)))
                for p, y in zip(ps, ys, strict=True)) / len(ps)


def _folds(data: Sequence[Any]) -> list[set[str]]:
    slots = sorted({d[0] for d in data})
    return [set(slots[i::P["folds"]]) for i in range(P["folds"])]


def cv_log_loss(data: Sequence[tuple[str, dict[str, Any], dict[str, float], bool]],
                which: str, l2: float = 0.0, features: Sequence[str] = FEATURES) -> float:
    """Out-of-fold log-loss, folds grouped by clue (a clue's candidates never
    straddle train and held-out)."""
    ps, ys = [], []
    for held in _folds(data):
        train = [d for d in data if d[0] not in held]
        test = [d for d in data if d[0] in held]
        if which == "binned":
            m = fit_binned(train)
            ps += [predict_binned(m, h) for _s, h, _f, _y in test]
        else:
            m = fit_logistic(train, l2, features)
            ps += [predict_logistic(m, f) for _s, _h, f, _y in test]
        ys += [y for *_rest, y in test]
    return log_loss(ps, ys)


def fit(split: str, run: dict[str, Any]) -> dict[str, Any]:
    """Fit both models on a val solve run; choose by out-of-fold log-loss."""
    if split == "test" or run.get("set") == "test":
        raise FitOnTest("posteriors are fitted on val only; test is scored, never fitted")
    data = rows(run)
    cv = {l2: cv_log_loss(data, "logistic", l2) for l2 in P["l2_grid"]}
    l2 = min(cv, key=lambda k: cv[k])
    binned, logistic = fit_binned(data), fit_logistic(data, l2)
    losses = {"binned": cv_log_loss(data, "binned"), "logistic": cv[l2]}
    chosen = min(losses, key=lambda k: losses[k])
    meta = {"fitted_on": run["run_id"], "split": split, "n_clues": len(run["items"]),
            "n_candidates": len(data), "cv_log_loss": losses, "chosen": chosen}
    cv_by_l2 = {str(k): v for k, v in cv.items()}
    return {"binned": {**binned, **meta}, "logistic": {**logistic, **meta, "cv_by_l2": cv_by_l2}}


def posterior(model: dict[str, Any], h: dict[str, Any], others: Sequence[dict[str, Any]]) -> float:
    if model["model"] == "binned":
        return predict_binned(model, h)
    return predict_logistic(model, _features_for(model["features"])(h, others))


TABLES = {"binned": DATA / "posterior-binned.json", "logistic": DATA / "posterior-logistic.json"}


def load(which: str) -> dict[str, Any]:
    return json.loads(pathlib.Path(TABLES[which]).read_text())


VOTE_TABLE = DATA / "posterior-vote.json"


def fit_vote(split: str, run: dict[str, Any]) -> dict[str, Any]:
    """Brief 005: P(candidate correct | vote features only), for slots not yet
    formalised. Val only (D7)."""
    if split == "test" or run.get("set") == "test":
        raise FitOnTest("posteriors are fitted on val only; test is scored, never fitted")
    data = rows(run)
    cv = {l2: cv_log_loss(data, "logistic", l2, VOTE_FEATURES) for l2 in P["l2_grid"]}
    l2 = min(cv, key=lambda k: cv[k])
    return {**fit_logistic(data, l2, VOTE_FEATURES), "fitted_on": run["run_id"], "split": split,
            "cv_log_loss": cv[l2], "cv_by_l2": {str(k): v for k, v in cv.items()}}


ATTESTED_TABLE = DATA / "posterior-logistic-attested.json"


def fit_attested(split: str, run: dict[str, Any]) -> dict[str, Any]:
    """Brief 008: 003's logistic plus attestation features; val only (D7)."""
    if split != "val" or run.get("set") != "val":
        raise FitOnTest("the attested posterior is fitted on val only")
    data = rows(run, attested=True)
    cv = {l2: cv_log_loss(data, "logistic", l2, ATTESTED_FEATURES) for l2 in P["l2_grid"]}
    l2 = min(cv, key=lambda k: cv[k])
    base = cv_log_loss(rows(run), "logistic", min(
        P["l2_grid"], key=lambda k: cv_log_loss(rows(run), "logistic", k)))
    return {**fit_logistic(data, l2, ATTESTED_FEATURES), "fitted_on": run["run_id"],
            "split": split, "cv_log_loss": cv[l2], "cv_log_loss_without": base,
            "cv_by_l2": {str(k): v for k, v in cv.items()}}
