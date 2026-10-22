"""Brief 010 appendix: gold-in-k ranking and curve."""

from ximenes.clue import Clue, Enumeration
from ximenes.recall import curve, rank_of, ranked


def test_ranked_by_votes_then_first_appearance_valid_only() -> None:
    clue = Clue("x", Enumeration((3,), ()))
    samples = ["dog", "cat", "cat", "mouse", "dog", "emu", ""]
    assert ranked(samples, clue) == ["DOG", "CAT", "EMU"]


def test_curve_counts_gold_within_top_k() -> None:
    assert rank_of(["DOG", "CAT"], "CAT") == 1 and rank_of(["DOG"], "CAT") is None
    assert curve([0, 1, None, 2], 3) == [0.25, 0.5, 0.75]
