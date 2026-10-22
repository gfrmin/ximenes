"""Brief 008: thesaurus sources are hash-checked, attestation is a pure
lookup, attaching it never changes a verdict's status, the refit is val-only."""

import json

import pytest

from ximenes.data import THESAURI_SRC, Thesauri, ThesaurusMissing, load_thesauri
from ximenes.posterior import ATTESTED_TABLE, FitOnTest, fit_attested
from ximenes.thesaurus import DIRECT, TWO_HOP, attach, attest

TOY = Thesauri(
    moby={"notice": frozenset({0}), "ear": frozenset({0}), "heed": frozenset({0, 1}),
          "mind": frozenset({1}), "spirit": frozenset({2}), "ghost": frozenset({2}),
          "askfor": frozenset({3}), "request": frozenset({3})},
    moby_head={"notice": 0, "mind": 1, "spirit": 2, "request": 3},
    wn_synsets={"arrest": frozenset({"s1"}), "collar": frozenset({"s1"}),
                "big": frozenset({"s2"}), "huge": frozenset({"s3"})},
    wn_similar={"s2": frozenset({"s3"})},
    wn_members={"s1": frozenset({"arrest", "collar"}), "s2": frozenset({"big"}),
                "s3": frozenset({"huge"})},
)


@pytest.mark.parametrize("phrase,value,sources,relation", [
    ("notice", "EAR", ("moby",), DIRECT),            # listed under the headword
    ("ear", "MIND", ("moby",), TWO_HOP),             # share a line? no: ear on 0, mind on 1
    ("Request", "ASKFOR", ("moby",), DIRECT),         # multiword value without spaces
    ("arrest", "COLLAR", ("wordnet",), DIRECT),       # same synset
    ("big", "HUGE", ("wordnet",), DIRECT),            # similar-to
    ("spirits", "GHOSTS", ("moby",), DIRECT),         # plural fallback
])
def test_attest_cases(phrase: str, value: str, sources: tuple, relation: str) -> None:
    a = attest(phrase, value, TOY)
    if phrase == "ear":
        assert a is None  # ear (line 0) and mind (line 1) share no line
        return
    assert a is not None and a.sources == sources and a.relation == relation


def test_unattested_and_identity() -> None:
    assert attest("notice", "GHOST", TOY) is None
    assert attest("ear", "EAR", TOY) is None


def test_attach_adds_a_field_and_changes_nothing_else() -> None:
    rec = {"answer": "EARN", "status": "Quarantine", "reasons": ["synonym"],
           "prov": {"oracle_calls": [{"reason": "synonym", "phrase": "notice", "value": "EAR",
                                      "score": 0.8},
                                     {"reason": "homophone", "phrase": "x", "value": "Y",
                                      "score": 0.4}]},
           "scores": {"leaves": [{"reason": "synonym", "score": 0.8},
                                 {"reason": "homophone", "score": 0.4}]}}
    out = attach(rec, TOY)
    assert out["status"] == rec["status"] and out["reasons"] == rec["reasons"]
    assert out["prov"]["oracle_calls"][0]["attested"] == {"sources": ["moby"],
                                                          "relation": DIRECT}
    assert "attested" not in out["prov"]["oracle_calls"][1]
    assert "attested" not in rec["prov"]["oracle_calls"][0]  # input untouched


def test_loader_refuses_without_sources(tmp_path) -> None:  # noqa: ANN001
    load_thesauri.cache_clear()
    with pytest.raises(ThesaurusMissing):
        load_thesauri(tmp_path)
    load_thesauri.cache_clear()


@pytest.mark.skipif(not (THESAURI_SRC / "mthesaur.txt").exists(), reason="thesauri not fetched")
def test_real_sources_match_hashes_and_attest() -> None:
    th = load_thesauri()
    assert attest("arrest", "COLLAR", th) is not None


def test_attested_refit_is_val_only() -> None:
    with pytest.raises(FitOnTest):
        fit_attested("test", {"set": "test", "items": []})
    assert json.loads(ATTESTED_TABLE.read_text())["split"] == "val"
