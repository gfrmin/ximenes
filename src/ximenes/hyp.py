"""The hypothesis relation (docs/GAME.md §5), as a stable record schema.

One `Hyp` row per (slot, candidate answer). `solve` writes them, `decide` and
`posterior` read them. No cells and no propagation yet (brief 004).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any

from .verdict import Reject, Verdict


@dataclass(frozen=True)
class Hyp:
    slot: str  # which clue, e.g. "test:4512"
    answer: str  # normalised candidate
    parse_src: str  # the DSL source ("" if none)
    status: str  # "Ok" | "Quarantine" | "none" (no accepted parse)
    reasons: tuple[str, ...]  # typed Quarantine reasons
    # token multiplicities, table hits (table, key, value), oracle calls
    prov: dict[str, Any] = field(default_factory=dict)
    # definition score/status, per-leaf scores, min_score (brief 002's rule),
    # indicator_min (brief 003)
    scores: dict[str, Any] = field(default_factory=dict)
    vote_share: float = 0.0
    candidate_rank: int = 0  # 0 = most-voted candidate
    attempts: int = 0
    rule: str | None = None  # first broken rule, for a Reject
    posterior: float | None = None  # P(correct | features), set by brief 003's model

    def to_record(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def status_of(v: Verdict) -> str:
    return "none" if isinstance(v, Reject) else type(v).__name__


def hyp_of(slot: str, answer: str, src: str, verdict: Verdict, *, vote_share: float,
           rank: int, attempts: int, min_score: float | None,
           indicator_min: float | None) -> Hyp:
    accepted = not isinstance(verdict, Reject)
    leaves = getattr(verdict, "leaves", ())
    return Hyp(
        slot=slot, answer=answer, parse_src=src, status=status_of(verdict),
        reasons=tuple(r.value for r in getattr(verdict, "reasons", ())),
        prov={
            "consumed": [list(c) for c in verdict.provenance.consumed] if accepted else [],
            "table_hits": [list(h) for h in verdict.provenance.table_hits] if accepted else [],
            "oracle_calls": [{"reason": lf.reason.value, "phrase": lf.phrase,
                              "value": lf.value, "score": lf.score,
                              **({"attested": {"sources": list(lf.attested[0]),
                                               "relation": lf.attested[1]}}
                                 if lf.attested else {})} for lf in leaves],
        },
        scores={
            "definition": dataclasses.asdict(verdict.definition) if accepted else None,
            "leaves": [{"reason": lf.reason.value, "score": lf.score} for lf in leaves],
            "min_score": min_score,
            "indicator_min": indicator_min,
        },
        vote_share=vote_share, candidate_rank=rank, attempts=attempts,
        rule=getattr(verdict, "first_broken_rule", None),
    )
