"""Brief 015, Stage D: the puzzle as text, reading the reply, scoring a grid
(conflicts, missing slots), the paired table, and a stub run end to end."""

from __future__ import annotations

import pathlib

from ximenes.clue import normalise
from ximenes.direct import CFG, answers_of, paired, puzzle_text, run, score_grid
from ximenes.gridsolve import load_grid
from ximenes.instruments import SOLVE_GRID

FIX = pathlib.Path(__file__).parent / "fixtures" / "grid5" / "synthetic-grid5.json"


def _grid():
    grid, clues = load_grid(FIX)
    return grid, clues, {k: normalise(c.answer) for k, c in clues.items()}


def test_puzzle_text_lists_every_slot_and_its_crossings() -> None:
    grid, clues, _gold = _grid()
    clue_lines, grid_lines = puzzle_text(grid, clues)
    assert [ln.split(".")[0] for ln in clue_lines] == ["1A", "4A", "5A", "1D", "2D", "3D"]
    assert grid_lines[0].startswith("1A (4 letters): letter 1 = 1D letter 1")
    assert all("(" in ln and ln.endswith(")") for ln in clue_lines)


def test_score_grid_counts_conflicts_and_missing() -> None:
    grid, _clues, gold = _grid()
    right = {k: (v, 0.9) for k, v in gold.items()}
    s = score_grid(right, grid, gold)
    assert s["fully_correct"] and s["conflicts"] == 0 and s["clues"] == 1.0
    bad = {**right, "1A": ("XTAR", 0.5)}  # first letter crosses 1D's S
    s = score_grid(bad, grid, gold)
    assert not s["fully_correct"] and s["conflicts"] == 1 and s["clues_right"] == len(gold) - 1
    gone = {k: v for k, v in right.items() if k != "5A"}
    assert score_grid(gone, grid, gold)["missing"] == 1


def test_answers_of_normalises_and_skips_unknown_slots() -> None:
    grid, _clues, _gold = _grid()
    out = answers_of({"answers": [{"slot": "1 a", "answer": "st-ar", "confidence": 1.5},
                                  {"slot": "9D", "answer": "X", "confidence": 0.1}]}, grid)
    assert out == {"1A": ("STAR", 1.0)}


def test_paired_table() -> None:
    d = {"a": True, "b": True, "c": False}
    s = {"a": True, "b": False, "c": False, "z": True}
    t = paired(d, s)
    assert (t["n"], t["both"], t["only_direct"], t["only_solver"], t["neither"]) == (3, 1, 1, 0, 1)
    assert t["p_direct_greater"] > 0.5


def test_run_with_a_stub_backend(monkeypatch) -> None:
    from ximenes import e2e

    grid, clues, gold = _grid()
    monkeypatch.setattr(e2e, "grids", lambda *a, **k: ([FIX], {}))
    seen = []

    def backend(instrument, model, inp):
        seen.append((instrument, model, inp["prompt"], inp["effort"], inp["max_tokens"]))
        return ({"answers": [{"slot": k, "answer": v, "confidence": 0.8}
                             for k, v in gold.items()], "_stop_reason": "end_turn"}, {"usd": 0.0})

    out = run("D1", [("014", FIX.stem)], backend)
    cfg = CFG["arms"]["D1"]
    assert seen == [(SOLVE_GRID, cfg["model"], CFG["prompt"], cfg["effort"], cfg["max_tokens"])]
    assert out[0]["fully_correct"] and out[0]["calibration"] == [[0.8, True]] * len(gold)


def test_clues_only_arm_sends_no_grid(monkeypatch) -> None:
    """Brief 018: arm C's input has no grid lines and the clues-only prompt;
    D1's input (and so its replay key) is unchanged."""
    from ximenes import e2e

    grid, clues, gold = _grid()
    monkeypatch.setattr(e2e, "grids", lambda *a, **k: ([FIX], {}))
    seen = []

    def backend(instrument, model, inp):
        seen.append(dict(inp))
        return ({"answers": [{"slot": k, "answer": v, "confidence": 0.8}
                             for k, v in gold.items()]}, {"usd": 0.0})

    run("C", [("018", FIX.stem)], backend)
    run("D1", [("018", FIX.stem)], backend)
    assert "grid" not in seen[0] and seen[0]["prompt"] == "direct-clues-v1"
    assert seen[1]["prompt"] == "direct-grid-v1" and "grid" in seen[1]
    assert set(seen[1]) == {"clues", "grid", "prompt", "render", "format", "effort",
                            "max_tokens"}
