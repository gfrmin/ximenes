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


# --- policies offline on the 5x5 fixture ---------------------------------------------------

def _grid(policy: str, table: dict | None = None, budget: float = float("inf"),
          moves: list | None = None):
    import pathlib

    from test_005_voc import FIX, MODELS, fake

    from ximenes.gridsolve import load_grid
    from ximenes.instruments import metered
    from ximenes.policy import GridRun, load_tables

    grid, clues = load_grid(pathlib.Path(FIX) / "grid5" / "synthetic-grid5.json")
    backend, totals = metered(fake)
    g = GridRun("grid5", grid, clues, backend, totals, load_tables(), MODELS,
                commit_table=table)
    g.run(policy, budget=budget, moves=moves)
    return g


def test_crossers_first_respects_its_budget() -> None:
    g = _grid("crossers_first", budget=0.1)
    assert g.checkpoints[-1]["usd"] <= 0.1 + 0.1  # it stops at the first move past budget
    full = _grid("crossers_first")
    assert len(full.checkpoints) >= len(g.checkpoints)


def test_replaying_moves_under_the_same_rule_reproduces_the_run() -> None:
    a = _grid("crossers_first")
    moves = [(c["move"], c["slot"]) for c in a.checkpoints
             if c["move"] in ("solve", "formalise_more", "repropose")]
    b = _grid("replay_moves", moves=moves)
    strip = [{k: v for k, v in c.items() if k != "seconds"} for c in a.checkpoints]
    assert [{k: v for k, v in c.items() if k != "seconds"} for c in b.checkpoints] == strip


def test_calibrated_commits_are_never_overwritten() -> None:
    g = _grid("crossers_first", table=TABLE)
    final = g.checkpoints[-1]["slot_tops"]
    for k, word in g.commits.items():
        assert final[k][-1] is True  # still committed at the end
        assert g.variables()[k].words == (word,)
