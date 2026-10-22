"""Brief 009: the Wikipedia list parser, and syn() as a table hit only for
reviewed abbreviation entries."""

import importlib.util
import json

from ximenes.clue import Clue, Enumeration
from ximenes.data import LEXICON, abbreviation_trust
from ximenes.verdict import Ok, Quarantine, Reason
from ximenes.verify import verify

EXCERPT = """Intro text with an example: "six" for <small>VI</small>
==A==
* Aboard – <small>SS</small>, or a word inside the letters <small>SS</small>
* About – <small>C</small> or <small>CA</small> ([[circa]]) or <small>[[wikt:re|RE]]</small>
* Abstainer, teetotaller – <small>TT</small>
==B==
* Bend – <small>S</small> or <small>U</small> (as in "S-bend")
* Ball – <small>O</small>; also 1-0 <small>10</small>
==Further reading==
* Some book – <small>XX</small>
"""


def _parser():
    spec = importlib.util.spec_from_file_location("b", LEXICON / "build_abbreviations.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_wikipedia


def test_parser_reads_the_lettered_sections_only() -> None:
    got = _parser()(EXCERPT)
    assert got == {"aboard": {"SS"}, "about": {"C", "CA", "RE"}, "abstainer": {"TT"},
                   "teetotaller": {"TT"}, "bend": {"S", "U"}, "ball": {"O"}}


def _origin(key: str, value: str) -> str:
    return json.loads((LEXICON / "abbreviations.json").read_text())["_origin"][key][value]


def _clue(words: list[str], answer: str) -> Clue:
    return Clue(" ".join(words), Enumeration((len(answer),), ()))


def test_syn_on_a_reviewed_entry_is_a_mechanical_table_hit() -> None:
    assert abbreviation_trust()["quietly"]["P"] and "wikipedia" in _origin("quietly", "P")
    v = verify(_clue(["fish", "quietly"], "p"), "p",
               'clue(defn(tok("fish")), syn(tok("quietly"), "P"))')
    assert isinstance(v, Ok)
    assert ("abbreviations", "quietly", "P") in v.provenance.table_hits


def test_syn_on_an_unreviewed_entry_stays_a_synonym() -> None:
    trust = abbreviation_trust()
    key, value = next((k, v) for k, d in sorted(trust.items()) for v, ok in sorted(d.items())
                      if not ok and k.isalpha() and _origin(k, v) == "wikipedia")
    v = verify(_clue(["fish", key], value), value,
               f'clue(defn(tok("fish")), syn(tok("{key}"), "{value}"))')
    assert isinstance(v, Quarantine) and Reason.SYNONYM in v.reasons
    w = verify(_clue(["fish", key], value), value,
               f'clue(defn(tok("fish")), abbr(tok("{key}"), "{value}"))')
    assert isinstance(w, Quarantine) and Reason.TABLE_UNREVIEWED in w.reasons


def test_a_non_table_synonym_is_unchanged() -> None:
    v = verify(_clue(["fish", "notice"], "ear"), "ear",
               'clue(defn(tok("fish")), syn(tok("notice"), "EAR"))')
    assert isinstance(v, Quarantine) and v.reasons == (Reason.SYNONYM,)
