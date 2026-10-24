"""Brief 016: the paired statistic matches the brief's worked cases; the
grids are never-read and fixed by the seed; the hybrid keeps D's right
answers, repairs a wrong one by escalation, and counts what it overturned."""

from __future__ import annotations

import pathlib

import pytest

from ximenes.clue import normalise
from ximenes.hybrid import CFG, Hybrid, _tables, p_paired, summary
from ximenes.instruments import PROPOSE_TOP, metered

FIX = pathlib.Path(__file__).parent / "fixtures" / "grid5" / "synthetic-grid5.json"


def test_paired_statistic_matches_the_brief() -> None:
    assert p_paired(3, 0) == pytest.approx(0.9375)
    assert p_paired(2, 0) == pytest.approx(0.875)
    assert p_paired(3, 1) == pytest.approx(0.8125)
    assert p_paired(0, 0) == pytest.approx(0.5)


def test_split_is_seeded_and_never_read() -> None:
    try:
        from ximenes.hybrid import hybrid_split, never_read
        pool = never_read()
    except Exception:  # noqa: BLE001 - no post-cutoff data on CI
        pytest.skip("post-cutoff grids absent")
    from ximenes.e2e import grids, split
    from ximenes.last_slots import reserve_split

    s = split(grids()[0])
    read = set(s["evaluation"]) | set(s["fit"]) | set(reserve_split())
    names = hybrid_split()
    assert names == hybrid_split() and not set(names) & read and set(names) <= set(pool)
    assert len(names) == min(CFG["grids"], len(pool))


def _run(d_answers, top):
    from ximenes.gridsolve import load_grid

    grid, clues = load_grid(FIX)
    gold = {k: normalise(c.answer) for k, c in clues.items()}
    seen = []

    def backend(instrument, model, inp):
        assert instrument == PROPOSE_TOP
        seen.append(inp["pattern"])
        return {"candidates": top}, {"usd": 0.01}

    cal = {"model": "logistic", "features": ["confidence"], "mean": [0.5], "sd": [0.1],
           "intercept": 0.0, "coef": {"confidence": 4.0}}
    b, totals = metered(backend)
    g = Hybrid("grid5", grid, clues, b, totals, _tables(), d_answers(gold), cal)
    return g, gold, seen


def test_confident_right_answers_commit_without_escalation() -> None:
    g, gold, seen = _run(lambda gold: {k: (v, 0.99) for k, v in gold.items()}, [])
    assert g.escalate(1.0) == "all_committed" and not seen
    assert g.submission() == gold


def test_a_wrong_low_confidence_answer_is_repaired_by_escalation() -> None:
    def d(gold):
        out = {k: (v, 0.99) for k, v in gold.items()}
        out["5A"] = ("TEAL", 0.3)  # wrong, unsure; crosses 3D's last letter (M)
        return out

    g, gold, seen = _run(d, [{"answer": "TEAM", "share": 0.8}, {"answer": "TEAL", "share": 0.1}])
    stop = g.escalate(1.0)
    assert seen and seen[0].endswith("M") and stop in ("all_committed", "no_new_candidates")
    assert g.submission()["5A"] == gold["5A"]


def test_summary_counts_and_decides() -> None:
    def grid(i: int, a: bool, b: bool) -> dict:
        arm = {"fully_correct": a, "clues_right": 1, "slots": 1, "usd": 0.3, "conflicts": 0,
               "calibration": [[0.9, a]], "calibrated": [[0.9, a]]}
        hyb = {**arm, "fully_correct": b, "stop": "budget",
               "overturned": {"right_to_wrong": 0, "wrong_to_right": int(b and not a)},
               "readouts": {str(x): {"fully_correct": b, "clues": 1.0} for x in CFG["readouts"]},
               "slot_confidences": [[0.95, b, True]]}
        return {"puzzle": f"p{i}", "direct": arm, "hybrid": hyb}

    doc = {"grids": [grid(0, False, True), grid(1, False, True), grid(2, False, True),
                     grid(3, True, True)]}
    s = summary(doc)
    assert s["paired"]["only_hybrid"] == 3 and s["paired"]["only_direct"] == 0
    assert s["decision"] == "hybrid_is_the_solver" and s["overturned"]["wrong_to_right"] == 3
