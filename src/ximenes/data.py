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


def frozen_hashes(root: pathlib.Path = CRYPTONITE, name: str = "SPLITS.sha256"
                  ) -> dict[str, str]:
    lines = (root / name).read_text().splitlines()
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


TRUSTED_ORIGINS = frozenset({"hand", "review"})


def _trusted(origin: str) -> bool:
    return bool(TRUSTED_ORIGINS & set(origin.split("+")))


@functools.cache
def indicator_trust() -> dict[str, dict[str, bool]]:
    """{operator: {phrase: reviewed or hand-written?}} (DESIGN D4)."""
    raw = json.loads((LEXICON / "indicators.json").read_text())["_origin"]
    return {op: {p: _trusted(o) for p, o in d.items()} for op, d in raw.items()}


ABBREVIATION_FILES = ("abbreviations.json", "abbreviations.wikipedia.json")


@functools.cache
def abbreviation_origins() -> dict[str, dict[str, str]]:
    """{phrase: {VALUE: origin}} merged over the abbreviation files (brief 010:
    the CC BY-SA Wikipedia entries live in their own file); origins union."""
    merged: dict[str, dict[str, set[str]]] = {}
    for name in ABBREVIATION_FILES:
        path = LEXICON / name
        if path.exists():
            for k, d in json.loads(path.read_text())["_origin"].items():
                for v, o in d.items():
                    merged.setdefault(k, {}).setdefault(v, set()).update(o.split("+"))
    return {k: {v: "+".join(sorted(o)) for v, o in d.items()} for k, d in merged.items()}


@functools.cache
def abbreviation_trust() -> dict[str, dict[str, bool]]:
    """{phrase: {VALUE: reviewed or hand-written?}} (DESIGN D4)."""
    return {k: {v: _trusted(o) for v, o in d.items()}
            for k, d in abbreviation_origins().items()}


@functools.cache
def indicators() -> dict[str, frozenset[str]]:
    """{operator: indicator phrases}, from data/lexicon/indicators.json."""
    raw = json.loads((LEXICON / "indicators.json").read_text())
    return {op: frozenset(v) for op, v in raw.items() if op != "source" and not op.startswith("_")}


@functools.cache
def abbreviations() -> dict[str, frozenset[str]]:
    """{phrase: abbreviations}, merged over the abbreviation files."""
    return {k: frozenset(d) for k, d in abbreviation_origins().items()}


@dataclass(frozen=True, order=True)
class PuzzleKey:
    publisher: str
    sub_publisher: str
    date: date
    quick: bool

    @property
    def name(self) -> str:
        return f"{self.publisher}-{self.date.isoformat()}-{'quick' if self.quick else 'cryptic'}"


def load_puzzles(root: pathlib.Path = CRYPTONITE
                 ) -> dict[PuzzleKey, list[tuple[str, dict[str, Any]]]]:
    """Every Cryptonite clue, grouped by puzzle across the three splits (a
    puzzle's clues are spread over train/val/test), as (split, raw row)."""
    out: dict[PuzzleKey, list[tuple[str, dict[str, Any]]]] = {}
    for split in SPLITS:
        for r in _jsonl(verify_split(split, root)):
            key = PuzzleKey(r["publisher"], r["sub_publisher"] or "", _ms_to_date(r["date"]),
                            r["quick"])
            out.setdefault(key, []).append((split, r))
    return out


# --- brief 008: thesauri ---------------------------------------------------------------

THESAURI = DATA / "thesauri"
THESAURI_SRC = DATA / ".src" / "thesauri"


class ThesaurusMissing(FileNotFoundError):
    """The thesaurus sources are absent or do not match their hashes."""


@dataclass(frozen=True)
class Thesauri:
    """Indexes over the two sources, keyed by letters-only lowercase forms.
    moby: word -> ids of the Moby lines it appears on (its own headword line
    included); moby_head: headword -> its line id. wn_synsets: lemma ->
    synset ids; wn_similar: synset -> similar-to synsets; wn_members: synset ->
    member lemmas."""

    moby: dict[str, frozenset[int]]
    moby_head: dict[str, int]
    wn_synsets: dict[str, frozenset[str]]
    wn_similar: dict[str, frozenset[str]]
    wn_members: dict[str, frozenset[str]]


def letters(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalpha())


@functools.cache
def load_thesauri(root: pathlib.Path = THESAURI_SRC) -> Thesauri:
    import gzip
    import xml.etree.ElementTree as ET

    hashes = frozen_hashes(THESAURI, "SOURCES.sha256")
    for name, digest in hashes.items():
        path = root / name
        if not path.exists() or sha256(path) != digest:
            raise ThesaurusMissing(f"{path}: missing or not matching data/thesauri/SOURCES.sha256"
                                   " (run ./setup.sh)")
    moby: dict[str, set[int]] = {}
    head: dict[str, int] = {}
    with open(root / "mthesaur.txt", encoding="latin-1") as f:
        for i, line in enumerate(f):
            words = [letters(w) for w in line.strip().split(",") if letters(w)]
            if words:
                head.setdefault(words[0], i)
                for w in words:
                    moby.setdefault(w, set()).add(i)
    synsets: dict[str, set[str]] = {}
    members: dict[str, set[str]] = {}
    similar: dict[str, set[str]] = {}
    with gzip.open(root / "english-wordnet-2025.xml.gz", "rb") as f:
        entry_lemma = ""
        synset_id = ""
        for _event, el in ET.iterparse(f, events=("start",)):
            tag = el.tag
            if tag == "LexicalEntry":
                entry_lemma = ""
            elif tag == "Lemma":
                entry_lemma = letters(el.get("writtenForm", ""))
            elif tag == "Sense" and entry_lemma:
                s = el.get("synset", "")
                synsets.setdefault(entry_lemma, set()).add(s)
                members.setdefault(s, set()).add(entry_lemma)
            elif tag == "Synset":
                synset_id = el.get("id", "")
            elif tag == "SynsetRelation" and el.get("relType") == "similar" and synset_id:
                similar.setdefault(synset_id, set()).add(el.get("target", ""))
    return Thesauri(
        {k: frozenset(v) for k, v in moby.items()}, head,
        {k: frozenset(v) for k, v in synsets.items()},
        {k: frozenset(v) for k, v in similar.items()},
        {k: frozenset(v) for k, v in members.items()},
    )
