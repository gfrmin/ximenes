"""Brief 012: post-cutoff puzzles from Fifteensquared (an I/O module, like
`instruments`). Fetches posts through the WordPress REST API with a crawl
delay, and stores the raw JSON under data/postcutoff/ (gitignored). Counts
are printed; content never is.

    python -m ximenes.harvest fetch      # categories + posts since the floor
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import urllib.request
from collections.abc import Callable
from typing import Any

from .eval import PARAMS, POSTCUTOFF

CFG = PARAMS["harvest"]
RAW = POSTCUTOFF / "raw"


class Stopped(RuntimeError):
    """The site answered with a status that means stop (e.g. 403, 429)."""


def polite(get: Callable[[str], tuple[int, bytes]], clock: Callable[[], float],
           sleep: Callable[[float], None]) -> Callable[[str], bytes]:
    """Wrap `get` so that at least the crawl delay passes between any two
    requests, and a stop status raises Stopped."""
    last: list[float] = []

    def call(url: str) -> bytes:
        if last:
            wait = CFG["crawl_delay_seconds"] - (clock() - last[-1])
            if wait > 0:
                sleep(wait)
        status, body = get(url)
        last[:] = [clock()]
        if status in CFG["stop_status"] or status != CFG["ok_status"]:
            raise Stopped(f"{status} on {url}")
        return body

    return call


def http_get(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": CFG["user_agent"]})
    try:
        with urllib.request.urlopen(req, timeout=CFG["timeout_seconds"]) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def fetch(get: Callable[[str], bytes], root: pathlib.Path = RAW) -> dict[str, Any]:
    """Categories, then every post dated on or after the floor, page by page.
    Writes raw JSON; returns counts only."""
    root.mkdir(parents=True, exist_ok=True)
    api = CFG["base"] + "/wp-json/wp/v2"
    cats = json.loads(get(f"{api}/categories?per_page={CFG['per_page']}"
                          "&_fields=id,name,slug,count,parent"))
    (root / "categories.json").write_text(json.dumps(cats))
    posts: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = json.loads(get(f"{api}/posts?after={CFG['after']}T00:00:00"
                               f"&per_page={CFG['per_page']}&page={page}&orderby=date&order=asc"
                               "&_fields=id,date,link,title,categories,tags,content,author"))
        posts += batch
        if len(batch) < CFG["per_page"]:
            break
        page += 1
    for p in posts:
        (root / f"post-{p['id']}.json").write_text(json.dumps(p))
    return {"requests": page + 1, "posts": len(posts), "categories": len(cats)}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m ximenes.harvest")
    p.add_argument("step", choices=("fetch",))
    args = p.parse_args(argv)
    if args.step == "fetch":
        t0 = time.monotonic()
        counts = fetch(polite(http_get, time.monotonic, time.sleep))
        print(json.dumps({**counts, "seconds": time.monotonic() - t0}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
