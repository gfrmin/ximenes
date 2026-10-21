"""Brief 004: crossword grids — slots, numbering, crossers — and reconstruction
of a grid's layout from its clue list.

Numbering follows the standard rule: an open cell starts an across (down)
slot when the cell to its left (above) is blocked or off-grid and the run is
longer than one cell. Slots are numbered in reading order.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from .clue import Orientation

Cell = tuple[int, int]  # (row, col)
ACROSS, DOWN = Orientation.ACROSS, Orientation.DOWN
STEP = {ACROSS: (0, 1), DOWN: (1, 0)}
SlotKey = tuple[int, Orientation]


@dataclass(frozen=True)
class Slot:
    number: int
    orientation: Orientation
    cells: tuple[Cell, ...]

    @property
    def length(self) -> int:
        return len(self.cells)


@dataclass(frozen=True)
class Grid:
    width: int
    height: int
    blocked: frozenset[Cell]

    def open(self, c: Cell) -> bool:
        r, k = c
        return 0 <= r < self.height and 0 <= k < self.width and c not in self.blocked

    def _run(self, start: Cell, o: Orientation) -> tuple[Cell, ...]:
        dr, dc = STEP[o]
        cells = []
        c = start
        while self.open(c):
            cells.append(c)
            c = (c[0] + dr, c[1] + dc)
        return tuple(cells)

    @property
    def slots(self) -> tuple[Slot, ...]:
        out: list[Slot] = []
        number = 0
        for r in range(self.height):
            for k in range(self.width):
                c = (r, k)
                if not self.open(c):
                    continue
                starts = []
                for o in (ACROSS, DOWN):
                    dr, dc = STEP[o]
                    run = self._run(c, o)
                    if not self.open((r - dr, k - dc)) and len(run) > 1:
                        starts.append(Slot(0, o, run))
                if starts:
                    number += 1
                    out += [Slot(number, s.orientation, s.cells) for s in starts]
        return tuple(out)

    def crossers(self) -> dict[SlotKey, list[tuple[int, SlotKey, int]]]:
        """For each slot (number, orientation): (index in slot, other slot, index in other)."""
        where: dict[Cell, list[tuple[SlotKey, int]]] = {}
        for s in self.slots:
            for i, c in enumerate(s.cells):
                where.setdefault(c, []).append(((s.number, s.orientation), i))
        out: dict[SlotKey, list[tuple[int, SlotKey, int]]] = {}
        for s in self.slots:
            key = (s.number, s.orientation)
            out[key] = [(i, other, j) for i, c in enumerate(s.cells)
                        for other, j in where[c] if other != key]
        return out

    def symmetric(self) -> bool:
        """180° rotational symmetry of the blocked cells."""
        return all((self.height - 1 - r, self.width - 1 - k) in self.blocked
                   for r, k in self.blocked)


def from_rows(rows: Sequence[str]) -> Grid:
    """Hand format: one string per row, '#' blocked, anything else open."""
    return Grid(len(rows[0]), len(rows),
                frozenset((r, k) for r, row in enumerate(rows) for k, ch in enumerate(row)
                          if ch == "#"))


def from_ipuz(doc: dict[str, Any]) -> Grid:
    """ipuz (open JSON standard): dimensions + puzzle grid, '#' or null blocked."""
    w, h = doc["dimensions"]["width"], doc["dimensions"]["height"]
    blocked = frozenset((r, k) for r, row in enumerate(doc["puzzle"]) for k, v in enumerate(row)
                        if v == "#" or v is None
                        or (isinstance(v, dict) and v.get("cell") == "#"))
    return Grid(w, h, blocked)


# --- reconstruction ------------------------------------------------------------------

BLOCK = "#"
OPEN = "?"  # open (forced by symmetry), letter not yet known


@dataclass(frozen=True)
class ClueEntry:
    number: int
    orientation: Orientation
    answer: str  # normalised letters


def numbering_of(grid: Grid) -> frozenset[tuple[int, Orientation, int]]:
    return frozenset((s.number, s.orientation, s.length) for s in grid.slots)


def reconstruct(entries: Iterable[ClueEntry], size: int, max_solutions: int,
                node_limit: int) -> tuple[str, list[tuple[Grid, dict[Cell, str]]]]:
    """Find size×size grids with 180° symmetry whose numbering and slot lengths
    match the entries and whose crossing letters agree. Returns (outcome,
    solutions): outcome is "unique", "multiple", "none" or "limit"."""
    by_number: dict[int, list[ClueEntry]] = {}
    for e in entries:
        by_number.setdefault(e.number, []).append(e)
    numbers = sorted(by_number)
    want = frozenset((e.number, e.orientation, len(e.answer))
                     for es in by_number.values() for e in es)
    state: dict[Cell, str] = {}
    solutions: list[tuple[Grid, dict[Cell, str]]] = []
    nodes = [0]
    last = size - 1

    def inside(c: Cell) -> bool:
        return 0 <= c[0] < size and 0 <= c[1] < size

    def is_open(c: Cell) -> bool | None:
        """True / False (blocked or edge) / None (unknown)."""
        if not inside(c):
            return False
        v = state.get(c)
        return None if v is None else v != BLOCK

    def mirror(c: Cell) -> Cell:
        return (last - c[0], last - c[1])

    def put(c: Cell, v: str, undo: list[tuple[Cell, str | None]]) -> bool:
        """Set a cell (letter, BLOCK or OPEN), keeping 180° symmetry; record the
        previous value for undo. False on a contradiction."""
        cur = state.get(c)
        if cur == v:
            return True
        if cur is not None:
            if cur == OPEN and v not in (BLOCK, OPEN):
                undo.append((c, cur))
                state[c] = v
                return True
            return v == OPEN and cur != BLOCK  # a letter already satisfies OPEN
        undo.append((c, None))
        state[c] = v
        m = mirror(c)
        if m == c:
            return True
        return put(m, BLOCK if v == BLOCK else OPEN, undo)

    def definite_start(c: Cell) -> bool:
        """An open cell that the final grid will number (known neighbours)."""
        if is_open(c) is not True:
            return False
        for dr, dc in STEP.values():
            if is_open((c[0] - dr, c[1] - dc)) is False and is_open((c[0] + dr, c[1] + dc)):
                return True
        return False

    def place_slot(p: Cell, e: ClueEntry, undo: list[tuple[Cell, str | None]]) -> bool:
        dr, dc = STEP[e.orientation]
        before = (p[0] - dr, p[1] - dc)
        after = (p[0] + dr * len(e.answer), p[1] + dc * len(e.answer))
        if inside(before) and not put(before, BLOCK, undo):
            return False
        if inside(after) and not put(after, BLOCK, undo):
            return False
        for i, ch in enumerate(e.answer):
            c = (p[0] + dr * i, p[1] + dc * i)
            if not inside(c) or not put(c, ch, undo):
                return False
        return True

    def finish() -> None:
        if any(v == OPEN for v in state.values()):
            return  # an open cell no entry fills
        blocked = frozenset((r, k) for r in range(size) for k in range(size)
                            if state.get((r, k), BLOCK) == BLOCK)
        g = Grid(size, size, blocked)
        if g.symmetric() and numbering_of(g) == want:
            solutions.append((g, {c: v for c, v in state.items() if v != BLOCK}))

    def search(i: int, start: int) -> None:
        nodes[0] += 1
        if len(solutions) >= max_solutions or nodes[0] > node_limit:
            return
        if i == len(numbers):
            finish()
            return
        # Cells passed over can no longer be filled (later entries start later
        # and run right or down), so an unknown one is blocked, with its mirror.
        skipped: list[tuple[Cell, str | None]] = []
        for pos in range(start, size * size):
            p = divmod(pos, size)
            if is_open(p) is not False:
                undo: list[tuple[Cell, str | None]] = []
                if all(place_slot(p, e, undo) for e in by_number[numbers[i]]):
                    search(i + 1, pos + 1)
                for c, prev in reversed(undo):
                    if prev is None:
                        del state[c]
                    else:
                        state[c] = prev
                if len(solutions) >= max_solutions or nodes[0] > node_limit:
                    break
            # pass over p: unknown -> blocked; an open p must not start an entry
            if state.get(p) is None and not put(p, BLOCK, skipped):
                break
            if state.get(p) == OPEN or definite_start(p):
                break
        for c, prev in reversed(skipped):
            if prev is None:
                del state[c]
            else:
                state[c] = prev

    search(0, 0)
    if nodes[0] > node_limit and len(solutions) < max_solutions:
        return "limit", solutions
    return {0: "none", 1: "unique"}.get(len(solutions), "multiple"), solutions


# --- CLI: reconstruct a seeded sample of Cryptonite puzzles (local only) -------------------


def main(argv: Sequence[str] | None = None) -> int:
    import argparse
    import json
    import pathlib
    import random
    import time

    from .clue import normalise
    from .data import load_cryptonite, load_puzzles
    from .eval import PARAMS, sample_indices

    p = argparse.ArgumentParser(prog="python -m ximenes.grid")
    p.add_argument("cmd", choices=("reconstruct",))
    p.add_argument("--n", type=int, default=PARAMS["grid"]["reconstruct_sample"])
    p.add_argument("--seed", type=int, default=PARAMS["seed"])
    p.add_argument("--out", default="runs/grids")
    p.add_argument("--exclude", nargs="*", default=[],
                   help="grid directories whose puzzles must not be reused (disjoint sets, D7)")
    args = p.parse_args(argv)
    cfg = PARAMS["grid"]
    test = load_cryptonite("test")
    sampled = {(c.publisher, c.sub_publisher or "", c.date) for c in
               (test[i] for i in sample_indices(len(test), PARAMS["n"], PARAMS["seed"]))}
    puzzles = load_puzzles()
    taken = {f.stem for d in args.exclude for f in pathlib.Path(d).glob("*.json")}
    keys = sorted(k for k in puzzles if (k.publisher, k.sub_publisher, k.date) in sampled
                  and k.name not in taken)
    keys = random.Random(args.seed).sample(keys, min(args.n, len(keys)))
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for k in keys:
        rows = puzzles[k]
        entries = [ClueEntry(int(r["number"]), Orientation(r["orientation"]),
                             normalise(r["answer"]))
                   for _s, r in rows if str(r["number"]).isdigit()]
        t0 = time.monotonic()
        outcome, sols, size = "none", [], None
        for size in cfg["sizes"]:
            outcome, sols = reconstruct(entries, size, cfg["max_solutions"],
                                        cfg["reconstruct_node_limit"])
            if outcome != "none":
                break
        seconds = time.monotonic() - t0
        name = k.name
        results.append({"puzzle": name, "clues": len(rows), "outcome": outcome,
                        "size": size, "seconds": seconds})
        if outcome == "unique":
            g, letters = sols[0]
            (out_dir / f"{name}.json").write_text(json.dumps({
                "key": k.name, "size": g.width, "blocked": sorted(map(list, g.blocked)),
                "letters": {f"{r},{c}": v for (r, c), v in sorted(letters.items())},
                "clues": [{"split": s, **r} for s, r in rows],
            }))
    summary = {"n": len(results), "seed": args.seed,
               "outcomes": {o: sum(r["outcome"] == o for r in results)
                            for o in ("unique", "multiple", "none", "limit")},
               "seconds_total": sum(r["seconds"] for r in results), "puzzles": results}
    (out_dir / "_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k != "puzzles"}, indent=1))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
