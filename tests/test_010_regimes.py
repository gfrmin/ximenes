"""Brief 010: hard vs soft evidence on the 3-slot toy from 004."""

from __future__ import annotations

from itertools import product

from ximenes.bp import (
    Var,
    agree,
    decode,
    exact_marginals,
    hard,
    prior_with_other,
    soft,
    soft_annealed,
    with_floor,
)

F = 0.05
EDGES = [("A", 0, "B", 0), ("A", 2, "C", 0)]  # A[0]=B[0], A[2]=C[0]


def toy(a: list[float], b: list[float], c: list[float]) -> dict[str, Var]:
    return {
        "A": Var(("CAT", "OAT"), prior_with_other(a, F)),
        "B": Var(("CAB", "OAK"), prior_with_other(b, F)),
        "C": Var(("TOE", "RYE"), prior_with_other(c, F)),
    }


def exact_map(vs: dict[str, Var]) -> dict[str, str | None]:
    """Joint MAP over candidates (OTHER excluded) by enumeration."""
    names = list(vs)

    def weight(combo: tuple[int, ...]) -> float:
        val = dict(zip(names, combo, strict=True))
        w = 1.0
        for k in names:
            w *= vs[k].prior[val[k]]
        for a, i, b, j in EDGES:
            w *= agree(vs[a].words[val[a]], i, vs[b].words[val[b]], j)
        return w

    best = max(product(*(range(len(vs[k].words)) for k in names)), key=weight)
    return {k: vs[k].words[x] for k, x in zip(names, best, strict=True)}


def test_soft_equals_exact_on_the_tree() -> None:
    vs = toy([0.5, 0.3], [0.6, 0.3], [0.4, 0.4])
    assert soft(vs, EDGES) == decode(vs, exact_marginals(vs, EDGES)) == exact_map(vs)


def test_hard_equals_soft_when_no_clamp_is_wrong() -> None:
    vs = toy([0.5, 0.3], [0.95, 0.01], [0.6, 0.2])  # gold CAT / CAB / TOE
    assignment, clamped = hard(vs, EDGES, 0.9)
    assert clamped and assignment == {"A": "CAT", "B": "CAB", "C": "TOE"}
    assert assignment == soft(vs, EDGES) == exact_map(vs)


def test_a_wrong_clamp_costs_hard_a_slot_soft_keeps() -> None:
    # gold CAT / CAB / TOE. B's marginal on OAK passes 0.9, so hard clamps it and
    # A must start with O; soft keeps B's OTHER mass, which leaves CAT ahead.
    vs = toy([0.3, 0.005], [0.001, 0.97], [0.5, 0.4])
    assignment, clamped = hard(vs, EDGES, 0.9)
    assert clamped == frozenset({"B"}) and assignment["B"] == "OAK"
    assert assignment["A"] == "OAT"
    s = soft(vs, EDGES)
    assert s["A"] == "CAT" and s == decode(vs, exact_marginals(vs, EDGES))


def test_regimes_are_pure() -> None:
    vs = toy([0.3, 0.005], [0.001, 0.97], [0.5, 0.4])
    before = dict(vs)
    assert hard(vs, EDGES, 0.9) == hard(vs, EDGES, 0.9)
    assert soft(vs, EDGES) == soft(vs, EDGES)
    priors = {k: (v.words, v.prior) for k, v in vs.items()}
    floors = (0.05, 0.02, 0.01)
    assert soft_annealed(priors, EDGES, floors) == soft_annealed(priors, EDGES, floors)
    assert vs == before


def test_with_floor_raises_other_only() -> None:
    p = with_floor((0.6, 0.38, 0.02), 0.05)
    assert abs(sum(p) - 1) < 1e-12 and p[-1] == 0.05
    assert abs(p[0] / p[1] - 0.6 / 0.38) < 1e-12
    assert with_floor((0.5, 0.2, 0.3), 0.05) == (0.5, 0.2, 0.3)
