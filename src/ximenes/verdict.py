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
    TABLE_UNREVIEWED = "table_unreviewed"  # step rests on an unreviewed table entry
    RESIDUAL = "residual"  # declared leftover tokens (only under a declared mode)


@dataclass(frozen=True)
class Provenance:
    """N[X] multiset of consumed token ids, plus declared link/defn tokens and
    the table entries the derivation used, as (table, key, value)."""

    consumed: tuple[tuple[int, int], ...]  # (token_id, multiplicity), sorted
    links: frozenset[int]
    definition: frozenset[int]
    table_hits: tuple[tuple[str, str, str], ...] = ()

    def multiplicity(self, token_id: int) -> int:
        return dict(self.consumed).get(token_id, 0)


@dataclass(frozen=True)
class Definition:
    """The definition channel (DESIGN D4): reported alongside every verdict,
    never folded into its status."""

    span: str = ""  # the clue words declared as definition; "" if none (double/cryptic def)
    status: str = "pending"  # "pending" | "judged"
    score: float | None = None
    oracle: str | None = None  # model id of the judge


@dataclass(frozen=True)
class OracleLeaf:
    """One wordplay step that rests on a judgement, for an oracle to score."""

    reason: Reason
    phrase: str  # the clue words the step consumes
    value: str  # the stated value (synonym value, homophone source, answer)
    result: str  # what the step produced (heard string for a homophone)
    score: float | None = None


@dataclass(frozen=True)
class Ok:
    answer: str
    provenance: Provenance
    definition: Definition = field(default_factory=Definition)


@dataclass(frozen=True)
class Quarantine:
    answer: str
    provenance: Provenance
    reasons: tuple[Reason, ...]
    oracle_scores: tuple[tuple[str, float], ...] = field(default_factory=tuple)
    definition: Definition = field(default_factory=Definition)
    leaves: tuple[OracleLeaf, ...] = ()


@dataclass(frozen=True)
class Reject:
    first_broken_rule: str  # e.g. "surface:If", "coverage:unused:3", "arity:insert"
    hint: str = ""  # proposer-facing, Andrews & Witteveen style


Verdict = Ok | Quarantine | Reject
