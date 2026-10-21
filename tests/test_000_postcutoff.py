"""Brief 000 / DESIGN D7: only ximenes.eval may open data/postcutoff/."""

import json
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


def _row(day: str) -> str:
    from datetime import date as _d

    ms = int((_d.fromisoformat(day) - _d(1970, 1, 1)).total_seconds() * 1000)
    return json.dumps({"publisher": "synthetic", "date": ms, "author": None, "number": 1,
                       "orientation": "across", "clue": "rats back, a celebrity (4)",
                       "answer": "star", "enumeration": "(4)", "quick": False,
                       "sub_publisher": None})


def test_postcutoff_filters_by_floor_and_release_date(tmp_path: pathlib.Path) -> None:
    (tmp_path / "synthetic-1-x.jsonl").write_text(
        "\n".join(_row(d) for d in ("2026-10-01", "2026-10-22", "2026-10-23", "2026-12-01"))
    )
    kept, excluded = load_postcutoff(allow_postcutoff=True, model="m", root=tmp_path,
                                     released={"m": "2026-01-01"})
    assert [str(c.date) for c in kept] == ["2026-10-23", "2026-12-01"] and excluded == 2
    kept, excluded = load_postcutoff(allow_postcutoff=True, model="m", root=tmp_path,
                                     released={"m": "2026-11-15"})
    assert [str(c.date) for c in kept] == ["2026-12-01"] and excluded == 3


def test_postcutoff_needs_a_release_date(tmp_path: pathlib.Path) -> None:
    with pytest.raises(ValueError):
        load_postcutoff(allow_postcutoff=True, model="m", root=tmp_path, released={"m": None})
