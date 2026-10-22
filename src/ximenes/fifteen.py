"""Brief 012: parse a Fifteensquared post's clue list. Pure; no I/O.

The post's HTML is flattened into segments (a block, table cell or line
break ends one), with underlined or definition-classed text wrapped in
{braces} and bold text noted. Then a scan: "Across"/"Down" headers set the
direction; a segment starting with a clue number opens an entry; within an
entry, the segment ending in an enumeration is the clue, a capitals-only run
whose letter count matches the enumeration is the answer, and the rest is the
explanation. Approach after mdda/cryptic-wordplay's generic parser (scoring
text by shape); the code is ours.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser

from .clue import Enumeration, Orientation, normalise, parse_enumeration

BLOCK = {"p", "br", "div", "tr", "td", "th", "li", "h1", "h2", "h3", "h4", "h5", "h6",
         "table", "tbody", "thead", "ul", "ol", "hr", "blockquote"}
ENUM = re.compile(r"\(\s*(\d+(?:\s*[,\-–.]\s*\d+)*)\s*(?:words?)?\)")
NUMBER = re.compile(r"^\s*(?P<n>\d+)\s*(?P<dir>a|ac|across|d|dn|down)?\b\s*[.:)\-–]?\s*"
                    r"(?P<rest>.*)$",
                    re.IGNORECASE | re.DOTALL)
HEADER = re.compile(r"^\W*(across|down)\W*$", re.IGNORECASE)
CAPS = re.compile(r"[A-Z][A-Z'’\- ]*[A-Z]|[A-Z]")


@dataclass(frozen=True)
class Segment:
    text: str
    bold: bool  # most of the segment's letters were in bold


@dataclass(frozen=True)
class Entry:
    number: int
    orientation: Orientation
    clue: str  # clue text without the enumeration, definition unmarked
    clue_marked: str  # with {definition} braces where the blogger marked it
    enumeration: Enumeration
    answer: str  # normalised
    wordplay: str


class _Flatten(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.segments: list[Segment] = []
        self.buf: list[tuple[str, bool]] = []
        self.stack: list[tuple[str, bool, bool]] = []  # tag, underline, bold

    def _flags(self) -> tuple[bool, bool]:
        return (any(u for _t, u, _b in self.stack), any(b for _t, _u, b in self.stack))

    def _end_segment(self) -> None:
        text = "".join(t for t, _b in self.buf)
        letters = sum(len(re.sub(r"[^A-Za-z]", "", t)) for t, _b in self.buf)
        bold = sum(len(re.sub(r"[^A-Za-z]", "", t)) for t, b in self.buf if b)
        text = re.sub(r"\s+", " ", text).replace("{ ", "{").replace(" }", "}").strip()
        if text:
            self.segments.append(Segment(text, letters > 0 and bold + bold > letters))
        self.buf = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in BLOCK:
            self._end_segment()
        if tag in ("br", "hr"):
            return
        a = {k: (v or "") for k, v in attrs}
        under = (tag == "u" or "underline" in a.get("style", "")
                 or "definition" in a.get("class", "") or "underline" in a.get("class", ""))
        was_under, _b = self._flags()
        if under and not was_under:
            self.buf.append(("{", False))
        self.stack.append((tag, under, tag in ("b", "strong")))

    def handle_endtag(self, tag: str) -> None:
        if not any(t == tag for t, _u, _b in self.stack):
            if tag in BLOCK:
                self._end_segment()
            return
        while self.stack:
            t, u, _b = self.stack.pop()
            if u and not self._flags()[0]:
                self.buf.append(("}", False))
            if t == tag:
                break
        if tag in BLOCK:
            self._end_segment()

    def handle_data(self, data: str) -> None:
        self.buf.append((data, self._flags()[1]))

    def close(self) -> None:
        super().close()
        self._end_segment()


def segments(html: str) -> list[Segment]:
    p = _Flatten()
    p.feed(html)
    p.close()
    return p.segments


def _orientation(word: str | None, current: Orientation) -> Orientation:
    if not word:
        return current
    return Orientation.ACROSS if word.lower().startswith("a") else Orientation.DOWN


def _answer_in(text: str, length: int) -> str | None:
    """A capitals run (spaces, hyphens, apostrophes allowed) of `length` letters."""
    for m in CAPS.finditer(text):
        if len(normalise(m.group(0))) == length:
            return normalise(m.group(0))
    return None


def _entry(number: int, orientation: Orientation, parts: list[Segment]) -> Entry | None:
    clue_i = next((i for i, s in enumerate(parts) if ENUM.search(s.text)), None)
    if clue_i is None:
        return None
    marked_full = parts[clue_i].text
    m = ENUM.search(marked_full)
    assert m is not None
    raw = re.sub(r"\s", "", m.group(1)).replace("–", "-").replace(".", ",")
    try:
        enum = parse_enumeration(raw)
    except ValueError:
        return None
    marked = marked_full[:m.start()].strip()
    tail = marked_full[m.end():].strip(" \u2013\u2014-:;")  # inline style: explanation follows
    # the clue segment may begin with the answer ("CARPET Vehicle beside ...")
    answer = None
    words = marked.split()
    for j in range(1, len(words)):
        head = " ".join(words[:j])
        if any(ch.islower() for ch in head) or not normalise(head):
            break
        if len(normalise(head)) == enum.length:
            answer, marked = normalise(head), " ".join(words[j:])
            break
    others = [s for i, s in enumerate(parts) if i != clue_i]
    used: int | None = None
    if answer is None:
        order = sorted(range(len(others)), key=lambda i: (not others[i].bold, i))
        found = ((i, a) for i in order if (a := _answer_in(others[i].text, enum.length)))
        used, answer = next(found, (None, None))
    if answer is None:
        return None
    plain = marked.replace("{", "").replace("}", "")
    if not plain or plain.isupper():
        return None
    rest = [s.text for i, s in enumerate(others)
            if not (i == used and normalise(s.text) == answer)]
    wordplay = " ".join([tail, *rest] if tail else rest).strip()
    return Entry(number, orientation, plain, marked, enum, answer, wordplay)


def parse(html: str) -> list[Entry]:
    """Entries in post order; entries without a clue, an enumeration or an
    answer of the right length are dropped."""
    out: list[Entry] = []
    orientation = Orientation.UNKNOWN
    current: tuple[int, Orientation] | None = None
    parts: list[Segment] = []

    def close() -> None:
        if current is not None:
            e = _entry(current[0], current[1], parts)
            if e is not None and e.orientation != Orientation.UNKNOWN:
                out.append(e)

    for s in segments(html):
        h = HEADER.match(s.text)
        if h:
            close()
            current, parts = None, []
            orientation = _orientation(h.group(1), orientation)
            continue
        n = NUMBER.match(s.text)
        if n and int(n.group("n")) > 0:
            close()
            o = _orientation(n.group("dir"), orientation)
            current = (int(n.group("n")), o)
            rest = n.group("rest").strip()
            parts = [Segment(rest, s.bold)] if rest else []
            continue
        if current is not None:
            parts.append(s)
    close()
    # a number may repeat (blogger notes): keep the first per (number, direction)
    seen: set[tuple[int, Orientation]] = set()
    return [e for e in out if not ((e.number, e.orientation) in seen
                                   or seen.add((e.number, e.orientation)))]
