"""Brief 011: sample, pattern, list parser, and replay of a logged run."""

from __future__ import annotations

import pathlib
from collections import Counter
from datetime import date

import pytest

from ximenes.clue import Clue, Enumeration, Orientation
from ximenes.data import CRYPTONITE, CryptoniteClue, load_cryptonite
from ximenes.eval import sample_indices
from ximenes.instruments import logged, stub_backend
from ximenes.proposers import CFG, candidates, half_pattern, parse_list, pick, run, sample_clues


@pytest.mark.skipif(not (CRYPTONITE / "cryptonite-test.jsonl").exists(),
                    reason="Cryptonite not fetched")
def test_sample_excludes_seed_20261021_and_is_proportional() -> None:
    pop = load_cryptonite("test")
    idx = sample_clues(pop)
    assert len(idx) == CFG["n"] == len(set(idx))
    assert not set(idx) & set(sample_indices(len(pop), CFG["exclude_n"], CFG["exclude_seed"]))
    got = Counter(pop[i].publisher for i in idx)
    share = Counter(c.publisher for c in pop)
    for p, n in got.items():
        assert abs(n - CFG["n"] * share[p] / len(pop)) <= 1 + 1  # proportional, up to rounding
    assert sample_clues(pop) == idx


@pytest.mark.parametrize("answer", ["CAT", "CARPET", "A", "AB", "LISTENING"])
def test_half_pattern_deterministic_and_at_most_half(answer: str) -> None:
    for index in range(20):
        p = half_pattern(answer, index)
        assert p == half_pattern(answer, index) and len(p) == len(answer)
        shown = [i for i, ch in enumerate(p) if ch != "?"]
        assert len(shown) <= len(answer) // 2
        assert all(answer[i] == p[i] for i in shown)
        assert all(b - a == 2 for a, b in zip(shown, shown[1:], strict=False))


@pytest.mark.parametrize("text,expected", [
    ("CARPET\nRUGGED\n", ["CARPET", "RUGGED"]),
    ("1. CARPET\n2) RUG MAT\n3: TAPIS", ["CARPET", "RUGMAT", "TAPIS"]),
    ("- carpet\n* Carpet\n\n  \n• MAT", ["CARPET", "MAT"]),
    ("CARPET (6)\nCARPET - a rug\nRUG: floor covering", ["CARPET", "RUG"]),
    ("Here are some candidates:\nCARPET", ["HEREARESOMECANDIDATES", "CARPET"]),
    ("", []),
])
def test_parse_list(text: str, expected: list[str]) -> None:
    assert parse_list(text) == expected


def test_candidates_filter_enumeration_and_pattern() -> None:
    clue = Clue("x", Enumeration((3,), ()))
    keep, enum_fail, pat_fail = candidates(["HEREARE", "CAT", "COT", "CAT"], "list", clue, "C?T")
    assert keep == ["CAT", "COT", "CAT"]  # list candidates arrive de-duplicated by parse_list
    assert enum_fail == 1 and pat_fail == 0
    keep, _e, pat_fail = candidates(["DOG", "CAT", "CAT"], "sample", clue, "C??")
    assert keep == ["CAT"] and pat_fail == 1


def test_pick_respects_price_and_ties_go_cheaper() -> None:
    k = str(CFG["pick_k"])
    cells = {
        "a": {"pattern": "half", "usd_per_clue": 0.01, "gold_in": {k: 0.80}},
        "b": {"pattern": "half", "usd_per_clue": 0.05, "gold_in": {k: 0.81}},
        "c": {"pattern": "half", "usd_per_clue": 1.00, "gold_in": {k: 0.99}},
        "d": {"pattern": "none", "usd_per_clue": 0.01, "gold_in": {k: 0.95}},
    }
    assert pick(cells, "half") == "a" and pick(cells, "none") == "d"


def _clue(i: int, answer: str) -> CryptoniteClue:
    return CryptoniteClue("times" if i % 2 else "telegraph", date(2001 + i * 5, 1, 1), None, i,
                          Orientation.ACROSS, f"clue {i}", Enumeration((len(answer),), ()),
                          answer, False, None)


def fake(instrument: str, model: str, inp: dict) -> tuple[object, dict]:
    """Deterministic stand-in: answers depend on the input only."""
    n = len(inp["clue_text"]) + len(model)
    if instrument == "propose_list":
        return "1. CAT\n2. DOG\nCOW", {"usd": 0.001, "output_tokens": 7, "refusals": 0}
    return (["CAT", "DOG", "CAT"] * inp["k"])[:inp["k"] - n % 2], {
        "usd": 0.002, "output_tokens": inp["k"], "refusals": 0}


def test_replay_of_logged_run_reproduces_every_number(tmp_path: pathlib.Path) -> None:
    clues = {i: _clue(i, a) for i, a in enumerate(["CAT", "DOG", "EMU"])}
    log = tmp_path / "run.jsonl"
    live = run(clues, logged(fake, log))
    replay = run(clues, stub_backend(log))
    assert live == replay
    cell = live["cells"]["claude-haiku-5-5|list|none"]
    assert cell["n"] == 3 and cell["usd_per_clue"] == pytest.approx(0.001)
    assert cell["gold_in"]["1"] == pytest.approx(1 / 3)
    assert cell["gold_in"]["all"] == pytest.approx(2 / 3)  # EMU is never listed


def test_structured_reply_extraction() -> None:
    from types import SimpleNamespace

    from ximenes.instruments import _formatted

    def msg(text: str) -> SimpleNamespace:
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])

    assert _formatted(msg('{"answer": "LIGHTER"}'), {"format": "answer"}) == "LIGHTER"
    assert _formatted(msg('{"candidates": ["A", "B"]}'), {"format": "candidates"}) == "A\nB"
    assert _formatted(msg("not json"), {"format": "answer"}) == ""


def test_cell_plan_limits_n_and_separates_thinking(tmp_path: pathlib.Path) -> None:
    clues = {i: _clue(i, a) for i, a in enumerate(["CAT", "DOG", "EMU"])}
    plan = [{"model": "claude-opus-5-5", "prompt": "sample", "pattern": "none", "n": 2,
             "thinking": None},
            {"model": "claude-sonnet-5-5", "prompt": "list", "pattern": "half", "n": None,
             "thinking": "between_tools"}]
    out = run(clues, logged(fake, tmp_path / "p.jsonl"), plan)["cells"]
    assert out["claude-opus-5-5|sample|none"]["n"] == 2
    assert out["claude-sonnet-5-5|list|half|between_tools"]["n"] == 3
    assert CFG["cells"] and all(c["prompt"] in ("sample", "list") for c in CFG["cells"])
