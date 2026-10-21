"""Typed loaders for Cryptonite and the wordplay sample (brief 000).

Rows are frozen dataclasses. The Cryptonite loader verifies the split against
`data/cryptonite/SPLITS.sha256` before reading a line (DESIGN D7).
"""

from __future__ import annotations

import functools
import hashlib
import json
import pathlib
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from .clue import Enumeration, Orientation, split_clue

DATA = pathlib.Path(__file__).resolve().parent.parent.parent / "data"
CRYPTONITE = DATA / "cryptonite"
WORDPLAY = DATA / "wordplay"
SPLITS = ("train", "val", "test")
_EPOCH = datetime.fromtimestamp(0, UTC)


class SplitHashMismatch(ValueError):
    """A split file's sha256 differs from the frozen value in SPLITS.sha256."""


@dataclass(frozen=True)
class CryptoniteClue:
    publisher: str
    date: date
    author: str | None
    number: int
    orientation: Orientation
    text: str
    enumeration: Enumeration
    answer: str
    is_quick: bool
    sub_publisher: str | None


@dataclass(frozen=True)
class WordplayExample:
    clue: str  # definition marked with {}
    pattern: str
    orientation: Orientation
    answer: str
    wordplay: str
    author: str
    setter: str
    publication: str
    is_quick: bool
    num: int
    comment: str | None = None


def format_enumeration(e: Enumeration) -> str:
    """Inverse of `clue.parse_enumeration`: (4,3) with a hyphen before 3 -> '4-3'."""
    seps = ("-" if h else "," for h in e.hyphens)
    head, *tail = (str(p) for p in e.parts)
    return head + "".join(s + p for s, p in zip(seps, tail, strict=True))


def _ms_to_date(ms: int) -> date:
    return (_EPOCH + timedelta(milliseconds=ms)).date()


def parse_cryptonite(row: dict[str, Any]) -> CryptoniteClue:
    text, enum = split_clue(row["clue"])
    return CryptoniteClue(
        publisher=row["publisher"],
        date=_ms_to_date(row["date"]),
        author=row["author"],
        number=row["number"],
        orientation=Orientation(row["orientation"]),
        text=text,
        enumeration=enum,
        answer=row["answer"],
        is_quick=row["quick"],
        sub_publisher=row["sub_publisher"],
    )


def _jsonl(path: pathlib.Path) -> Iterator[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        yield from (json.loads(line) for line in f if line.strip())


def read_cryptonite(path: pathlib.Path) -> tuple[CryptoniteClue, ...]:
    """Parse a Cryptonite-format JSONL file. No hash check: for fixtures only."""
    return tuple(map(parse_cryptonite, _jsonl(path)))


def frozen_hashes(root: pathlib.Path = CRYPTONITE) -> dict[str, str]:
    lines = (root / "SPLITS.sha256").read_text().splitlines()
    pairs = (line.split() for line in lines if line.strip())
    return {name: digest for digest, name in pairs}


def sha256(path: pathlib.Path) -> str:
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def verify_split(split: str, root: pathlib.Path = CRYPTONITE) -> pathlib.Path:
    name = f"cryptonite-{split}.jsonl"
    expected = frozen_hashes(root).get(name)
    if expected is None:
        raise SplitHashMismatch(f"{name}: no frozen hash in {root / 'SPLITS.sha256'}")
    path = root / name
    actual = sha256(path)
    if actual != expected:
        raise SplitHashMismatch(f"{name}: sha256 {actual} != frozen {expected}")
    return path


def load_cryptonite(split: str, root: pathlib.Path = CRYPTONITE) -> tuple[CryptoniteClue, ...]:
    """Load a published split after verifying its frozen hash; raises on mismatch."""
    if split not in SPLITS:
        raise ValueError(f"unknown split {split!r}; expected one of {SPLITS}")
    return read_cryptonite(verify_split(split, root))


_AD = {"A": Orientation.ACROSS, "D": Orientation.DOWN}


def parse_wordplay(row: dict[str, Any]) -> WordplayExample:
    return WordplayExample(
        clue=row["clue"],
        pattern=row["pattern"],
        orientation=_AD.get(row["ad"], Orientation.UNKNOWN),
        answer=row["answer"],
        wordplay=row["wordplay"],
        author=row["author"],
        setter=row["setter"],
        publication=row["publication"],
        is_quick=row["is_quick"],
        num=row["num"],
        comment=row.get("comment"),
    )


def load_wordplay(split: str, root: pathlib.Path = WORDPLAY) -> tuple[WordplayExample, ...]:
    """The teacow sample: split is 'train' or 'val'."""
    return tuple(map(parse_wordplay, _jsonl(root / f"sample_teacow_{split}.jsonl")))


def load_wordplay_answers(split: str, root: pathlib.Path = WORDPLAY) -> frozenset[str]:
    """`cryptonite.{val,test}.txt`: the answer list for a Cryptonite split."""
    lines: Iterable[str] = (root / f"cryptonite.{split}.txt").read_text().splitlines()
    return frozenset(line.strip() for line in lines if line.strip())


LEXICON = DATA / "lexicon"


@functools.cache
def indicators() -> dict[str, frozenset[str]]:
    """{operator: indicator phrases}, from data/lexicon/indicators.json."""
    raw = json.loads((LEXICON / "indicators.json").read_text())
    return {op: frozenset(v) for op, v in raw.items() if op != "source"}


@functools.cache
def abbreviations() -> dict[str, frozenset[str]]:
    """{phrase: abbreviations}, from data/lexicon/abbreviations.json."""
    raw = json.loads((LEXICON / "abbreviations.json").read_text())
    return {k: frozenset(v) for k, v in raw.items() if k != "source" and not k.startswith("_")}
