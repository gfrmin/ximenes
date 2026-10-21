"""Brief 000: stub replay is exact; ECE of a perfectly calibrated run is 0."""

import argparse
import json
import pathlib
from fractions import Fraction

import pytest

from ximenes.data import CRYPTONITE, format_enumeration, load_cryptonite, read_cryptonite
from ximenes.eval import PARAMS, Vote, cmd_vote, ece, majority, sample_indices, vote_run
from ximenes.instruments import (
    SETTINGS,
    MissingFromLog,
    logged,
    propose_answers,
    read_log,
    replay_then,
    stub_backend,
)

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
STUB = FIXTURES / "stub-20.jsonl"
CLUES = read_cryptonite(FIXTURES / "clues-20.jsonl")  # original clues, Cryptonite format


def _run(tmp_path: pathlib.Path, name: str) -> dict:
    backend = logged(stub_backend(STUB), tmp_path / f"{name}.jsonl")
    return vote_run(CLUES, k=PARAMS["k"], model="hand-fixture", backend=backend,
                    n_bins=PARAMS["bins"], workers=PARAMS["workers"])


def test_replay_twice_gives_identical_numbers(tmp_path: pathlib.Path) -> None:
    a, b = _run(tmp_path, "a"), _run(tmp_path, "b")
    assert a == b
    assert a["top1"] == pytest.approx(0.7)  # 14 of the 20 hand-made votes are right
    assert a["ece"] == pytest.approx(0.175)  # worked by hand from the fixture's vote shares


def test_replay_log_replays_exactly(tmp_path: pathlib.Path) -> None:
    first = _run(tmp_path, "first")
    second = vote_run(CLUES, k=PARAMS["k"], model="hand-fixture",
                      backend=stub_backend(tmp_path / "first.jsonl"), n_bins=PARAMS["bins"])
    assert first == second
    strip = [{k: r[k] for k in ("instrument", "model", "input", "output", "cost")}
             for r in read_log(tmp_path / "first.jsonl")]
    original = [{k: r[k] for k in ("instrument", "model", "input", "output", "cost")}
                for r in read_log(STUB)]
    key = json.dumps
    assert sorted(map(key, strip)) == sorted(map(key, original))


def test_replay_then_calls_live_only_for_unseen_inputs() -> None:
    seen: list[str] = []

    def live(instrument: str, model: str, inp: dict) -> tuple[list[str], dict]:
        seen.append(inp["clue_text"])
        return ["LIVE"] * inp["k"], {"usd": 0.0}

    backend = replay_then(STUB, live)
    def first(text: str) -> str:
        enum = format_enumeration(CLUES[0].enumeration)
        return propose_answers(text, enum, PARAMS["k"], "hand-fixture", backend=backend)[0]

    assert first(CLUES[0].text) == "LISTEN"
    assert first("new clue") == "LIVE"
    assert seen == ["new clue"]


def test_stub_raises_on_unseen_input() -> None:
    with pytest.raises(MissingFromLog):
        propose_answers("not in the log", "5", PARAMS["k"], "hand-fixture",
                        backend=stub_backend(STUB))


def test_perfectly_calibrated_run_has_zero_ece() -> None:
    bins = PARAMS["bins"]
    votes = [Vote("X", Fraction(j, bins), i < j)
             for j in range(bins + 1) for i in range(bins)]
    assert ece(votes, bins) == 0


def test_miscalibrated_run_has_positive_ece() -> None:
    votes = [Vote("X", Fraction(1), False)] * 4
    assert ece(votes, PARAMS["bins"]) == 1


def test_majority_ties_go_to_first_sampled() -> None:
    assert majority(["norm", "rule", "rule", "norm", ""]) == ("NORM", Fraction(2, 5))
    assert majority(["", ""]) == (None, Fraction(0))


@pytest.mark.skipif(not (CRYPTONITE / "cryptonite-val.jsonl").exists(),
                    reason="Cryptonite not downloaded (./setup.sh)")
def test_cli_path_on_real_split(tmp_path: pathlib.Path) -> None:
    """End to end through cmd_vote on seeded val clues, with a gold-answer log
    built on the fly (Cryptonite rows are never committed: public repo)."""
    val = load_cryptonite("val")
    picked = [val[i] for i in sample_indices(len(val), PARAMS["bins"], PARAMS["seed"])]
    oracle = tmp_path / "gold.jsonl"
    record = logged(lambda ins, m, inp: ([inp["gold"]] * inp["k"], {"usd": 0.0}), oracle)
    for c in picked:
        inp = {"clue_text": c.text, "enumeration": format_enumeration(c.enumeration),
               "k": PARAMS["k"], **SETTINGS["propose_answers"]}
        record("propose_answers", "gold", inp | {"gold": c.answer})
    gold_log = tmp_path / "replay.jsonl"
    gold_log.write_text("".join(
        json.dumps(r | {"input": {k: v for k, v in r["input"].items() if k != "gold"}}) + "\n"
        for r in read_log(oracle)))
    args = argparse.Namespace(set="val", n=PARAMS["bins"], k=PARAMS["k"], model="gold",
                              backend="stub", log=str(gold_log), seed=PARAMS["seed"],
                              bins=PARAMS["bins"], workers=PARAMS["workers"],
                              runs_dir=str(tmp_path), allow_postcutoff=False)
    out = cmd_vote(args)
    assert out["top1"] == 1 and out["ece"] == 0
    assert json.loads((tmp_path / f"{out['run_id']}.json").read_text())["seed"] == PARAMS["seed"]
