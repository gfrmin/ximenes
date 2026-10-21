"""Brief 004: loopy belief propagation over the grid's hypothesis relation.

A variable per slot, whose domain is its candidate answers plus OTHER ("a word
we have not proposed"); a factor per crossing cell, 1 when the two letters
agree, and OTHER agrees with any letter. Sum-product gives marginals,
max-product the MAP. Pure functions; no I/O.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import product

from .eval import PARAMS

CFG = PARAMS["bp"]
OTHER = None  # the extra domain value


@dataclass(frozen=True)
class Var:
    words: tuple[str, ...]  # candidate answers (normalised); OTHER is appended implicitly
    prior: tuple[float, ...]  # one per word, plus one for OTHER (sums to 1)

    @property
    def domain(self) -> tuple[str | None, ...]:
        return (*self.words, OTHER)


Edge = tuple[str, int, str, int]  # (slot a, index in a, slot b, index in b)


def prior_with_other(posteriors: Sequence[float], floor_other: float) -> tuple[float, ...]:
    """Candidates' posteriors plus OTHER = max(1 - sum, floor), normalised."""
    other = max(1.0 - sum(posteriors), floor_other)
    total = sum(posteriors) + other
    return (*(p / total for p in posteriors), other / total)


def committed(word: str) -> Var:
    """Hard evidence: a committed slot has one value and no OTHER."""
    return Var((word,), (1.0, 0.0))


def agree(x: str | None, i: int, y: str | None, j: int) -> float:
    return 1.0 if x is None or y is None or x[i] == y[j] else 0.0


def _normalise(v: list[float]) -> list[float]:
    s = sum(v)
    return [x / s for x in v] if s else [1.0 / len(v)] * len(v)


def propagate(variables: Mapping[str, Var], edges: Sequence[Edge], mode: str = "sum"
              ) -> dict[str, list[float]]:
    """Loopy BP. mode "sum": marginals; "max": max-marginals (for the MAP)."""
    combine = sum if mode == "sum" else max
    nbrs: dict[str, list[tuple[str, int, int]]] = {k: [] for k in variables}
    for a, i, b, j in edges:
        nbrs[a].append((b, i, j))
        nbrs[b].append((a, j, i))
    msg = {(a, b): [1.0] * len(variables[b].domain) for a in variables for b, _i, _j in nbrs[a]}

    def belief_without(a: str, skip: str | None) -> list[float]:
        bel = list(variables[a].prior)
        for c, _i, _j in nbrs[a]:
            if c != skip:
                bel = [x * m for x, m in zip(bel, msg[(c, a)], strict=True)]
        return bel

    for _ in range(CFG["max_iters"]):
        delta = 0.0
        new = {}
        for a in variables:
            for b, i, j in nbrs[a]:
                bel = belief_without(a, b)
                out = _normalise([combine(bel[x] * agree(xa, i, xb, j)
                                          for x, xa in enumerate(variables[a].domain))
                                  for xb in variables[b].domain])
                damped = [CFG["damping"] * o + (1 - CFG["damping"]) * m
                          for o, m in zip(out, msg[(a, b)], strict=True)]
                change = max(abs(d - m) for d, m in zip(damped, msg[(a, b)], strict=True))
                delta = max(delta, change)
                new[(a, b)] = damped
        msg = new
        if delta < CFG["tol"]:
            break
    return {a: _normalise(belief_without(a, None)) for a in variables}


def map_assignment(variables: Mapping[str, Var], edges: Sequence[Edge]) -> dict[str, str | None]:
    """Max-product decoding: each slot's value with the highest max-marginal."""
    mm = propagate(variables, edges, mode="max")
    return {a: variables[a].domain[max(range(len(p)), key=lambda x: p[x])] for a, p in mm.items()}


def exact_marginals(variables: Mapping[str, Var], edges: Sequence[Edge]
                    ) -> dict[str, list[float]]:
    """Brute-force marginals by enumeration (for tests on tiny graphs)."""
    names = list(variables)
    totals = {a: [0.0] * len(variables[a].domain) for a in names}
    for combo in product(*(range(len(variables[a].domain)) for a in names)):
        val = dict(zip(names, combo, strict=True))
        w = 1.0
        for a in names:
            w *= variables[a].prior[val[a]]
        for a, i, b, j in edges:
            w *= agree(variables[a].domain[val[a]], i, variables[b].domain[val[b]], j)
        for a in names:
            totals[a][val[a]] += w
    return {a: _normalise(t) for a, t in totals.items()}
