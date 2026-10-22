"""Brief 012: the crawl delay and stop statuses."""

from __future__ import annotations

import json
import pathlib

import pytest

from ximenes.harvest import CFG, Stopped, fetch, polite


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.sleeps.append(s)
        self.t += s


def test_crawl_delay_between_every_request() -> None:
    clock, times = FakeClock(), []

    def get(url: str) -> tuple[int, bytes]:
        times.append(clock.t)
        clock.t += 1.5  # the request itself takes time
        return CFG["ok_status"], b"[]"

    call = polite(get, clock.now, clock.sleep)
    for _ in range(4):
        call("u")
    gaps = [b - a for a, b in zip(times, times[1:], strict=False)]
    assert all(g >= CFG["crawl_delay_seconds"] for g in gaps)


@pytest.mark.parametrize("status", [403, 429, 500])
def test_stop_status_raises(status: int) -> None:
    clock = FakeClock()
    call = polite(lambda u: (status, b""), clock.now, clock.sleep)
    with pytest.raises(Stopped):
        call("u")


def test_fetch_pages_until_a_short_page(tmp_path: pathlib.Path) -> None:
    per = CFG["per_page"]
    pages = {1: [{"id": i} for i in range(per)], 2: [{"id": per}]}
    urls: list[str] = []

    def get(url: str) -> bytes:
        urls.append(url)
        if "/categories" in url:
            return b"[]"
        page = int(url.split("&page=")[1].split("&")[0])
        return json.dumps(pages[page]).encode()

    counts = fetch(get, tmp_path)
    assert counts == {"requests": 3, "posts": per + 1, "categories": 0}
    assert len(list(tmp_path.glob("post-*.json"))) == per + 1
    assert all(CFG["after"] in u for u in urls if "/posts" in u)


ROWS = ["CAT#SON", "A#O#E#O", "PLANETS", "E#R#R#E", "RAINBOW", "S#E#E#S", "SET#DIE"]


def _post(post_id: int, drop: int = 0) -> dict:
    """A synthetic table-style post for the 7x7 grid above (invented clues);
    `drop` leaves out that many entries."""
    from ximenes.grid import from_rows

    slots = sorted(from_rows(ROWS).slots, key=lambda s: (s.orientation.value, s.number))
    cells = []
    for s in slots[drop:]:
        ans = "".join(ROWS[r][c] for r, c in s.cells)
        cells.append(f"<tr><td>{s.number}{s.orientation.value[0]}</td>"
                     f"<td><strong>{ans}</strong></td></tr>"
                     f"<tr><td></td><td>Some <u>clue</u> words here ({len(ans)})</td></tr>"
                     "<tr><td></td><td>explanation</td></tr>")
    return {"id": post_id, "date": "2026-09-01T09:00:00", "link": f"https://example.org/{post_id}",
            "categories": [1], "content": {"rendered": "<table>" + "".join(cells) + "</table>"}}


def test_complete_puzzle_rule_and_reconstruction(tmp_path: pathlib.Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    from ximenes.eval import PARAMS
    from ximenes.harvest import parse_all

    monkeypatch.setitem(PARAMS["grid"], "sizes", [len(ROWS)])
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    (raw / "categories.json").write_text(json.dumps([{"id": 1, "name": "Guardian"}]))
    (raw / "post-1.json").write_text(json.dumps(_post(1)))
    (raw / "post-2.json").write_text(json.dumps(_post(2, drop=1)))  # one clue missing
    stats = parse_all(raw, out)["publishers"]["guardian"]
    assert stats["posts"] == 2 and stats["complete"] == 1
    files = sorted(p.name for p in out.glob("*.jsonl"))
    assert files == ["guardian-1-2026-09-01.jsonl"]
    grid = json.loads((out / "grids" / "guardian-1-2026-09-01.json").read_text())
    assert grid["size"] == len(ROWS) and len(grid["clues"]) == stats["clues_complete"]


FEED = b"""<?xml version="1.0"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
<item><title>t</title><link>https://example.org/a</link>
<pubDate>Wed, 21 Oct 2026 08:00:00 +0000</pubDate><category><![CDATA[Guardian]]></category>
<guid isPermaLink="false">https://example.org/?p=101</guid>
<content:encoded><![CDATA[<p>body</p>]]></content:encoded></item>
<item><title>old</title><link>https://example.org/b</link>
<pubDate>Fri, 31 Jul 2026 08:00:00 +0000</pubDate><category>FT</category>
<guid isPermaLink="false">https://example.org/?p=7</guid>
<content:encoded><![CDATA[<p>old</p>]]></content:encoded></item>
</channel></rss>"""


def test_update_from_feed_stores_new_posts_only(tmp_path: pathlib.Path) -> None:
    from ximenes.harvest import update

    (tmp_path / "categories.json").write_text(json.dumps([{"id": 1, "name": "Guardian"},
                                                          {"id": 2, "name": "FT"}]))
    assert update(lambda u: FEED, tmp_path) == {"requests": 1, "in_feed": 2, "new": 1}
    post = json.loads((tmp_path / "post-101.json").read_text())
    assert post["categories"] == [1] and post["content"]["rendered"] == "<p>body</p>"
    assert update(lambda u: FEED, tmp_path)["new"] == 0  # already stored
