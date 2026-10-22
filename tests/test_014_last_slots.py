"""Brief 014: persistent re-proposal stops under each condition, never
re-proposes a committed slot; shared parameters; reserve disjoint."""

from __future__ import annotations

import json
import pathlib

import pytest

from ximenes.e2e import CFG as E2E
from ximenes.last_slots import CFG, PersistentFrontier


def _fake(seen: list[str]):
    from test_013_e2e import _list_fake

    from ximenes.instruments import PROPOSE_PATTERN

    inner = _list_fake()

    def call(instrument: str, model: str, inp: dict) -> tuple[object, dict]:
        if instrument == PROPOSE_PATTERN:
            seen.append(inp["clue_text"])
        return inner(instrument, model, inp)

    return call


def _run(seen: list[str]) -> PersistentFrontier:
    from test_005_voc import FIX, MODELS

    from ximenes.gridsolve import load_grid
    from ximenes.instruments import metered
    from ximenes.policy import load_tables

    grid, clues = load_grid(FIX / "grid5" / "synthetic-grid5.json")
    backend, totals = metered(_fake(seen))
    return PersistentFrontier("grid5", grid, clues, backend, totals, load_tables(),
                              MODELS, proposer=E2E["proposer"])


def test_stops_on_budget() -> None:
    seen: list[str] = []
    g = _run(seen)
    assert g.persist(0.0) in ("budget", "all_committed") and not seen


def test_stops_when_passes_add_nothing_and_skips_committed() -> None:
    seen: list[str] = []
    g = _run(seen)
    committed = set(g.commits)
    assert g.persist(float("inf")) in ("no_new_candidates", "all_committed")
    texts = {g.s[k].clue.text for k in committed}
    assert not texts & set(seen)  # committed slots are never re-proposed


def test_stops_when_everything_is_committed() -> None:
    seen: list[str] = []
    g = _run(seen)
    g.commits = {k: s.votes[0][0] for k, s in g.s.items() if s.votes}
    assert g.persist(float("inf")) == "all_committed" and not seen


def test_both_policies_share_budget_and_stopping_parameters() -> None:
    docs = [json.loads(p.read_text())
            for p in sorted(pathlib.Path("runs").glob("*-last-slots-*-anthropic-*.json"))]
    arms = [[d for d in docs if d["policy"] == p and len(d["grids"]) == CFG["eval_grids"]]
            for p in CFG["arms"]]
    if not all(arms):
        pytest.skip("no paired run here")
    last = [a[-1] for a in arms]
    assert all(d["params"] == CFG for d in last)
    assert {g["budget"] for d in last for g in d["grids"]} == {CFG["budget_usd"]}


def test_reserve_is_disjoint_from_013() -> None:
    from ximenes.e2e import grids, split
    from ximenes.last_slots import reserve_split

    keep = grids()[0]
    if not keep:
        pytest.skip("no post-cutoff grids here")
    s, r = split(keep), set(reserve_split())
    assert len(r) == CFG["eval_grids"]
    assert not r & set(s["evaluation"]) and not r & set(s["fit"])
