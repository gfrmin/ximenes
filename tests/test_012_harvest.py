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
