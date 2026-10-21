"""Brief 002: the new mechanical operators, property-tested with random fodder;
each tampered result is Rejected. Indicators used here are hand-listed."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ximenes.clue import Clue, Enumeration, normalise
from ximenes.mutants import false_accept, mutants
from ximenes.verdict import Ok, Quarantine, Reject
from ximenes.verify import verify

WORD = st.text(alphabet="bcdfghjklmnpqrstvwxyz", min_size=3, max_size=7)
WORDS = st.lists(WORD, min_size=3, max_size=3, unique=True)


def clue_of(words: list[str], answer: str) -> Clue:
    return Clue(" ".join(words), Enumeration((len(normalise(answer)),), ()))


def accepted(v: object) -> bool:
    return isinstance(v, Ok | Quarantine)


def check(words: list[str], answer: str, src: str) -> None:
    clue = clue_of(words, answer)
    v = verify(clue, answer, src)
    assert isinstance(v, Ok), (src, v)  # hand indicators + lit fodder: fully mechanical
    trials = [(k, verify(clue, a, s)) for k, a, s in mutants(words[0], answer, src)]
    assert trials and not [k for k, t in trials if false_accept(k, t)]


@settings(max_examples=40, deadline=None)
@given(WORDS)
def test_first_and_last_letters(w: list[str]) -> None:
    first = normalise(w[1][0] + w[2][0])
    check([w[0], "initially", w[1], w[2]], first,
          f'clue(defn(tok("{w[0]}")), first_letters(tok("initially"), tok("{w[1]}", "{w[2]}")))')
    last = normalise(w[1][-1] + w[2][-1])
    check([w[0], "finally", w[1], w[2]], last,
          f'clue(defn(tok("{w[0]}")), last_letters(tok("finally"), tok("{w[1]}", "{w[2]}")))')


@settings(max_examples=40, deadline=None)
@given(WORDS)
def test_outer_letters_and_strip_outer(w: list[str]) -> None:
    f = normalise(w[2])
    check([w[0], "outside", w[2]], f[0] + f[-1],
          f'clue(defn(tok("{w[0]}")), outer_letters(tok("outside"), lit(tok("{w[2]}"))))')
    check([w[0], "shelled", w[2]], f[1:-1],
          f'clue(defn(tok("{w[0]}")), strip_outer(tok("shelled"), lit(tok("{w[2]}"))))')


@settings(max_examples=40, deadline=None)
@given(WORDS, st.data())
def test_middle_letters(w: list[str], data: st.DataObject) -> None:
    f = normalise(w[1] + w[2])
    k = data.draw(st.integers(1, (len(f) - 1) // 2))
    mid = f[k:len(f) - k]
    words = [w[0], "heart", "of", w[1], w[2]]
    src = (f'clue(defn(tok("{w[0]}")), middle_letters(tok("heart", "of"), '
           f'lit(tok("{w[1]}", "{w[2]}")), "{mid}"))')
    check(words, mid, src)
    off = f[k:len(f) - k - 1] if len(mid) > 1 else None
    if off:  # not centred
        bad = src.replace(f'"{mid}"', f'"{off}"')
        assert isinstance(verify(clue_of(words, off), off, bad), Reject)


@settings(max_examples=40, deadline=None)
@given(WORDS)
def test_remove(w: list[str]) -> None:
    # the removed word appears twice in the clue: once in the fodder, once alone
    result = normalise(w[1])
    words = [w[0], "without", w[1], w[2], w[2]]
    src = (f'clue(defn(tok("{w[0]}")), remove(tok("without"), lit(tok("{w[1]}", "{w[2]}")), '
           f'lit(tok("{w[2]}")), "{result}"))')
    check(words, result, src)


def test_remove_accepts_any_occurrence_and_nothing_else() -> None:
    words = ["d", "without", "total", "t"]
    src = 'clue(defn(tok("d")), remove(tok("without"), lit(tok("total")), lit(tok("t")), "{}"))'
    for result in ("OTAL", "TOAL"):  # [T]OTAL and TO[T]AL
        assert isinstance(verify(clue_of(words, result), result, src.format(result)), Ok)
    assert isinstance(verify(clue_of(words, "tota"), "tota", src.format("TOTA")), Reject)


@pytest.mark.parametrize("which,expect", [("first", "PO"), ("second", "ND")])
def test_half(which: str, expect: str) -> None:
    words = ["x", "half", "pond"]
    src = f'clue(defn(tok("x")), half(tok("half"), lit(tok("pond")), "{which}"))'
    assert isinstance(verify(clue_of(words, expect), expect, src), Ok)


def test_half_needs_even_length_and_a_named_half() -> None:
    words = ["x", "half", "ponds"]
    src = 'clue(defn(tok("x")), half(tok("half"), lit(tok("ponds")), "first"))'
    assert isinstance(verify(clue_of(words, "po"), "po", src), Reject)
    src = 'clue(defn(tok("x")), half(tok("half"), lit(tok("pond")), "middle"))'
    v = verify(clue_of(["x", "half", "pond"], "po"), "po", src)
    assert isinstance(v, Reject) and v.first_broken_rule == "half:claim"
