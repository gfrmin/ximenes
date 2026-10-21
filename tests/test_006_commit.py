"""Brief 006: the marginal calibration is monotone, counts the fit grids'
slots, refuses evaluation grids; the commit rule is a pure function."""

import json

import pytest

from ximenes.voc import (
    MARGINAL_CALIBRATION,
    VOC,
    FitOnEvaluation,
    calibrated,
    commit_rule,
    fit_marginal_calibration,
)

TABLE = {"blocks": [{"lo": 0.0, "calibrated": 0.1}, {"lo": 0.3, "calibrated": 0.6},
                    {"lo": 0.5, "calibrated": 0.95}, {"lo": 0.9, "calibrated": 1.0}]}


def test_committed_table_is_monotone_and_counts_slots() -> None:
    t = json.loads(MARGINAL_CALIBRATION.read_text())
    ps = [b["calibrated"] for b in t["blocks"]]
    assert ps == sorted(ps)
    assert sum(b["count"] for b in t["blocks"]) == t["n_slots"]
    assert t["fit_seed"] == VOC["fit_seed"]


def test_fit_refuses_evaluation_grids() -> None:
    for seed in (VOC["eval_seed"], 12345):
        with pytest.raises(FitOnEvaluation):
            fit_marginal_calibration({"grids_seed": seed, "grids": [], "run_id": "x"})


@pytest.mark.parametrize("m,expected", [(0.0, 0.1), (0.29, 0.1), (0.3, 0.6), (0.7, 0.95),
                                        (0.95, 1.0), (1.0, 1.0)])
def test_calibrated_step_function(m: float, expected: float) -> None:
    assert calibrated(m, TABLE) == expected


@pytest.mark.parametrize("m,table,commit", [
    (0.6, TABLE, True),     # calibrated 0.95 >= 0.9
    (0.6, None, False),     # 005's rule on the raw marginal
    (0.4, TABLE, False),
    (0.92, None, True),
    (0.92, TABLE, True),
])
def test_commit_rule(m: float, table: dict | None, commit: bool) -> None:
    assert commit_rule(m, table, VOC.get("tau", 0.9)) is commit
