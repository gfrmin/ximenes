"""Brief 017: a source fetch asks only for its category; the pooled
decision bands; per-publisher splits of the summary."""

from __future__ import annotations

import json

from ximenes.hard import CFG, summary
from ximenes.harvest import fetch


def test_source_fetch_asks_for_one_category(tmp_path) -> None:
    urls = []

    def get(url: str) -> bytes:
        urls.append(url)
        return json.dumps([{"id": 1, "date": "2026-08-02T00:00:00", "link": "x",
                            "categories": [11], "content": {"rendered": ""}}]).encode()

    src = {"base": "https://example.org", "category": 11, "publisher": "times"}
    counts = fetch(get, tmp_path, src)
    assert counts["posts"] == 1 and len(urls) == 1 and "&categories=11" in urls[0]
    assert json.loads((tmp_path / "categories.json").read_text()) == [{"id": 11,
                                                                       "name": "times"}]


def _g(pub: str, i: int, ok: bool) -> dict:
    return {"puzzle": f"{pub}-{i}-2026-09-01", "fully_correct": ok, "clues_right": 30 - (not ok),
            "slots": 30, "conflicts": 0, "calibration": [[0.95, True], [0.6, ok]],
            "stop_reason": "end_turn"}


def test_decision_bands_and_publishers() -> None:
    grids = ([_g("times", i, True) for i in range(18)] + [_g("toughie", i, True)
                                                          for i in range(14)]
             + [_g("toughie", i + 20, False) for i in range(4)])
    s = summary({"usd": 9.0, "grids": grids})
    assert s["pooled"]["fully_correct"] == 32 and s["decision"] == "direct_holds"
    assert s["by_publisher"]["toughie"]["wrong_slots_per_imperfect_grid"] == [1, 1, 1, 1]
    bad = [_g("times", i, i < 8) for i in range(36)]
    assert summary({"usd": 9.0, "grids": bad})["decision"] == "direct_falls_off"
    mid = [_g("times", i, i < 20) for i in range(36)]
    assert summary({"usd": 9.0, "grids": mid})["decision"] == "no_claim"
    assert CFG["publishers"] == ["times", "toughie"]
