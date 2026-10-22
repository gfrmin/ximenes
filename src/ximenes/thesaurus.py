"""Brief 008: synonym attestation from published thesauri (Moby, Open English
WordNet). Evidence, not proof: an attested synonym stays Quarantine(synonym)
under DESIGN D4. Pure lookups over indexes loaded by ximenes.data.
"""

from __future__ import annotations

from dataclasses import dataclass

from .data import Thesauri, letters

DIRECT, TWO_HOP = "direct", "2-hop"


@dataclass(frozen=True)
class Attestation:
    sources: tuple[str, ...]  # which thesauri attest it ("moby", "wordnet")
    relation: str  # the closest relation any source gives: "direct" or "2-hop"


def _moby(th: Thesauri, p: str, v: str) -> str | None:
    lp, lv = th.moby.get(p, frozenset()), th.moby.get(v, frozenset())
    if (p in th.moby_head and th.moby_head[p] in lv) or (v in th.moby_head
                                                         and th.moby_head[v] in lp):
        return DIRECT
    return TWO_HOP if lp & lv else None


def _wordnet(th: Thesauri, p: str, v: str) -> str | None:
    sp, sv = th.wn_synsets.get(p, frozenset()), th.wn_synsets.get(v, frozenset())
    if not sp or not sv:
        return None
    near = sp | frozenset(t for s in sp for t in th.wn_similar.get(s, frozenset()))
    if near & sv:
        return DIRECT
    lemmas_p = frozenset(m for s in sp for m in th.wn_members.get(s, frozenset())) - {p}
    lemmas_v = frozenset(m for s in sv for m in th.wn_members.get(s, frozenset())) - {v}
    return TWO_HOP if lemmas_p & lemmas_v else None


def attest(phrase: str, value: str, th: Thesauri) -> Attestation | None:
    """Is `value` listed as a synonym of the clue `phrase`? Case, spaces and
    punctuation are ignored (DSL values carry no spaces)."""
    p, v = letters(phrase), letters(value)
    if not p or not v or p == v:
        return None
    pairs = [(p, v)]
    if p.endswith("s") and v.endswith("s"):  # both plural: also try the singulars
        pairs.append((p[:-1], v[:-1]))
    found: dict[str, str] = {}
    for a, b in pairs:
        for name, rel in (("moby", _moby(th, a, b)), ("wordnet", _wordnet(th, a, b))):
            if rel and (found.get(name) != DIRECT):
                found[name] = rel
    if not found:
        return None
    rel = DIRECT if DIRECT in found.values() else TWO_HOP
    return Attestation(tuple(sorted(found)), rel)


def attach(record: dict[str, object], th: Thesauri) -> dict[str, object]:
    """A Hyp record with attestation added to each synonym leaf (in
    prov.oracle_calls and scores.leaves). Status and everything else unchanged."""
    import copy

    out = copy.deepcopy(record)
    calls = out["prov"]["oracle_calls"]  # type: ignore[index]
    leaves = out["scores"]["leaves"]  # type: ignore[index]
    for call, leaf in zip(calls, leaves, strict=True):
        if call["reason"] == "synonym":
            a = attest(call["phrase"], call["value"], th)
            att = None if a is None else {"sources": list(a.sources), "relation": a.relation}
            call["attested"] = att
            leaf["attested"] = att
    return out
