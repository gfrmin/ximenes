"""Brief 003: posteriors are fitted on val only, deterministic, auditable;
the decision layer is a pure function; ECE/risk-coverage are shared with 000."""

import json
import pathlib
from fractions import Fraction

import pytest

from ximenes.data import read_cryptonite
from ximenes.decide import act
from ximenes.eval import PARAMS, Vote, ece, ece_of, risk_coverage
from ximenes.instruments import replay_then, stub_backend
from ximenes.posterior import (
    TABLES,
    FitOnTest,
    _pav,
    fit,
    fit_binned,
    predict_logistic,
    rows,
)
from ximenes.solve import run

FIX = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def synthetic_val() -> dict:
    """The offline 20-clue loop (original clues), labelled as a val run."""
    clues = read_cryptonite(FIX / "clues-20.jsonl")
    backend = replay_then(FIX / "stub-20.jsonl", stub_backend(FIX / "solve-stub-20.jsonl"))
    models = {k: "hand-fixture" for k in ("proposer", "formaliser", "judge")}
    out = run(clues, models=models, backend=backend, k=20, m=3, retries=2, floor=0.5,
              workers=4, score_indicators=False)
    return {**out, "set": "val", "run_id": "synthetic"}


def test_fit_refuses_test(synthetic_val: dict) -> None:
    with pytest.raises(FitOnTest):
        fit("test", synthetic_val)
    with pytest.raises(FitOnTest):
        fit("val", {**synthetic_val, "set": "test"})


def test_fits_are_deterministic_and_counts_add_up(synthetic_val: dict) -> None:
    a, b = fit("val", synthetic_val), fit("val", synthetic_val)
    assert a == b
    n = len(rows(synthetic_val))
    assert sum(c["n"] for c in a["binned"]["cells"]) == n == a["binned"]["n_candidates"]
    assert a["binned"]["chosen"] in ("binned", "logistic")


def test_binned_is_monotone_within_status(synthetic_val: dict) -> None:
    cells = fit_binned(rows(synthetic_val))["cells"]
    for status in {c["status"] for c in cells}:
        ps = [c["p"] for c in cells if c["status"] == status]
        assert ps == sorted(ps)


def test_pav() -> None:
    assert _pav([0.5, 0.2, 0.9], [1.0, 1.0, 2.0]) == pytest.approx([0.35, 0.35, 0.9])
    assert _pav([0.1, 0.2], [1.0, 1.0]) == [0.1, 0.2]


@pytest.mark.skipif(not TABLES["logistic"].exists(), reason="posterior not fitted yet")
def test_committed_tables_reproduce_from_the_val_log() -> None:
    committed = {k: json.loads(p.read_text()) for k, p in TABLES.items()}
    src = pathlib.Path("runs") / f"{committed['binned']['fitted_on']}.json"
    if not src.exists():
        pytest.skip("the val solve run is local (runs/)")
    refit = fit("val", json.loads(src.read_text()))
    for k in TABLES:
        assert {**refit[k], "source": committed[k]["source"]} == committed[k], k


def test_logistic_prediction_is_a_probability(synthetic_val: dict) -> None:
    m = fit("val", synthetic_val)["logistic"]
    for _s, _h, f, _y in rows(synthetic_val):
        assert 0.0 < predict_logistic(m, f) < 1.0


# --- decide is a pure function of the posteriors and tau --------------------------------

@pytest.mark.parametrize("ps,tau,expected,members", [
    ([0.95, 0.03], 0.9, "point", [0]),
    ([0.6, 0.35, 0.02], 0.9, "set", [0, 1]),
    ([0.25, 0.7], 0.9, "set", [1, 0]),
    ([0.4, 0.3, 0.1], 0.9, "abstain", []),
    ([], 0.5, "abstain", []),
    ([0.5], 0.5, "point", [0]),
])
def test_act(ps: list[float], tau: float, expected: str, members: list[int]) -> None:
    a = act(ps, tau)
    assert a["act"] == expected and a["members"] == members


# --- ECE and risk-coverage share brief 000's function ---------------------------------------

def test_shared_ece_is_zero_when_perfectly_calibrated() -> None:
    bins = PARAMS["bins"]
    conf = [j / bins for j in range(bins + 1) for _ in range(bins)]
    corr = [i < j for j in range(bins + 1) for i in range(bins)]
    value, _ = ece_of(conf, corr, bins)
    assert value == pytest.approx(0, abs=1e-12)  # floats j/10 are not exact fractions
    votes = [Vote("X", Fraction(c), y) for c, y in zip(conf, corr, strict=True)]
    assert value == float(ece(votes, bins))


def test_risk_coverage() -> None:
    rc = risk_coverage([0.9, 0.1, 0.5], [True, False, True])
    assert rc == [(1 / 3, 1.0), (2 / 3, 1.0), (1.0, 2 / 3)]
