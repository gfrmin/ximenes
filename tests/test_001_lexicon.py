"""Brief 001: the abbreviation table is mechanical, so known-bad upstream
values must stay out (data/lexicon/REVIEW.md)."""

import json
import pathlib

from ximenes.data import LEXICON, abbreviations

LONG_OK = {"greek character", "greek letter", "month", "day", "thursday"}


def test_known_fused_values_are_gone() -> None:
    table = abbreviations()
    fused = {("america", "USUSA"), ("australia", "AUSOZ"), ("church", "CHCERC"),
             ("bishop", "BRR"), ("caught", "CCT"), ("railway", "RYBR"),
             ("versus", "VVS"), ("year", "YYR"), ("one", "RARELY"), ("st", "STONE")}
    assert not {(k, v) for k, v in fused if v in table.get(k, frozenset())}
    assert "deaddied" not in table
    assert "ST" in table["stone"]


def test_values_are_short_letters() -> None:
    bad = {(k, v) for k, vs in abbreviations().items() for v in vs
           if not v.isalpha() or not v.isupper() or (len(v) > 4 and k not in LONG_OK)}
    assert not bad


def test_built_file_matches_build_script() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build_abbreviations", LEXICON / "build_abbreviations.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.build() == json.loads(pathlib.Path(LEXICON / "abbreviations.json").read_text())
