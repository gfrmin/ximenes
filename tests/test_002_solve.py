"""Brief 002: the decision rule, oracle replies, concurrency, and the whole
propose -> verify -> decide loop replayed offline over original clues."""

import json
import pathlib
import random
import time

import pytest

from ximenes.clue import Clue, Enumeration
from ximenes.data import read_cryptonite
from ximenes.eval import majority
from ximenes.instruments import parse_judgement, replay_then, sample_concurrently, stub_backend
from ximenes.prompts import FORMALISE_SPEC, formalise_clue_system
from ximenes.solve import decide, judged, min_score, run, verified
from ximenes.verify import verify

FIX = pathlib.Path(__file__).parent / "fixtures"
CLUES = read_cryptonite(FIX / "clues-20.jsonl")
MODELS = {"proposer": "hand-fixture", "formaliser": "hand-fixture", "judge": "hand-fixture"}


def rec(answer: str, status: str, score: float | None, share: float,
        reasons: tuple[str, ...] = ()) -> dict:
    # Superseded by brief 003: records follow the Hyp schema (ximenes/hyp.py);
    # the decision rule reads scores.min_score. Cases unchanged.
    return {"answer": answer, "status": status, "scores": {"min_score": score},
            "vote_share": share, "reasons": list(reasons)}


# --- the decision rule is a pure function of status, min score, vote share ------------

CASES = [
    ("Ok beats Quarantine", [rec("A", "Quarantine", 0.99, 0.9), rec("B", "Ok", 0.1, 0.1)], "B"),
    ("Quarantine beats no parse", [rec("A", "none", None, 0.9), rec("B", "Quarantine", 0.1, 0.05)],
     "B"),
    ("higher min score", [rec("A", "Quarantine", 0.4, 0.8), rec("B", "Quarantine", 0.7, 0.1)],
     "B"),
    ("then vote share", [rec("A", "Ok", 0.9, 0.3), rec("B", "Ok", 0.9, 0.6)], "B"),
    ("ties keep candidate order", [rec("A", "Ok", 0.9, 0.5), rec("B", "Ok", 0.9, 0.5)], "A"),
    ("no parse anywhere: vote decides", [rec("A", "none", None, 0.6), rec("B", "none", None, 0.3)],
     "A"),
    ("nothing judged ranks above a judged score",
     [rec("A", "Ok", 0.95, 0.5), rec("B", "Ok", None, 0.1)], "B"),
]


@pytest.mark.parametrize("name,records,expected", CASES, ids=[c[0] for c in CASES])
def test_decision_rule(name: str, records: list[dict], expected: str) -> None:
    assert decide(records)["answer"] == expected


def test_decide_on_nothing_is_none() -> None:
    assert decide([]) is None


def test_verified_set_rule() -> None:
    floor = 0.5
    assert verified(rec("A", "Ok", 0.1, 0.1), floor)
    assert verified(rec("A", "Quarantine", 0.6, 0.1, ("synonym",)), floor)
    assert not verified(rec("A", "Quarantine", 0.4, 0.1, ("synonym",)), floor)
    assert not verified(rec("A", "Quarantine", 0.9, 0.1, ("indicator",)), floor)
    assert verified(rec("A", "Quarantine", 0.9, 0.1, ("indicator",)), floor, strict=False)
    assert not verified(rec("A", "none", None, 0.9), floor) and not verified(None, floor)


# --- a wordplay that works for the wrong answer ------------------------------------------

def test_wrong_answer_with_working_wordplay_is_separated_by_the_definition() -> None:
    clue = Clue("listen to broken tinsel", Enumeration((6,), ()))
    src = 'clue(defn(tok("listen")), anagram(tok("broken"), lit(tok("tinsel")), "{}"), ' \
          'link(tok("to")))'

    def judge_backend(instrument: str, model: str, inp: dict) -> tuple[dict, dict]:
        good = inp["value"] == "LISTEN"
        return {"score": 0.9 if good else 0.1, "reason": "test"}, {"usd": 0.0}

    verdicts = {a: verify(clue, a, src.format(a)) for a in ("LISTEN", "SILENT")}
    assert type(verdicts["LISTEN"]) is type(verdicts["SILENT"])  # wordplay alone can't tell
    scored = {a: judged(v, clue, "m", judge_backend) for a, v in verdicts.items()}
    assert all(type(scored[a]) is type(verdicts[a]) for a in scored)  # status unchanged (D4)
    assert scored["SILENT"].definition.status == "judged"
    assert min_score(scored["SILENT"]) < min_score(scored["LISTEN"])
    records = [rec("SILENT", type(scored["SILENT"]).__name__, min_score(scored["SILENT"]), 0.6),
               rec("LISTEN", type(scored["LISTEN"]).__name__, min_score(scored["LISTEN"]), 0.4)]
    assert decide(records)["answer"] == "LISTEN"


# --- oracle replies -----------------------------------------------------------------------

@pytest.mark.parametrize("text,score", [
    ('{"score": 0.82, "reason": "fine"}', 0.82),
    ('Sure. {"score": 1.7, "reason": "x"}', 1.0),
    ('```json\n{"score": -1, "reason": "x"}\n```', 0.0),
    ("I cannot judge this.", None),
    ('{"reason": "no score"}', None),
])
def test_parse_judgement(text: str, score: float | None) -> None:
    assert parse_judgement(text)["score"] == score


# --- concurrency keeps sample order ---------------------------------------------------------

def test_concurrent_samples_come_back_in_index_order() -> None:
    rnd = random.Random(0)
    counter = iter(range(1000))

    def slow() -> int:
        i = next(counter)
        time.sleep(rnd.random() / 200)
        return i

    out = sample_concurrently(slow, 20, 8)
    assert sorted(out) == list(range(20))  # every sample present exactly once


def test_replayed_votes_do_not_depend_on_live_scheduling(tmp_path: pathlib.Path) -> None:
    from ximenes.instruments import logged, propose_answers

    def fake_live(order_seed: int):
        def call(instrument: str, model: str, inp: dict) -> tuple[list[str], dict]:
            rnd = random.Random(order_seed)

            def one(i: int) -> str:
                time.sleep(rnd.random() / 500)
                return ["NORM", "RULE"][i % 2]

            idx = iter(range(inp["k"]))
            return sample_concurrently(lambda: one(next(idx)), inp["k"], 8), {"usd": 0.0}
        return call

    logs = []
    for seed in (1, 2):
        log = tmp_path / f"{seed}.jsonl"
        propose_answers("x", "4", 20, "m", backend=logged(fake_live(seed), log))
        logs.append(log)
    votes = [majority(propose_answers("x", "4", 20, "m", backend=stub_backend(log)))
             for log in logs]
    assert votes[0] == votes[1]


# --- prompts ----------------------------------------------------------------------------------

def test_formalise_clue_prompt_lists_the_new_operators_and_v1_is_frozen() -> None:
    s = formalise_clue_system()
    for op in ("first_letters", "last_letters", "outer_letters", "middle_letters", "remove",
               "strip_outer", "half"):
        assert f"{op}(tok(indicator)" in s
    assert "You explain how" in s and "reply NONE" in s and "taking last letters" not in s
    assert "taking last letters" in FORMALISE_SPEC  # brief 001's prompt is unchanged


# --- the whole loop, offline -------------------------------------------------------------------

def _run() -> dict:
    backend = replay_then(FIX / "stub-20.jsonl", stub_backend(FIX / "solve-stub-20.jsonl"))
    # brief 003: the fixture predates judge_indicator, so indicators stay unscored
    return run(CLUES, models=MODELS, backend=backend, k=20, m=3, retries=2, floor=0.5,
               workers=4, score_indicators=False)


def test_offline_loop_replays_exactly() -> None:
    a, b = _run(), _run()
    assert a == b
    assert a["n"] == len(CLUES) and a["top1"] == pytest.approx(1.0)
    assert a["vote_top1"] == pytest.approx(0.7)
    assert a["verified_n"] == 8 and a["verified_top1"] == pytest.approx(1.0)
    listen = next(x for x in a["items"] if x["answer"] == "LISTEN")  # (Hyp records)
    assert [r["answer"] for r in listen["candidates"]] == ["LISTEN", "SILENT"]
    assert listen["chosen"] == "LISTEN"


@pytest.mark.skipif(not list(pathlib.Path("runs").glob("*-solve-anthropic-*.json")),
                    reason="the 1,000-clue run's log is local (runs/)")
def test_headline_run_replays_exactly() -> None:
    """The headline run predates memoization: 38 synonym judgements were asked
    twice with different answers. Its canonical replay takes the first logged
    answer (on_conflict="first") under memoization; it must be deterministic and
    reproduce the reported headline."""
    from ximenes.data import load_cryptonite
    from ximenes.instruments import memoized

    paths = pathlib.Path("runs").glob("*-solve-anthropic-*.json")
    runs = [json.loads(p.read_text()) for p in paths]
    full = max((r for r in runs if r["n"] == 1000 and r["set"] == "test"
                and not r.get("score_indicators", False)),
               key=lambda r: r["run_id"], default=None)
    if full is None:
        pytest.skip("no 1,000-clue run yet")
    test = load_cryptonite("test")

    def replay() -> dict:
        backend = memoized(stub_backend(pathlib.Path(full["log"]), on_conflict="first"))
        return run([test[i] for i in full["indices"]], models=full["models"], backend=backend,
                   k=20, m=full["candidates_m"], retries=2, floor=full["oracle_floor"],
                   workers=32, score_indicators=False)

    a, b = replay(), replay()
    assert a == b
    for key in ("top1", "vote_top1", "verified_n", "verified_top1", "verified_lenient_n",
                "verified_lenient_top1", "recall_candidates", "gold_parsed"):
        assert a[key] == full[key], key


def test_memoized_backend_answers_a_repeated_input_once() -> None:
    from ximenes.instruments import memoized

    calls = []

    def flaky(instrument: str, model: str, inp: dict) -> tuple[dict, dict]:
        calls.append(1)
        return {"score": random.random(), "reason": ""}, {"usd": 0.0}

    b = memoized(flaky)
    first = b("judge_synonym", "m", {"phrase": "p", "value": "V"})
    assert all(b("judge_synonym", "m", {"phrase": "p", "value": "V"}) == first for _ in range(5))
    assert len(calls) == 1
    out = sample_concurrently(lambda: b("judge_synonym", "m", {"phrase": "q", "value": "V"}),
                              10, 10)
    assert len({json.dumps(o) for o in out}) == 1 and len(calls) == 1 + 1


def test_stub_replay_of_conflicting_log_is_explicit(tmp_path: pathlib.Path) -> None:
    log = tmp_path / "c.jsonl"
    rec_ = {"ts": "", "instrument": "judge_synonym", "model": "m", "input": {"x": 1}, "cost": {}}
    log.write_text(json.dumps({**rec_, "output": {"score": 0.1}}) + "\n"
                   + json.dumps({**rec_, "output": {"score": 0.9}}) + "\n")
    with pytest.raises(ValueError):
        stub_backend(log)
    assert stub_backend(log, on_conflict="first")("judge_synonym", "m", {"x": 1})[0] == \
        {"score": 0.1}
