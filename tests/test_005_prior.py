"""Brief 005: the OTHER prior is fitted on val, sums to 1 per band, refuses
test, and the slot prior is a proper distribution."""

import json

import pytest

from ximenes.posterior import BANDS, FitOnTest
from ximenes.voc import OTHER_PRIOR, fit_other_prior, load_other_prior, slot_prior


def test_committed_table_sums_to_one_per_band_and_names_val() -> None:
    t = load_other_prior()
    assert len(t["rows"]) == len(BANDS)
    for r in t["rows"]:
        assert r["p_other"] + r["p_inside"] == pytest.approx(1.0)
    assert "val" in json.loads(OTHER_PRIOR.read_text())["source"]


def test_fit_refuses_test() -> None:
    with pytest.raises(FitOnTest):
        fit_other_prior({"set": "test", "items": [], "run_id": "x"}, {"model": "logistic"})


@pytest.mark.parametrize("ps", [[0.97, 0.01], [0.3, 0.2, 0.1], [0.6], []])
def test_slot_prior_is_a_distribution(ps: list[float]) -> None:
    p = slot_prior(ps, load_other_prior())
    assert sum(p) == pytest.approx(1.0) and len(p) == len(ps) + 1
    if len(ps) > 1:
        assert p[0] >= p[1]  # candidates keep their order
