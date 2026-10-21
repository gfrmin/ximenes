"""Brief 005: priced moves, the gain model, the VOC chooser (pure), score at a
budget from checkpoints, and the policy loop offline on the 5x5 fixture."""

import pathlib

import pytest

from ximenes.gridsolve import load_grid
from ximenes.instruments import FORMALISE_CLUE, PROPOSE_ANSWERS, PROPOSE_PATTERN, metered
from ximenes.policy import GridRun, load_tables, score_at
from ximenes.voc import VOC, FitOnEvaluation, choose, fit_gain, predicted_gain

FIX = pathlib.Path(__file__).parent / "fixtures"
MODELS = {k: "hand-fixture" for k in ("proposer", "formaliser", "judge")}

MODEL = {"kinds": {
    "solve": {"features": ["top_vote_share"], "weights": [0.0, 1.0], "price_usd": 0.02},
    "repropose": {"features": ["other_mass"], "weights": [0.0, 1.0], "price_usd": 0.01},
}}


@pytest.mark.parametrize("moves,rho,budget,expected", [
    ([("solve", "1A", {"top_vote_share": 0.4}), ("repropose", "2D", {"other_mass": 0.3})],
     0.0, 1.0, ("repropose", "2D")),           # 0.3/0.01 = 30 beats 0.4/0.02 = 20
    ([("solve", "1A", {"top_vote_share": 0.4})], 25.0, 1.0, None),   # below rho: submit
    ([("solve", "1A", {"top_vote_share": 0.4}), ("repropose", "2D", {"other_mass": 0.3})],
     0.0, 0.015, ("repropose", "2D")),         # solve unaffordable
    ([("solve", "1A", {"top_vote_share": 0.4})], 0.0, 0.01, None),   # nothing affordable
    ([("formalise_more", "3A", {})], 0.0, 1.0, None),                # kind not modelled
    ([], 0.0, 1.0, None),
])
def test_chooser(moves: list, rho: float, budget: float, expected: object) -> None:
    assert choose(moves, MODEL, rho, budget) == expected


def _events(grid: str, n: int) -> list[dict]:
    return [{"grid": grid, "kind": "repropose", "usd": 0.01 * (i + 1), "seconds": 2.0,
             "delta": 0.1 * i, "features": {"max_marginal": 0.5, "other_mass": 0.1 * i,
                                            "committed_crossers": 0.0, "pattern_density": 0.2,
                                            "round": 0.0, "n_candidates": 3.0}}
            for i in range(n)]


def test_prices_are_reproduced_from_events() -> None:
    ev = _events("g1", 3) + _events("g2", 3)
    m = fit_gain(ev, VOC["fit_seed"])["kinds"]["repropose"]
    assert m["price_usd"] == pytest.approx(0.02) and m["price_seconds"] == pytest.approx(2.0)
    assert m["n"] == len(ev)
    assert predicted_gain({"kinds": {"repropose": m}}, "repropose", ev[-1]["features"]) == \
        pytest.approx(0.2, abs=0.05)


def test_gain_model_refuses_evaluation_grids() -> None:
    with pytest.raises(FitOnEvaluation):
        fit_gain(_events("g1", 2), VOC["eval_seed"])


def test_score_at_budget_reads_the_log() -> None:
    cps = [{"usd": 0.2, "clues_correct": 0.4}, {"usd": 0.5, "clues_correct": 0.6},
           {"usd": 0.9, "clues_correct": 0.7}]
    assert score_at(cps, 0.6)["clues_correct"] == 0.6
    assert score_at(cps, 0.1)["clues_correct"] == 0.4  # below the floor: the floor
    assert score_at(cps, 5.0)["clues_correct"] == 0.7


# --- the policy loop offline -----------------------------------------------------------

SAMPLES = {"heavenly body": ["STAR"] * 18 + ["SUNS"] * 2,
           "thick slice": ["SLAB"] * 15 + ["SLUB"] * 5,
           "solitary single": ["ALONE"] * 16 + ["ONLY"] * 4,
           "tiny particle": ["IOTA"] * 12 + ["MOTE"] * 8,
           "regarding concerning": ["ABOVE"] * 12 + ["ABOUT"] * 8,
           "side squad": ["TEAM"] * 17 + ["CREW"] * 3}
GOLD = {"STAR", "SLAB", "ALONE", "ATOM", "ABOUT", "TEAM", "ABOVE"}


def fake(instrument: str, model: str, inp: dict) -> tuple[object, dict]:
    if instrument == PROPOSE_ANSWERS:
        return SAMPLES[inp["clue_text"]], {"usd": 0.01, "seconds": 1.0}
    if instrument == PROPOSE_PATTERN:
        return ["ATOM"] * 7 + ["ITEM"] * 3, {"usd": 0.005, "seconds": 1.0}
    if instrument == FORMALISE_CLUE:
        w0, w1 = inp["tokens"]
        return f'clue(defn(tok("{w0}")), syn(tok("{w1}"), "{inp["answer"]}"))', \
            {"usd": 0.02, "seconds": 3.0}
    return {"score": 0.92 if inp["value"] in GOLD else 0.15, "reason": "t"}, \
        {"usd": 0.001, "seconds": 0.5}


def _run(policy: str) -> GridRun:
    grid, clues = load_grid(FIX / "grid5" / "synthetic-grid5.json")
    backend, totals = metered(fake)
    g = GridRun("grid5", grid, clues, backend, totals, load_tables(), MODELS)
    g.run(policy)
    return g


def test_vote_only_is_the_proposal_state() -> None:
    g = _run("vote")
    assert len(g.checkpoints) == 1 and g.checkpoints[0]["usd"] == pytest.approx(0.06)


def test_attempt_all_solves_every_slot_in_order_and_spend_rises() -> None:
    g = _run("attempt_all")
    moves = [c for c in g.checkpoints if c["move"] == "solve"]
    assert len(moves) == len(g.s)
    spends = [c["usd"] for c in g.checkpoints]
    assert spends == sorted(spends)
    assert not [e for e in g.events if e["kind"] != "solve"]


def test_fit_policy_logs_every_move_kind_it_can() -> None:
    g = _run("fit")
    kinds = {e["kind"] for e in g.events}
    assert "solve" in kinds and kinds <= {"solve", "formalise_more", "repropose"}
    assert all(set(e["features"]) for e in g.events)
