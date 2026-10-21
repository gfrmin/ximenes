"""Brief 000: loaders verify frozen split hashes and return typed rows."""

import hashlib
import json
import pathlib
import shutil
from datetime import date

import pytest

from ximenes.clue import Orientation
from ximenes.data import (
    CRYPTONITE,
    SplitHashMismatch,
    load_cryptonite,
    read_cryptonite,
)

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "clues-20.jsonl"


def _split_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """A temp split dir whose SPLITS.sha256 matches a copy of the fixture as 'val'."""
    root = tmp_path / "cryptonite"
    root.mkdir()
    shutil.copy(FIXTURE, root / "cryptonite-val.jsonl")
    digest = hashlib.sha256((root / "cryptonite-val.jsonl").read_bytes()).hexdigest()
    (root / "SPLITS.sha256").write_text(f"{digest}  cryptonite-val.jsonl\n")
    return root


def test_loader_accepts_matching_hash(tmp_path: pathlib.Path) -> None:
    clues = load_cryptonite("val", _split_dir(tmp_path))
    assert len(clues) == 20


def test_loader_raises_on_hash_mismatch(tmp_path: pathlib.Path) -> None:
    root = _split_dir(tmp_path)
    path = root / "cryptonite-val.jsonl"
    path.write_text(path.read_text().replace("listen", "lusten", 1))
    with pytest.raises(SplitHashMismatch):
        load_cryptonite("val", root)


@pytest.mark.skipif(not (CRYPTONITE / "cryptonite-test.jsonl").exists(),
                    reason="Cryptonite not downloaded (./setup.sh)")
def test_real_split_raises_when_tampered(tmp_path: pathlib.Path) -> None:
    root = tmp_path / "cryptonite"
    root.mkdir()
    shutil.copy(CRYPTONITE / "SPLITS.sha256", root / "SPLITS.sha256")
    shutil.copy(CRYPTONITE / "cryptonite-val.jsonl", root / "cryptonite-val.jsonl")
    with open(root / "cryptonite-val.jsonl", "a") as f:
        f.write("\n")
    with pytest.raises(SplitHashMismatch):
        load_cryptonite("val", root)


def test_row_fields_are_mapped() -> None:
    raw = json.loads(FIXTURE.read_text().splitlines()[0])
    c = read_cryptonite(FIXTURE)[0]
    assert c.text == "listen to broken tinsel"
    assert c.enumeration.parts == (6,)
    assert c.answer == "listen"
    assert c.is_quick is raw["quick"]
    assert isinstance(c.date, date)
    assert c.orientation in (Orientation.ACROSS, Orientation.DOWN)
    with pytest.raises(AttributeError):
        c.answer = "x"  # type: ignore[misc]


def test_epoch_ms_is_parsed_in_utc() -> None:
    from ximenes.data import parse_cryptonite

    row = json.loads(FIXTURE.read_text().splitlines()[0]) | {"date": 971654400000}
    assert parse_cryptonite(row).date == date(2000, 10, 16)
