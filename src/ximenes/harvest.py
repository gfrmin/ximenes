"""Brief 012: post-cutoff puzzles from Fifteensquared (an I/O module, like
`instruments`). Fetches posts through the WordPress REST API with a crawl
delay, and stores the raw JSON under data/postcutoff/ (gitignored). Counts
are printed; content never is.

    python -m ximenes.harvest fetch      # categories + posts since the floor
    python -m ximenes.harvest update     # RSS feed (one request): new posts only
    python -m ximenes.harvest parse      # clue rows + reconstructed grids, counts only
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time
import urllib.request
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from .data import format_enumeration
from .eval import PARAMS, POSTCUTOFF
from .fifteen import Entry, parse
from .grid import ClueEntry, reconstruct

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


def from_feed(xml: bytes, cats: dict[str, int]) -> list[dict[str, Any]]:
    """RSS items in the REST API's post shape (id, date, link, categories,
    content.rendered); the id is the WordPress ?p= number in the guid."""
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime

    ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
    out = []
    for item in ET.fromstring(xml).iter("item"):
        guid = item.findtext("guid") or ""
        m = re.search(r"[?&]p=(\d+)", guid)
        if not m:
            continue
        day = parsedate_to_datetime(item.findtext("pubDate") or "").astimezone(UTC)
        out.append({"id": int(m.group(1)), "date": day.replace(tzinfo=None).isoformat(),
                    "link": item.findtext("link"),
                    "categories": [cats[c.text] for c in item.findall("category")
                                   if c.text in cats],
                    "content": {"rendered": item.findtext("content:encoded", "", ns)}})
    return out


def update(get: Callable[[str], bytes], root: pathlib.Path = RAW) -> dict[str, Any]:
    """One feed request; store posts not yet in `root` and dated on or after
    the floor."""
    cats = {c["name"]: c["id"] for c in json.loads((root / "categories.json").read_text())}
    posts = from_feed(get(CFG["base"] + "/feed/"), cats)
    new = [p for p in posts if p["date"] >= CFG["after"]
           and not (root / f"post-{p['id']}.json").exists()]
    for p in new:
        (root / f"post-{p['id']}.json").write_text(json.dumps(p))
    return {"requests": 1, "in_feed": len(posts), "new": len(new)}


def shape(html: str) -> str:
    """A post's structural signature from tag names only (no content)."""
    tags = Counter(t.lower() for t in re.findall(r"<\s*([a-zA-Z][a-zA-Z0-9]*)", html))
    kind = ("table" if tags["table"] else "list" if tags["li"] > CFG["shape_min_items"]
            else "p+br" if tags["br"] > CFG["shape_min_items"] else "p")
    marks = ("u" if tags["u"] else "") + ("span" if "underline" in html or "definition" in html
                                           else "")
    return f"{kind}/{marks or 'nomark'}"


def rows_of(entries: list[Entry], post: dict[str, Any], publisher: str) -> list[dict[str, Any]]:
    """Cryptonite-format rows plus wordplay, clue_marked and source_url."""
    day = datetime.fromisoformat(post["date"]).replace(tzinfo=UTC)
    ms = int(day.timestamp()) * CFG["ms_per_second"]
    return [{"publisher": publisher, "date": ms, "author": None, "number": e.number,
             "orientation": e.orientation.value,
             "clue": f"{e.clue} ({format_enumeration(e.enumeration)})", "answer": e.answer,
             "quick": publisher in CFG["quick"], "sub_publisher": None,
             "wordplay": e.wordplay, "clue_marked": e.clue_marked, "source_url": post["link"],
             "post_id": post["id"]} for e in entries]


def parse_all(root: pathlib.Path = RAW, out: pathlib.Path = POSTCUTOFF) -> dict[str, Any]:
    """Parse every kept post, reconstruct its grid, write rows and grids for
    complete puzzles; return counts by publisher and by shape (no content)."""
    cats = {c["id"]: c["name"] for c in json.loads((root / "categories.json").read_text())}
    grids_dir = out / "grids"
    grids_dir.mkdir(parents=True, exist_ok=True)
    stats: dict[str, Counter[str]] = {}
    shapes: dict[str, Counter[str]] = {}
    gcfg = PARAMS["grid"]
    for f in sorted(root.glob("post-*.json")):
        post = json.loads(f.read_text())
        names = {cats.get(c, "") for c in post["categories"]}
        publisher = next((CFG["publishers"][n] for n in sorted(names) if n in CFG["publishers"]),
                         None)
        st = stats.setdefault(publisher or "skipped", Counter())
        st["posts"] += 1
        if publisher is None or names & set(CFG["skip_categories"]):
            continue
        html = post["content"]["rendered"]
        entries = parse(html)
        sig = shape(html)
        st["entries"] += len(entries)
        outcome, size, sols = "none", None, []
        clue_entries = [ClueEntry(e.number, e.orientation, e.answer) for e in entries]
        numbers = {e.number for e in entries}
        if entries and numbers != set(range(1, max(numbers) + 1)):
            outcome = "incomplete"  # a clue number has no row: no grid can match
        elif entries:
            for size in gcfg["sizes"]:
                outcome, sols = reconstruct(clue_entries, size, gcfg["max_solutions"],
                                            CFG["reconstruct_node_limit"])
                if outcome != "none":
                    break
        st[f"grid_{outcome}"] += 1
        shapes.setdefault(sig, Counter())[f"{publisher}:{outcome}"] += 1
        if outcome != "unique":
            continue
        st["complete"] += 1
        st["clues_complete"] += len(entries)
        name = f"{publisher}-{post['id']}-{post['date'][:len('yyyy-mm-dd')]}"
        rows = rows_of(entries, post, publisher)
        (out / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        g, letters = sols[0]
        (grids_dir / f"{name}.json").write_text(json.dumps({
            "key": name, "size": g.width, "blocked": sorted(map(list, g.blocked)),
            "letters": {f"{r},{c}": v for (r, c), v in sorted(letters.items())},
            "clues": [{"split": "postcutoff", **r} for r in rows]}))
    return {"publishers": {k: dict(v) for k, v in sorted(stats.items())},
            "shapes": {k: dict(v) for k, v in sorted(shapes.items())}}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m ximenes.harvest")
    p.add_argument("step", choices=("fetch", "update", "parse"))
    args = p.parse_args(argv)
    if args.step == "fetch":
        t0 = time.monotonic()
        counts = fetch(polite(http_get, time.monotonic, time.sleep))
        print(json.dumps({**counts, "seconds": time.monotonic() - t0}))
    elif args.step == "update":
        print(json.dumps(update(polite(http_get, time.monotonic, time.sleep))))
    else:
        print(json.dumps(parse_all(), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
