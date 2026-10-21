"""Brief 004: solve a whole grid, with crossers as evidence.

Round 1 solves every slot alone (brief 002's loop) and scores candidates with
brief 003's committed posterior. Then: belief propagation over the slots;
commit any slot whose top marginal reaches τ (committed letters are hard
evidence and never change); re-propose uncommitted slots with the pattern of
committed letters (only when the pattern has gained letters since the slot
was last proposed); repeat up to max_rounds; submit the MAP, entering the
best candidate where the MAP says OTHER.

    python -m ximenes.gridsolve --grids runs/grids --n 20 --seed 20261021
        [--backend stub --log ...]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import uuid
from collections import Counter
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from . import posterior as post
from .bp import OTHER, Var, committed, map_assignment, prior_with_other, propagate
from .clue import Clue, normalise
from .data import CryptoniteClue, format_enumeration, parse_cryptonite
from .eval import PARAMS
from .grid import ACROSS, Grid, Slot
from .hyp import hyp_of
from .instruments import (
    SETTINGS,
    BudgetExceeded,
    Instrument,
    anthropic_backend,
    budgeted,
    logged,
    memoized,
    propose_pattern,
    replay_then,
    stub_backend,
)
from .solve import formalise_and_verify, indicator_min, judged, min_score, solve_clue
from .verdict import Reject

BP = PARAMS["bp"]


def slot_key(s: Slot) -> str:
    return f"{s.number}{'A' if s.orientation == ACROSS else 'D'}"


def edges_of(grid: Grid) -> list[tuple[str, int, str, int]]:
    out = []
    for (num, ori), crossings in grid.crossers().items():
        a = slot_key(Slot(num, ori, ()))
        for i, (onum, oori), j in crossings:
            b = slot_key(Slot(onum, oori, ()))
            if a < b:
                out.append((a, i, b, j))
    return out


def with_posteriors(cands: list[dict[str, Any]], model: dict[str, Any]) -> list[dict[str, Any]]:
    return [{**h, "posterior": post.posterior(model, h, cands[:i] + cands[i + 1:])}
            for i, h in enumerate(cands)]


def pattern_of(slot: Slot, letters: dict[tuple[int, int], str]) -> str:
    return "".join(letters.get(c, "?") for c in slot.cells)


def fits(word: str, pattern: str) -> bool:
    return len(word) == len(pattern) and all(p in ("?", w) for w, p in zip(word, pattern,
                                                                          strict=True))


def repropose(clue: CryptoniteClue, slot: str, pattern: str, existing: Sequence[str], *,
              models: dict[str, str], backend: Instrument, m: int, retries: int,
              score_indicators: bool) -> list[dict[str, Any]]:
    """New candidates for a slot from samples given the crossing letters."""
    c = Clue(clue.text, clue.enumeration, clue.orientation)
    samples = propose_pattern(clue.text, format_enumeration(clue.enumeration), pattern,
                              BP["repropose_k"], models["proposer"], backend=backend)
    answers = [a for a in map(normalise, samples) if a and fits(a, pattern)
               and c.enumeration.matches(a)]
    counts = Counter(answers)
    first = {a: i for i, a in reversed(list(enumerate(answers)))}
    fresh = sorted((a for a in counts if a not in existing), key=lambda a: (-counts[a], first[a]))
    out = []
    for rank, a in enumerate(fresh[:m], start=len(existing)):
        src, verdict, attempts = formalise_and_verify(c, a, models["formaliser"], backend,
                                                      retries)
        if not isinstance(verdict, Reject):
            verdict = judged(verdict, c, models["judge"], backend, score_indicators)
        out.append(hyp_of(slot, a, src, verdict, vote_share=counts[a] / len(samples),
                          rank=rank, attempts=attempts, min_score=min_score(verdict),
                          indicator_min=indicator_min(verdict)).to_record())
    return out


def solve_grid(grid: Grid, clues: dict[str, CryptoniteClue], *, models: dict[str, str],
               backend: Instrument, model: dict[str, Any], workers: int,
               score_indicators: bool = True) -> dict[str, Any]:
    """The grid loop. `clues` maps slot key -> clue. Returns per-slot records."""
    slots = {slot_key(s): s for s in grid.slots}
    edges = edges_of(grid)
    cfg = PARAMS
    with ThreadPoolExecutor(max_workers=workers) as pool:
        alone = dict(zip(slots, pool.map(
            lambda k: solve_clue(clues[k], models=models, backend=backend, k=cfg["k"],
                                 m=cfg["candidates"], retries=cfg["formalise_retries"],
                                 floor=cfg["oracle_floor"], slot=k,
                                 score_indicators=score_indicators), slots), strict=True))
    cands = {k: with_posteriors([h for h in alone[k]["candidates"]
                                 if len(h["answer"]) == slots[k].length], model)
             for k in slots}
    commits: dict[str, tuple[str, int]] = {}  # slot -> (word, round)
    seen_pattern = {k: "?" * slots[k].length for k in slots}
    reproposed: Counter[str] = Counter()
    budget_hit = False
    rounds = 0
    marg: dict[str, list[float]] = {}

    def variables() -> dict[str, Var]:
        return {k: committed(commits[k][0]) if k in commits else
                Var(tuple(h["answer"] for h in cands[k]),
                    prior_with_other([h["posterior"] for h in cands[k]], BP["floor_other"]))
                for k in slots}

    for rnd in range(1, BP["max_rounds"] + 1):
        rounds = rnd
        vs = variables()
        marg = propagate(vs, edges)
        new_commits = 0
        for k in slots:
            if k in commits or not vs[k].words:
                continue
            best = max(range(len(vs[k].words)), key=lambda i: marg[k][i])
            if marg[k][best] >= BP["tau"]:
                commits[k] = (vs[k].words[best], rnd)
                new_commits += 1
        if rnd == BP["max_rounds"] or budget_hit:
            break
        letters = {c: commits[k][0][i] for k in commits for i, c in enumerate(slots[k].cells)}
        crossed = {k: sum(any(c in letters for c in slots[o].cells) for o in slots) for k in slots}
        targets = sorted((k for k in slots if k not in commits
                          and pattern_of(slots[k], letters).count("?")
                          < seen_pattern[k].count("?")), key=lambda k: -crossed[k])
        added = 0
        for k in targets:
            pattern = pattern_of(slots[k], letters)
            seen_pattern[k] = pattern
            try:
                fresh = repropose(clues[k], k, pattern, [h["answer"] for h in cands[k]],
                                  models=models, backend=backend, m=cfg["candidates"],
                                  retries=cfg["formalise_retries"],
                                  score_indicators=score_indicators)
            except BudgetExceeded:
                budget_hit = True
                break
            reproposed[k] += 1
            if fresh:
                cands[k] = with_posteriors(cands[k] + fresh, model)
                added += len(fresh)
        if not new_commits and not added:
            break
    vs = variables()
    final = map_assignment(vs, edges)
    marg = propagate(vs, edges)
    out = {}
    for k, s in slots.items():
        # OTHER is not a word: where the MAP says OTHER, enter the candidate with
        # the highest marginal (a blank scores 0 under the game's payoff,
        # docs/GAME.md, so a guess weakly dominates it)
        map_word = final[k]
        word = map_word
        if word is OTHER and vs[k].words:
            word = vs[k].words[max(range(len(vs[k].words)), key=lambda i: marg[k][i])]
        h = next((h for h in cands[k] if h["answer"] == word), None)
        alone_top = max(cands[k][:len(alone[k]["candidates"])], key=lambda h: h["posterior"],
                        default=None)
        out[k] = {
            "length": s.length, "submitted": word, "map_other": map_word is OTHER,
            "gold": normalise(clues[k].answer),
            "status": h["status"] if h else "none",
            "reasons": list(h["reasons"]) if h else [],
            "marginal": marg[k][vs[k].domain.index(word)] if word is not OTHER else marg[k][-1],
            "other_marginal": marg[k][-1],
            "committed_round": commits[k][1] if k in commits else None,
            "committed_word": commits[k][0] if k in commits else None,
            "reproposed": reproposed[k], "n_candidates": len(cands[k]),
            "alone_answer": alone_top["answer"] if alone_top else None,
        }
    return {"slots": out, "rounds": rounds, "budget_hit": budget_hit}


def score_grid(grid: Grid, result: dict[str, Any]) -> dict[str, Any]:
    slots = {slot_key(s): s for s in grid.slots}
    sub: dict[tuple[int, int], set[str]] = {}
    gold: dict[tuple[int, int], str] = {}
    for k, r in result["slots"].items():
        for i, c in enumerate(slots[k].cells):
            gold[c] = r["gold"][i]
            sub.setdefault(c, set()).add(r["submitted"][i] if r["submitted"] else "")
    cells_ok = sum(len(v) == 1 and next(iter(v)) == gold[c] for c, v in sub.items())
    rs = list(result["slots"].values())
    proven = all(r["status"] == "Ok" and r["submitted"] is not None for r in rs)
    return {
        "fully_correct": cells_ok == len(gold),
        "letters_correct": cells_ok / len(gold),
        "clues_correct": sum(r["submitted"] == r["gold"] for r in rs) / len(rs),
        "clues_correct_alone": sum(r["alone_answer"] == r["gold"] for r in rs) / len(rs),
        "clues_correct_pure_map": sum(r["submitted"] == r["gold"] and not r["map_other"]
                                      for r in rs) / len(rs),
        "map_other": sum(r["map_other"] for r in rs),
        "proven": proven,
        "slots_ok": sum(r["status"] == "Ok" for r in rs),
        "slots_quarantine": sum(r["status"] == "Quarantine" for r in rs),
        "slots_none": sum(r["status"] == "none" or r["submitted"] is None for r in rs),
        "quarantine_reasons": dict(Counter(x for r in rs if r["status"] == "Quarantine"
                                           for x in r["reasons"])),
        "uncommitted": sum(r["committed_round"] is None for r in rs),
        "rounds": result["rounds"], "n_slots": len(rs),
    }


def load_grid(path: pathlib.Path) -> tuple[Grid, dict[str, CryptoniteClue]]:
    doc = json.loads(path.read_text())
    size = doc["size"]
    grid = Grid(size, size, frozenset(tuple(c) for c in doc["blocked"]))
    by_slot = {f"{r['number']}{'A' if r['orientation'] == 'across' else 'D'}": r
               for _s, r in ((c["split"], c) for c in doc["clues"])}
    clues = {slot_key(s): parse_cryptonite(by_slot[slot_key(s)]) for s in grid.slots}
    return grid, clues


def _backend(args: argparse.Namespace, log_path: pathlib.Path) -> Instrument:
    if args.backend == "stub":
        replay: Instrument = stub_backend(pathlib.Path(args.log[0]), on_conflict="first")
        for extra in args.log[1:]:
            replay = replay_then(pathlib.Path(extra), replay, on_conflict="first")
        return memoized(logged(replay, log_path))
    live: Instrument = budgeted(anthropic_backend(), args.max_usd)
    for extra in reversed(args.log or []):
        live = replay_then(pathlib.Path(extra), live, on_conflict="first")
    return memoized(logged(live, log_path))


def main(argv: Sequence[str] | None = None) -> int:
    from .solve import spend_by_instrument

    p = argparse.ArgumentParser(prog="python -m ximenes.gridsolve")
    p.add_argument("--grids", default="runs/grids")
    p.add_argument("--n", type=int, default=PARAMS["grid"]["eval_grids"])
    p.add_argument("--backend", choices=("anthropic", "stub"), default="anthropic")
    p.add_argument("--log", nargs="*", default=[])
    p.add_argument("--max-usd", type=float, default=PARAMS["max_usd"])
    p.add_argument("--workers", type=int, default=PARAMS["workers"])
    p.add_argument("--runs-dir", default="runs")
    args = p.parse_args(argv)
    grids_dir = pathlib.Path(args.grids)
    summary = json.loads((grids_dir / "_summary.json").read_text())
    names = [r["puzzle"] for r in summary["puzzles"]
             if r["outcome"] == "unique" and r["clues"] >= PARAMS["grid"]["min_clues"]][:args.n]
    started = datetime.now(UTC)
    run_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}-grid-{args.backend}-{uuid.uuid4().hex}"
    runs = pathlib.Path(args.runs_dir)
    log_path = runs / f"{run_id}.jsonl"
    backend = _backend(args, log_path)
    models = {"proposer": SETTINGS["solve_models"]["proposer"],
              "formaliser": SETTINGS["solve_models"]["formaliser"],
              "judge": SETTINGS["judges"]["model"]}
    model = post.load(post.load("binned")["chosen"])
    grids = []
    for name in names:
        grid, clues = load_grid(grids_dir / f"{name}.json")
        before = spend_by_instrument(log_path, [pathlib.Path(x) for x in args.log])
        result = solve_grid(grid, clues, models=models, backend=backend, model=model,
                            workers=args.workers)
        after = spend_by_instrument(log_path, [pathlib.Path(x) for x in args.log])
        grids.append({"puzzle": name, **score_grid(grid, result),
                      "spend_usd": sum(after.values()) - sum(before.values()),
                      "budget_hit": result["budget_hit"], "slots": result["slots"]})
        if result["budget_hit"]:
            break
    out = {"run_id": run_id, "run_date": started.date().isoformat(), "grids": grids,
           "log": str(log_path),
           "spend_usd": spend_by_instrument(log_path, [pathlib.Path(x) for x in args.log])}
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{run_id}.json").write_text(json.dumps(out, indent=1))
    keys = ("puzzle", "fully_correct", "letters_correct", "clues_correct",
            "clues_correct_alone", "proven", "uncommitted", "rounds", "spend_usd")
    print(json.dumps([{k: g[k] for k in keys} for g in grids], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
