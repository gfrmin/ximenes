"""Brief 001: coverage runs replay exactly from a formaliser log, never touch
Cryptonite test, and retry with the verifier's hint."""

import argparse
import json
import pathlib

import pytest

from ximenes.data import load_wordplay
from ximenes.eval import PARAMS, cmd_coverage, coverage_run, parser
from ximenes.instruments import read_log, stub_backend

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
STUB = FIXTURES / "formalise-stub.jsonl"
EXAMPLES = load_wordplay("val", FIXTURES / "wordplay")  # original clues, teacow format


def _run() -> dict:
    return coverage_run(EXAMPLES, model="hand-fixture", backend=stub_backend(STUB),
                        retries=PARAMS["formalise_retries"], workers=PARAMS["workers"])


def test_replaying_the_formaliser_log_reproduces_coverage() -> None:
    a, b = _run(), _run()
    assert a == b
    assert a["coverage"] == pytest.approx(0.6)
    # (brief 002: the fixture's unknown operator is now spoonerism; last_letters exists)
    assert a["reject_rules"] == {"surface:unknown_operator:spoonerism": 1,
                                 "hidden:not_found": 1}
    assert a["mutant_false_accepts"] == 0 and a["mutants"] > 0


def test_retries_carry_the_hint_and_stop_on_unknown_operator() -> None:
    records = read_log(STUB)
    listen = [r for r in records if r["input"]["answer"] == "LISTEN"]
    assert len(listen) == 2 and listen[1]["input"]["previous"][0]["rule"] == \
        "coverage:unused:1:to"
    assert len([r for r in records if r["input"]["answer"] == "HEN"]) == 1
    assert len([r for r in records if r["input"]["answer"] == "LIME"]) == \
        PARAMS["formalise_retries"] + 1


def test_cli_replay_writes_summary(tmp_path: pathlib.Path) -> None:
    args = argparse.Namespace(set="val", n=None, model="hand-fixture", backend="stub",
                              log=str(STUB), seed=PARAMS["seed"],
                              retries=PARAMS["formalise_retries"], max_usd=PARAMS["max_usd"],
                              workers=PARAMS["workers"], runs_dir=str(tmp_path),
                              root=str(FIXTURES / "wordplay"))
    out = cmd_coverage(args)
    saved = json.loads((tmp_path / f"{out['run_id']}.json").read_text())
    assert saved["coverage"] == pytest.approx(0.6) and saved["set"] == "wordplay-val"


def test_coverage_never_runs_on_cryptonite_test() -> None:
    with pytest.raises(SystemExit):
        parser().parse_args(["coverage", "--set", "test", "--model", "m"])
