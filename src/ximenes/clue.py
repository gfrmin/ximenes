"""Clue and token types. Frozen; no behaviour beyond construction/normalisation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Orientation(Enum):
    ACROSS = "across"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Token:
    """One surface word of the clue, with a stable id (its position)."""

    id: int
    text: str  # as written, punctuation stripped, case preserved

    @property
    def key(self) -> str:
        return self.text.lower()


@dataclass(frozen=True)
class Enumeration:
    parts: tuple[int, ...]
    hyphens: tuple[bool, ...]  # hyphen before part i (i >= 1)

    @property
    def length(self) -> int:
        return sum(self.parts)

    def matches(self, answer: str) -> bool:
        return len(normalise(answer)) == self.length


@dataclass(frozen=True)
class Clue:
    text: str
    enumeration: Enumeration
    orientation: Orientation = Orientation.UNKNOWN
    crossers: str | None = None  # pattern like "S?A?F" or None

    @property
    def tokens(self) -> tuple[Token, ...]:
        words = _WORD.findall(self.text)
        return tuple(Token(i, w) for i, w in enumerate(words))


_WORD = re.compile(r"[A-Za-z][A-Za-z'’]*")
_ENUM = re.compile(r"\((\d+(?:[,\-]\d+)*)\)\s*$")


def normalise(s: str) -> str:
    """Answer normalisation: uppercase letters only."""
    return re.sub(r"[^A-Z]", "", s.upper())


def parse_enumeration(raw: str) -> Enumeration:
    """'5' -> (5,); '4,3' -> (4,3); '3-4' -> (3,4) with a hyphen."""
    parts: list[int] = []
    hyphens: list[bool] = []
    for m in re.finditer(r"([,\-]?)(\d+)", raw.strip()):
        sep, n = m.group(1), int(m.group(2))
        parts.append(n)
        if parts and len(parts) > 1:
            hyphens.append(sep == "-")
    return Enumeration(tuple(parts), tuple(hyphens))


def split_clue(raw: str) -> tuple[str, Enumeration]:
    """Separate trailing enumeration from clue text."""
    m = _ENUM.search(raw)
    if not m:
        raise ValueError(f"no enumeration in: {raw!r}")
    return raw[: m.start()].strip(), parse_enumeration(m.group(1))
