"""Brief 013: split, refit refusal, invariants, proposer swap, budget, and
the tables committed before the first evaluation run."""

from __future__ import annotations

import json
import pathlib
import subprocess
from datetime import UTC, datetime

import pytest

from ximenes.e2e import CFG, FitOnEvaluation, refit, row_ok, split


@pytest.mark.parametrize("clue,answer,ok", [
    ("Vehicle beside animal makes rug (6)", "CARPET", True),
    ("Rug (6)", "CARPET", False),                                   # one word
    ("Vehicle beside animal makes rug (5)", "CARPET", False),       # length mismatch
    ("Vehicle (3) beside animal (6)", "CARPET", False),             # inner enumeration
    ("Vehicle beside animal 12a Another clue (6)", "CARPET", False),  # merged clues
    ("No enumeration here", "CARPET", False),
])
def test_row_invariants(clue: str, answer: str, ok: bool) -> None:
    assert row_ok({"clue": clue, "answer": answer}) is ok


def _paths(counts: dict[str, int]) -> list[pathlib.Path]:
    return [pathlib.Path(f"{p}-{i}-2026-09-01.json") for p, n in counts.items()
            for i in range(n)]


def test_split_is_deterministic_disjoint_and_stratified() -> None:
    paths = _paths({"ft": 49, "independent": 41, "guardian": 30})
    a, b = split(paths), split(list(reversed(paths)))
    assert a == b
    ev, fit, res = set(a["evaluation"]), set(a["fit"]), set(a["reserved"])
    assert len(ev) == CFG["eval_grids"] and len(fit) == CFG["fit_grids"]
    assert not (ev & fit or ev & res or fit & res) and len(ev | fit | res) == len(paths)
    by = {p: sum(n.startswith(p + "-") for n in ev) for p in ("ft", "independent", "guardian")}
    assert by == {"ft": 8, "independent": 7, "guardian": 5}
    assert split(paths, CFG["split_seed"] + 1) != a


def test_refit_refuses_a_run_touching_evaluation_grids() -> None:
    run = {"run_id": "r", "grids": [{"puzzle": "ft-1-2026-09-01", "items": [], "events": [],
                                     "proposal_usd": 0.0}]}
    with pytest.raises(FitOnEvaluation):
        refit(run, ["ft-1-2026-09-01"])


def _list_fake():
    from test_005_voc import SAMPLES, fake

    from ximenes.instruments import PROPOSE_LIST

    def call(instrument: str, model: str, inp: dict) -> tuple[object, dict]:
        if instrument == PROPOSE_LIST:
            listed = list(dict.fromkeys(SAMPLES[inp["clue_text"]]))
            return "\n".join(listed), {"usd": 0.01, "seconds": 1.0}
        return fake(instrument, model, inp)

    return call


def _grid(policy: str, budget: float, gain: dict | None = None):
    from test_005_voc import FIX, MODELS

    from ximenes.gridsolve import load_grid
    from ximenes.instruments import metered
    from ximenes.policy import GridRun, load_tables

    grid, clues = load_grid(FIX / "grid5" / "synthetic-grid5.json")
    backend, totals = metered(_list_fake())
    g = GridRun("grid5", grid, clues, backend, totals, load_tables(), MODELS,
                proposer=CFG["proposer"])
    g.run(policy, gain, 0.0, budget)
    return g


def test_round1_list_proposer_ranks_by_position() -> None:
    g = _grid("vote", float("inf"))
    for s in g.s.values():
        shares = [sh for _a, sh in s.votes]
        assert shares == sorted(shares, reverse=True)
        assert not shares or abs(sum(shares) - 1) < 1e-9


def test_voc_never_exceeds_the_budget_by_more_than_one_move() -> None:
    gain = {"kinds": {"solve": {"features": ["top_vote_share"], "weights": [0.1, 1.0],
                                "price_usd": 0.02},
                      "repropose": {"features": ["other_mass"], "weights": [0.1, 1.0],
                                    "price_usd": 0.01}}}
    budget = 0.15
    g = _grid("voc", budget, gain)
    moves = [c["usd"] for c in g.checkpoints]
    steps = [b - a for a, b in zip(moves, moves[1:], strict=False)]
    assert moves[-1] <= budget + max(steps, default=0.0)


def test_tables_committed_before_the_first_evaluation_run() -> None:
    runs = sorted(pathlib.Path("runs").glob("*-e2e-voc-anthropic-*.json"))
    if not runs:
        pytest.skip("no evaluation run yet")
    first_run = datetime.strptime(runs[0].name[:len("20261022T000000Z")],
                                  "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%cI", "--",
                          "data/e2e-posterior.json"], capture_output=True, text=True, check=False)
    if out.returncode or not out.stdout.strip():
        pytest.skip("git history not available")
    added = datetime.fromisoformat(out.stdout.split()[-1])
    assert added < first_run
    assert json.loads(pathlib.Path("data/e2e-posterior.json").read_text())["fit_grids"]


def test_frontier_baseline_uses_no_formaliser_and_respects_budget() -> None:
    from test_005_voc import FIX, MODELS

    from ximenes.e2e import FrontierRun
    from ximenes.gridsolve import load_grid
    from ximenes.instruments import FORMALISE_CLUE, metered
    from ximenes.policy import load_tables

    seen: list[str] = []
    inner = _list_fake()

    def spy(instrument: str, model: str, inp: dict) -> tuple[object, dict]:
        seen.append(instrument)
        return inner(instrument, model, inp)

    grid, clues = load_grid(FIX / "grid5" / "synthetic-grid5.json")
    backend, totals = metered(spy)
    g = FrontierRun("grid5", grid, clues, backend, totals, load_tables(), MODELS,
                    proposer=CFG["proposer"])
    g.frontier(0.08)
    assert FORMALISE_CLUE not in seen and not any(i.startswith("judge") for i in seen)
    assert g.checkpoints[-1]["usd"] <= 0.08 + 0.005 * 2  # at most one move past the budget


def test_replay_reproduces_the_headline_grid() -> None:
    """The evaluation run replays from its log (local only; one grid, the
    smallest, to keep the kit fast)."""
    import argparse

    from ximenes.e2e import e2e_tables, run_grids

    runs = sorted(pathlib.Path("runs").glob("*-e2e-voc-anthropic-*.json"))
    live = [json.loads(r.read_text()) for r in runs]
    live = [d for d in live if len(d["grids"]) == CFG["eval_grids"]]
    if not live:
        pytest.skip("no full evaluation run here")
    run = live[-1]
    g = min(run["grids"], key=lambda g: len(g["checkpoints"]))
    logs = [run["log"], *(str(r.with_suffix(".jsonl")) for r in runs if r.stem not in run["log"])]
    args = argparse.Namespace(backend="stub", log=logs, offline=False, max_usd=CFG["cap_usd"],
                              runs_dir=str(pathlib.Path(run["log"]).parent / "replay-test"))
    tables, gain = e2e_tables()
    again = run_grids([g["puzzle"]], "voc", args, tables, gain)["grids"][0]
    assert again["slots"] == g["slots"] and again["fully_correct"] == g["fully_correct"]
    assert abs(again["usd"] - g["usd"]) < 1e-9
