"""Brief 007: the commit-time refit reads fit-seed rows only (one per
uncommitted slot-step), CV folds never split a grid, the map is monotone."""

import json

import pytest

from ximenes.voc import (
    MARGINAL_CALIBRATION_STEPS,
    VOC,
    FitOnEvaluation,
    fit_marginal_calibration_steps,
    step_rows,
)


def _run(seed: int) -> dict:
    cp = {"slot_tops": {"1A": [0.95, True, False], "2D": [0.3, False, False],
                        "3A": [1.0, True, True]}}
    return {"grids_seed": seed, "run_id": "t",
            "grids": [{"puzzle": f"g{i}", "checkpoints": [cp, cp]} for i in range(4)]}


def test_rows_are_uncommitted_slot_steps_from_fit_grids_only() -> None:
    rows = step_rows(_run(VOC["fit_seed"]))
    assert len(rows) == 4 * 2 * 2  # 4 grids x 2 checkpoints x 2 uncommitted slots
    with pytest.raises(FitOnEvaluation):
        step_rows(_run(VOC["eval_seed"]))


def test_cv_folds_never_split_a_grid() -> None:
    t = fit_marginal_calibration_steps(_run(VOC["fit_seed"]), 4)
    assert t["n_grids"] == 4 and t["folds"] == 4
    assert sum(b["n"] for b in t["cv_bins"]) == t["n_rows"]


def test_committed_map_is_monotone() -> None:
    t = json.loads(MARGINAL_CALIBRATION_STEPS.read_text())
    ps = [b["calibrated"] for b in t["blocks"]]
    assert ps == sorted(ps) and t["fit_seed"] == VOC["fit_seed"]
