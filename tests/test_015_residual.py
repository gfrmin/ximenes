"""Brief 015, A0 and A: statistics, the word-list key, the generators and
their parses through the verifier, the stuck-slot rule, the union arm and
the decision bands."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ximenes.clue import Clue, Orientation, parse_enumeration
from ximenes.data import entry_key
from ximenes.grid import Slot
from ximenes.residual import (
    CFG,
    best_verdict,
    beta_interval,
    decide,
    generated,
    p_greater,
    stuck_of,
    union,
)


def test_beta_helpers() -> None:
    lo, hi = beta_interval(0, 0)  # Beta(1, 1): the uniform
    assert lo == pytest.approx(0.05, abs=1e-9) and hi == pytest.approx(0.95, abs=1e-9)
    assert p_greater(3, 10, 3, 10) == pytest.approx(0.5)
    assert p_greater(8, 10, 2, 10) > 0.99 > 0.01 > p_greater(2, 10, 8, 10)
    # P(Beta(2,1) > Beta(1,1)) = 2/3
    assert p_greater(1, 1, 0, 0) == pytest.approx(2 / 3)


def test_entry_key_splits_words_and_hyphens() -> None:
    assert entry_key("ice cream") == ((3, 5), "ICECREAM")
    assert entry_key("well-to-do") == ((4, 2, 2), "WELLTODO")
    assert entry_key("o'clock") == ((6,), "OCLOCK")
    assert entry_key("  ") is None


def _clue(text: str, enum: str) -> Clue:
    return Clue(text, parse_enumeration(enum))


def test_hidden_word_is_generated_and_admitted() -> None:
    c = _clue("Fruit some deli meshes", "4")
    gen = generated(c, 4, frozenset({"LIME", "PEAR"}))
    assert "LIME" in gen and "PEAR" not in gen
    assert best_verdict(c, "LIME", gen["LIME"]) in ("Ok", "Quarantine")


def test_anagram_is_generated_only_from_the_list_and_admitted() -> None:
    c = _clue("Listen to broken tinsel", "6")
    gen = generated(c, 6, frozenset({"LISTEN", "SILENT", "ENLIST", "TINSEL"}))
    assert {"LISTEN", "SILENT", "ENLIST"} <= set(gen)
    assert best_verdict(c, "SILENT", gen["SILENT"]) in ("Ok", "Quarantine")


def test_reversed_hidden_needs_two_indicator_tokens() -> None:
    c = _clue("Celebrity back in sprat sold", "4")  # RATS inside "sprat sold", reversed
    gen = generated(c, 4, frozenset({"STAR"}))
    assert [how for how, _span in gen["STAR"]] == ["hidden_reversed"]
    assert best_verdict(c, "STAR", gen["STAR"]) in ("Ok", "Quarantine")
    one = _clue("Celebrity back sprat sold", "4")  # one indicator token: no parse
    assert best_verdict(one, "STAR", generated(one, 4, frozenset({"STAR"}))["STAR"]) is None


def test_a_word_without_a_generated_parse_is_not_admitted() -> None:
    c = _clue("Fruit some deli meshes", "4")
    assert best_verdict(c, "PEAR", []) is None


def _slot(text: str, number: int, o: Orientation, cells: tuple) -> SimpleNamespace:
    return SimpleNamespace(clue=SimpleNamespace(text=text), slot=Slot(number, o, cells),
                           votes=[], cands=[])


def test_stuck_excludes_committed_and_ever_proposed() -> None:
    a, d = Orientation.ACROSS, Orientation.DOWN
    g = SimpleNamespace(
        s={"1A": _slot("a", 1, a, ((0, 0), (0, 1))), "1D": _slot("b", 1, d, ((0, 0), (1, 0))),
           "3A": _slot("c", 3, a, ((1, 0), (1, 1)))},
        gold={"1A": "AB", "1D": "AC", "3A": "CD"},
        commits={"1A": "XB"},  # committed wrong: not a stuck slot
    )
    proposed = {"c": {"CD"}}  # 3A's gold was proposed once, then dropped: not stuck
    assert stuck_of(g, proposed) == [("1D", "X?")]


def test_union_averages_shares() -> None:
    a = {"ranked": ["X", "Y"], "shares": [0.6, 0.2]}
    b = {"ranked": ["Z", "Y"], "shares": [0.9, 0.5]}
    u = union(a, b)
    assert u["ranked"] == ["Z", "Y", "X"]
    assert u["shares"] == pytest.approx([0.45, 0.35, 0.3])


def _row(hits: int, n: int, usd: float) -> dict:
    key = f"gold_in_{CFG['top']}"
    return {"n": n, "usd": usd, key: {"hits": hits, "rate": hits / n,
                                      "interval": beta_interval(hits, n)}}


def test_decision_bands() -> None:
    assert decide({"a": _row(12, 17, 1.0), "b": _row(1, 17, 0.0)})["band"] == "run_b"
    assert decide({"a": _row(0, 100, 1.0), "b": _row(1, 100, 0.0)})["band"] == \
        "depth_does_not_reach"
    assert decide({"a": _row(3, 17, 1.0)})["band"] == "report_and_stop"
    # two arms tied within intervals above the bar: the cheaper one goes to B
    assert decide({"a": _row(12, 17, 2.0), "b": _row(11, 17, 0.5)})["arm_for_b"] == "b"
