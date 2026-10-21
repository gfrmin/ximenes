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
from .posterior import BANDS, FitOnTest, band, posterior

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
