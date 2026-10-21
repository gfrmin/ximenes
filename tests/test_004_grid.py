"""Brief 004: grid numbering and crossers, reconstruction, belief propagation."""

import pytest

from ximenes.bp import Var, committed, exact_marginals, map_assignment, prior_with_other, propagate
from ximenes.grid import ACROSS, DOWN, ClueEntry, from_ipuz, from_rows, reconstruct

FIVE = ["....#", ".#.#.", ".....", ".#.#.", "#...."]


def test_numbering_and_lengths_on_a_hand_grid() -> None:
    g = from_rows(FIVE)
    assert g.symmetric()
    assert [(s.number, s.orientation, s.length) for s in g.slots] == [
        (1, ACROSS, 4), (1, DOWN, 4), (2, DOWN, 5), (3, DOWN, 4), (4, ACROSS, 5), (5, ACROSS, 4)]


def test_crossers() -> None:
    cx = from_rows(FIVE).crossers()
    assert (0, (1, DOWN), 0) in cx[(1, ACROSS)]
    assert (2, (2, DOWN), 2) in cx[(4, ACROSS)]
    assert all(len(v) >= 1 for v in cx.values())


def test_fifteen_by_fifteen_symmetry() -> None:
    rows = ["...............", ".#.#.#.#.#.#.#."] * 7 + ["..............."]
    g = from_rows(rows)
    assert g.width == g.height == 15 and g.symmetric()
    assert not from_rows(["#" + "." * 14] + ["." * 15] * 14).symmetric()


def test_ipuz_loader() -> None:
    doc = {"dimensions": {"width": 5, "height": 5},
           "puzzle": [[0 if ch == "." else "#" for ch in row] for row in FIVE]}
    assert from_ipuz(doc) == from_rows(FIVE)


def test_reconstruction_recovers_a_hand_grid_uniquely() -> None:
    # a 7x7 with 180-degree symmetry, filled with real words; reconstruct from
    # its clue list (numbers, orientations, answers) alone
    rows = ["CAT#SON", "A#O#E#O", "PLANETS", "E#R#R#E", "RAINBOW", "S#E#E#S", "SET#DIE"]
    g = from_rows(["".join("#" if ch == "#" else "." for ch in r) for r in rows])
    assert g.symmetric()
    letters = {(r, c): ch for r, row in enumerate(rows) for c, ch in enumerate(row) if ch != "#"}
    entries = [ClueEntry(s.number, s.orientation, "".join(letters[c] for c in s.cells))
               for s in g.slots]
    outcome, sols = reconstruct(entries, 7, 2, 10**6)
    assert outcome == "unique"
    assert sols[0][0] == g and sols[0][1] == letters


def test_reconstruction_reports_none_for_inconsistent_letters() -> None:
    entries = [ClueEntry(1, ACROSS, "CAT"), ClueEntry(1, DOWN, "DOG")]
    assert reconstruct(entries, 3, 2, 10**5)[0] == "none"


# --- belief propagation ---------------------------------------------------------------

def toy() -> tuple[dict[str, Var], list]:
    # A (across, 3) crosses B (down) at A[0]=B[0] and C (down) at A[2]=C[0]
    f = 0.05
    vs = {
        "A": Var(("CAT", "COT"), prior_with_other([0.5, 0.3], f)),
        "B": Var(("CAB", "OAK"), prior_with_other([0.6, 0.3], f)),
        "C": Var(("TOE", "RYE"), prior_with_other([0.4, 0.4], f)),
    }
    return vs, [("A", 0, "B", 0), ("A", 2, "C", 0)]


def test_bp_matches_exact_enumeration_on_a_tree() -> None:
    vs, es = toy()
    bp, ex = propagate(vs, es), exact_marginals(vs, es)
    for k in vs:
        assert bp[k] == pytest.approx(ex[k], abs=1e-6)


def test_other_absorbs_mass_and_evidence_is_hard() -> None:
    vs, es = toy()
    vs = {**vs, "C": committed("RYE")}  # RYE starts with R: neither CAT nor COT fits A[2]
    m = propagate(vs, es)
    assert m["A"][-1] == pytest.approx(1.0)  # all of A's mass moves to OTHER
    assert m["C"] == [1.0, 0.0]
    assert map_assignment(vs, es)["C"] == "RYE"


def test_prior_with_other_floor() -> None:
    p = prior_with_other([0.7, 0.4], 0.05)
    assert sum(p) == pytest.approx(1.0) and p[-1] == pytest.approx(0.05 / 1.15)
