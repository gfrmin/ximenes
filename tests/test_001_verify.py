"""Brief 001: the verifier's stages 2-5, operator properties, coverage law,
and the mutation suite on known-good parses."""

import random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ximenes.clue import Clue, Enumeration, normalise
from ximenes.data import abbreviations
from ximenes.mutants import false_accept, mutants
from ximenes.prompts import FORMALISE_EXAMPLES
from ximenes.verdict import Ok, Quarantine, Reason, Reject
from ximenes.verify import verify


def clue_of(words: list[str], answer: str) -> Clue:
    return Clue(" ".join(words), Enumeration((len(normalise(answer)),), ()))


def accepted(v: object) -> bool:
    return isinstance(v, Ok | Quarantine)


# --- coverage law ------------------------------------------------------------

LISTEN = ["listen", "to", "broken", "tinsel"]
GOOD = 'clue(defn(tok("listen")), anagram(tok("broken"), lit(tok("tinsel")), "LISTEN"), ' \
       'link(tok("to")))'


def test_good_parse_is_quarantined_on_its_definition() -> None:
    v = verify(clue_of(LISTEN, "listen"), "listen", GOOD)
    assert isinstance(v, Quarantine) and v.reasons == (Reason.DEFINITION,)
    assert v.provenance.consumed == ((0, 1), (1, 1), (2, 1), (3, 1))


def test_leftover_token_is_rejected() -> None:
    src = 'clue(defn(tok("listen")), anagram(tok("broken"), lit(tok("tinsel")), "LISTEN"))'
    v = verify(clue_of(LISTEN, "listen"), "listen", src)
    assert isinstance(v, Reject) and v.first_broken_rule == "coverage:unused:1:to"


def test_token_used_twice_is_rejected() -> None:
    words = ["red", "and", "red"]
    once = 'clue(defn(tok("red")), lit(tok("red")), link(tok("and")))'
    assert accepted(verify(clue_of(words, "red"), "red", once))
    twice = 'clue(defn(tok("red")), lit(tok("red")), link(tok("and")), link(tok("red")))'
    assert isinstance(verify(clue_of(words, "red"), "red", twice), Reject)


def test_double_duty_allows_exactly_two_uses() -> None:
    words = ["cat", "x"]
    twice = 'clue(defn(tok("cat")), concat(lit(tok("cat")), syn(tok("x"), "S")))'
    assert isinstance(verify(clue_of(words, "cats"), "cats", twice), Reject)
    declared = twice[:-1] + ', double_duty(tok("cat")))'
    assert accepted(verify(clue_of(words, "cats"), "cats", declared))
    thrice = 'clue(defn(tok("cat")), concat(lit(tok("cat")), lit(tok("cat")), ' \
             'syn(tok("x"), "S")), double_duty(tok("cat")))'
    v = verify(clue_of(words, "catcats"), "catcats", thrice)
    assert isinstance(v, Reject) and v.first_broken_rule.startswith("coverage:reused:0")


def test_claim_cannot_be_fodder() -> None:
    src = 'clue(defn(tok("listen")), anagram(tok("broken"), "TINSEL", "LISTEN"), ' \
          'link(tok("to")), link(tok("tinsel")))'
    v = verify(clue_of(LISTEN, "listen"), "listen", src)
    assert isinstance(v, Reject) and v.first_broken_rule.startswith("sort:anagram:arg1")


def test_top_level_must_be_a_clue_form() -> None:
    v = verify(clue_of(["tinsel"], "tinsel"), "tinsel", 'lit(tok("tinsel"))')
    assert isinstance(v, Reject) and v.first_broken_rule == "sort:top:lit"


def test_defn_only_as_first_argument_of_clue() -> None:
    src = 'clue(defn(tok("a")), concat(defn(tok("b")), lit(tok("c"))))'
    v = verify(clue_of(["a", "b", "c"], "c"), "c", src)
    assert isinstance(v, Reject) and v.first_broken_rule == "sort:defn:placement"


def test_wrong_answer_is_rejected_even_when_wordplay_works() -> None:
    v = verify(clue_of(LISTEN, "enlist"), "enlist", GOOD.replace('"LISTEN"', '"ENLIST"'))
    assert accepted(v)  # the definition is an oracle leaf: not checked in brief 001
    v = verify(clue_of(LISTEN, "enlist"), "enlist", GOOD)
    assert isinstance(v, Reject) and v.first_broken_rule == "answer:mismatch"


def test_unknown_indicator_is_quarantined_not_ok() -> None:
    src = GOOD.replace('tok("broken")', 'tok("zzz")')
    v = verify(clue_of(["listen", "to", "zzz", "tinsel"], "listen"), "listen", src)
    assert isinstance(v, Quarantine) and Reason.INDICATOR in v.reasons


def test_abbreviation_must_be_in_the_table() -> None:
    words = ["queen", "x"]
    ok = 'clue(defn(tok("x")), abbr(tok("queen"), "R"))'
    assert accepted(verify(clue_of(words, "r"), "r", ok))
    bad = 'clue(defn(tok("x")), abbr(tok("queen"), "Z"))'
    v = verify(clue_of(words, "z"), "z", bad)
    assert isinstance(v, Reject) and v.first_broken_rule == "abbr:not_in_table"


# --- operator properties (random fodder) ----------------------------------------

WORD = st.text(alphabet="bcdfghjklmnpqrstvwxyz", min_size=3, max_size=7)
WORDS = st.lists(WORD, min_size=3, max_size=3, unique=True)


def _check(words: list[str], answer: str, src: str, tamper: str) -> None:
    clue = clue_of(words, answer)
    assert accepted(verify(clue, answer, src)), (words, answer, src, verify(clue, answer, src))
    assert isinstance(verify(clue, answer, tamper), Reject), tamper


def _bump(s: str) -> str:
    return ("A" if s[0] != "A" else "B") + s[1:]


@settings(max_examples=40, deadline=None)
@given(WORDS)
def test_lit_and_concat(w: list[str]) -> None:
    a = normalise(w[1] + w[2])
    src = f'clue(defn(tok("{w[0]}")), concat(lit(tok("{w[1]}")), lit(tok("{w[2]}"))))'
    _check(w, a, src, src.replace("concat(lit", "concat(syn").replace(
        f'tok("{w[1]}"))', f'tok("{w[1]}"), "{_bump(normalise(w[1]))}")', 1))


@settings(max_examples=40, deadline=None)
@given(WORDS, st.randoms())
def test_anagram(w: list[str], rnd: random.Random) -> None:
    letters = list(normalise(w[2]))
    rnd.shuffle(letters)
    a = "".join(letters)
    words = [w[0], "broken", w[2]]
    src = f'clue(defn(tok("{w[0]}")), anagram(tok("broken"), lit(tok("{w[2]}")), "{a}"))'
    _check(words, a, src, src.replace(f'"{a}"', f'"{_bump(a)}"'))


@settings(max_examples=40, deadline=None)
@given(WORDS)
def test_reverse(w: list[str]) -> None:
    forward = normalise(w[2])
    words = [w[0], "back", w[2]]
    src = f'clue(defn(tok("{w[0]}")), reverse(tok("back"), lit(tok("{w[2]}"))))'
    assert accepted(verify(clue_of(words, forward[::-1]), forward[::-1], src))
    if forward != forward[::-1]:
        assert isinstance(verify(clue_of(words, forward), forward, src), Reject)


@settings(max_examples=40, deadline=None)
@given(WORDS, st.integers(min_value=1, max_value=6))
def test_insert(w: list[str], pos: int) -> None:
    inner, outer = normalise(w[1]), normalise(w[2])
    p = min(pos, len(outer) - 1)
    a = outer[:p] + inner + outer[p:]
    words = [w[0], w[1], "in", w[2]]
    src = (f'clue(defn(tok("{w[0]}")), insert(tok("in"), lit(tok("{w[1]}")), '
           f'lit(tok("{w[2]}")), "{a}"))')
    _check(words, a, src, src.replace(f'"{a}"', f'"{_bump(a)}"'))  # A is in neither word


@settings(max_examples=40, deadline=None)
@given(WORDS, st.data())
def test_hidden(w: list[str], data: st.DataObject) -> None:
    letters = normalise(w[1] + w[2])
    i = data.draw(st.integers(0, len(letters) - 2))
    j = data.draw(st.integers(i + 1, len(letters) - (1 if i == 0 else 0)))
    a = letters[i:j]
    words = [w[0], "some", w[1], w[2]]
    src = f'clue(defn(tok("{w[0]}")), hidden(tok("some"), tok("{w[1]}", "{w[2]}"), "{a}"))'
    _check(words, a, src, src.replace(f'"{a}"', f'"{a}Q"'))


@pytest.mark.parametrize("op,ind,f", [
    ("delete_first", "headless", lambda s: s[1:]),
    ("delete_last", "endless", lambda s: s[:-1]),
    ("delete_middle", "heartless",
     lambda s: s[:len(s) // 2] + s[len(s) // 2 + 1:] if len(s) % 2
     else s[:len(s) // 2 - 1] + s[len(s) // 2 + 1:]),
])
@settings(max_examples=25, deadline=None)
@given(w=WORDS)
def test_deletions(op: str, ind: str, f: object, w: list[str]) -> None:
    a = f(normalise(w[2]))  # type: ignore[operator]
    words = [w[0], ind, w[2]]
    src = f'clue(defn(tok("{w[0]}")), {op}(tok("{ind}"), lit(tok("{w[2]}"))))'
    clue = clue_of(words, a)
    assert accepted(verify(clue, a, src))
    assert isinstance(verify(clue_of(words, normalise(w[2])), normalise(w[2]), src), Reject)


@settings(max_examples=40, deadline=None)
@given(WORDS)
def test_initials_and_alternate(w: list[str]) -> None:
    a = normalise(w[1][0] + w[2][0])
    words = [w[0], "initially", w[1], w[2]]
    src = f'clue(defn(tok("{w[0]}")), initials(tok("initially"), tok("{w[1]}", "{w[2]}")))'
    _check(words, a, src, src.replace("initials(", "alternate(").replace("initially", "oddly"))
    letters = normalise(w[1] + w[2])
    odd = letters[::2]
    words = [w[0], "oddly", w[1], w[2]]
    src = f'clue(defn(tok("{w[0]}")), alternate(tok("oddly"), tok("{w[1]}", "{w[2]}")))'
    assert accepted(verify(clue_of(words, odd), odd, src))


@settings(max_examples=40, deadline=None)
@given(WORDS, st.sampled_from(sorted(k for k in abbreviations() if k.isalpha())))
def test_abbr_and_syn(w: list[str], key: str) -> None:
    value = sorted(abbreviations()[key])[0]
    words = [w[0], key]
    src = f'clue(defn(tok("{w[0]}")), abbr(tok("{key}"), "{value}"))'
    clue = clue_of(words, value)
    assert accepted(verify(clue, value, src))
    syn = verify(clue, value, src.replace("abbr(", "syn("))
    assert isinstance(syn, Quarantine) and Reason.SYNONYM in syn.reasons


@settings(max_examples=25, deadline=None)
@given(WORDS)
def test_oracle_forms(w: list[str]) -> None:
    a = normalise(w[1])
    dd = verify(clue_of(w[:2], a), a, f'double_def(tok("{w[0]}"), tok("{w[1]}"), "{a}")')
    assert isinstance(dd, Quarantine) and dd.reasons == (Reason.DOUBLE_DEF,)
    cd = verify(clue_of(w, a), a, f'cryptic_def(tok("{w[0]}", "{w[1]}", "{w[2]}"), "{a}")')
    assert isinstance(cd, Quarantine) and cd.reasons == (Reason.CRYPTIC_DEF,)
    words = [w[0], "say", w[1]]
    hp = verify(clue_of(words, a), a, f'clue(defn(tok("{w[0]}")), homophone(tok("say"), '
                                      f'lit(tok("{w[1]}")), "{a}"))')
    assert isinstance(hp, Quarantine) and Reason.HOMOPHONE in hp.reasons


# --- mutation suite on known-good parses ------------------------------------------


def _examples() -> list[tuple[Clue, str, str]]:
    from ximenes.clue import split_clue

    out = []
    for raw, answer, src in FORMALISE_EXAMPLES:
        text, enum = split_clue(raw.replace("{", "").replace("}", ""))
        out.append((Clue(text, enum), answer, src))
    return out


@pytest.mark.parametrize("clue,answer,src", _examples())
def test_prompt_examples_verify(clue: Clue, answer: str, src: str) -> None:
    assert accepted(verify(clue, answer, src))


def test_mutants_of_good_parses_are_all_rejected() -> None:
    trials = [(kind, verify(c, a, s)) for clue, answer, src in _examples()
              for kind, a, s in mutants(clue.tokens[0].text, answer, src)
              for c in (clue,)]
    assert len(trials) >= len(_examples()) * 2
    assert [k for k, v in trials if false_accept(k, v)] == []
    # mechanical mutants are all Rejected outright
    assert all(isinstance(v, Reject) for k, v in trials if k != "oracle_claim")


# --- regressions found by the 30-Reject audit -----------------------------------


def test_stated_answer_is_the_last_fixed_argument_not_a_trailing_link() -> None:
    clue = clue_of(["fights", "for", "waste", "food"], "scraps")
    src = 'double_def(tok("fights"), tok("waste", "food"), "SCRAPS", link(tok("for")))'
    assert isinstance(verify(clue, "scraps", src), Quarantine)
    cd = 'cryptic_def(tok("waste", "food"), "SCRAPS", link(tok("fights")), link(tok("for")))'
    assert isinstance(verify(clue, "scraps", cd), Quarantine)


def test_repeated_word_references_avoid_overlap() -> None:
    clue = clue_of(["bowl", "over", "and", "over", "crazy"], "nuts")
    src = 'clue(defn(tok("crazy")), reverse(tok("over"), syn(tok("bowl", "over"), "STUN")), ' \
          'link(tok("and")))'
    v = verify(clue, "nuts", src)
    assert isinstance(v, Quarantine)
    assert v.provenance.consumed == ((0, 1), (1, 1), (2, 1), (3, 1), (4, 1))
