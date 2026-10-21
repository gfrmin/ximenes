"""Brief 000 / DESIGN D7: only ximenes.eval may open data/postcutoff/."""

import pathlib

import pytest

import ximenes
from ximenes.eval import load_postcutoff

PKG = pathlib.Path(ximenes.__file__).parent


def test_only_eval_mentions_postcutoff() -> None:
    hits = sorted(p.name for p in PKG.rglob("*.py") if "postcutoff" in p.read_text())
    assert hits == ["eval.py"]


def test_postcutoff_needs_explicit_permission() -> None:
    with pytest.raises(PermissionError):
        load_postcutoff()
