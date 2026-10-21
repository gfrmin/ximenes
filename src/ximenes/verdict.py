"""The three verdicts (DESIGN D4). Nothing else may be returned by verify()."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Reason(Enum):
    """Typed Quarantine reasons: which oracle the parse rests on."""

    SYNONYM = "synonym"
    DEFINITION = "definition"
    HOMOPHONE = "homophone"
    CRYPTIC_DEF = "cryptic_def"
    DOUBLE_DEF = "double_def"
    INDICATOR = "indicator"  # indicator phrase not in data/lexicon/indicators.json
    RESIDUAL = "residual"  # declared leftover tokens (only under a declared mode)


@dataclass(frozen=True)
class Provenance:
    """N[X] multiset of consumed token ids, plus declared link/defn tokens."""

    consumed: tuple[tuple[int, int], ...]  # (token_id, multiplicity), sorted
    links: frozenset[int]
    definition: frozenset[int]

    def multiplicity(self, token_id: int) -> int:
        return dict(self.consumed).get(token_id, 0)


@dataclass(frozen=True)
class Ok:
    answer: str
    provenance: Provenance


@dataclass(frozen=True)
class Quarantine:
    answer: str
    provenance: Provenance
    reasons: tuple[Reason, ...]
    oracle_scores: tuple[tuple[str, float], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Reject:
    first_broken_rule: str  # e.g. "surface:If", "coverage:unused:3", "arity:insert"
    hint: str = ""  # proposer-facing, Andrews & Witteveen style


Verdict = Ok | Quarantine | Reject
