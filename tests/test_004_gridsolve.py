"""Brief 004: the grid loop, offline on a 5x5 fixture (ordinary words, original
clues): crossers flip a wrong lone answer, a pattern re-proposal finds a word
the proposer missed, committed letters are never overwritten, replay is exact."""

import pathlib

from ximenes import posterior as post
from ximenes.gridsolve import edges_of, fits, load_grid, score_grid, solve_grid
from ximenes.instruments import memoized, stub_backend

FIX = pathlib.Path(__file__).parent / "fixtures"
MODELS = {k: "hand-fixture" for k in ("proposer", "formaliser", "judge")}


def _solve() -> tuple[object, dict]:
    grid, clues = load_grid(FIX / "grid5" / "synthetic-grid5.json")
    backend = memoized(stub_backend(FIX / "grid5-stub.jsonl"))
    return grid, solve_grid(grid, clues, models=MODELS, backend=backend,
                            model=post.load("logistic"), workers=2)


def test_grid_loop_replays_exactly_and_solves_the_fixture() -> None:
    grid, a = _solve()
    _, b = _solve()
    assert a == b
    s = score_grid(grid, a)
    assert s["fully_correct"] and s["clues_correct"] == 1.0
    assert s["clues_correct_alone"] < 1.0  # crossers and re-proposal did the rest
    assert a["slots"]["4A"]["alone_answer"] == "ABOVE" and a["slots"]["4A"]["submitted"] == "ABOUT"
    assert a["slots"]["3D"]["reproposed"] >= 1 and a["slots"]["3D"]["submitted"] == "ATOM"
    assert not s["proven"] and s["quarantine_reasons"] == {"synonym": 6}


def test_committed_letters_are_never_overwritten() -> None:
    _, r = _solve()
    for k, slot in r["slots"].items():
        if slot["committed_round"] is not None:
            assert slot["submitted"] == slot["committed_word"], k


def test_edges_and_pattern_fit() -> None:
    grid, _ = load_grid(FIX / "grid5" / "synthetic-grid5.json")
    edges = edges_of(grid)
    assert ("1A", 0, "1D", 0) in edges and all(a < b for a, _i, b, _j in edges)
    assert fits("ATOM", "?T?M") and not fits("ITEM", "?T?N") and not fits("AT", "?T?M")
