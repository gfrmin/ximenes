"""Brief 015, Stage D: the model given the whole puzzle, one call per grid.

Input: the clue list (slot, clue, enumeration) and the grid as text (each
slot's length and its crossings). Nothing from our solver. Output: every
slot's answer and a stated confidence. Paired against 013's and 014's
stored results on the same 40 grids.

    python -m ximenes.direct grids                  # counts per arm (012's post-cutoff rule)
    python -m ximenes.direct run --arm D1 --smoke   # 014's grid #1 only
    python -m ximenes.direct run --arm D1           # the 40 grids (paid)
    python -m ximenes.direct summary                # paired tables, P, ECE, conflicts
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import uuid
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from .clue import normalise
from .data import CryptoniteClue, format_enumeration
from .eval import PARAMS, ece_of
from .grid import Grid
from .gridsolve import load_grid, slot_key
from .instruments import Instrument, solve_grid
from .residual import p_greater

CFG = PARAMS["direct"]


def _order(k: str) -> tuple[str, int]:
    return (k[-1], int(k[:-1]))  # Across before Down, then by number


def puzzle_text(grid: Grid, clues: Mapping[str, CryptoniteClue]) -> tuple[list[str], list[str]]:
    """(clue lines, grid lines). A clue line: `1A. text (5)`; a grid line:
    `1A (5 letters): letter 1 = 1D letter 1; ...`."""
    keys = sorted(clues, key=_order)
    clue_lines = [f"{k}. {clues[k].text} ({format_enumeration(clues[k].enumeration)})"
                  for k in keys]
    from .grid import Slot

    lengths = {slot_key(s): s.length for s in grid.slots}
    crossings = {slot_key(Slot(n, o, ())): [(i, slot_key(Slot(on, oo, ())), j)
                                            for i, (on, oo), j in cx]
                 for (n, o), cx in grid.crossers().items()}
    grid_lines = [f"{k} ({lengths[k]} letters): " + ("; ".join(
        f"letter {i + 1} = {o} letter {j + 1}" for i, o, j in sorted(crossings.get(k, [])))
        or "no crossings") for k in keys]
    return clue_lines, grid_lines


def answers_of(output: Mapping[str, Any], grid: Grid) -> dict[str, tuple[str, float | None]]:
    """slot -> (answer letters, stated confidence); a slot the reply skipped
    or mislabelled is absent (it scores as wrong)."""
    keys = {slot_key(s) for s in grid.slots}
    out: dict[str, tuple[str, float | None]] = {}
    for a in output.get("answers", []):
        k = str(a.get("slot", "")).strip().upper().replace(" ", "")
        if k in keys and k not in out:
            c = a.get("confidence")
            out[k] = (normalise(str(a.get("answer", ""))),
                      None if c is None else min(1.0, max(0.0, float(c))))
    return out


def score_grid(answers: Mapping[str, tuple[str, float | None]], grid: Grid,
               gold: Mapping[str, str]) -> dict[str, Any]:
    """Clues right, letters right (a cell given two letters counts wrong, as
    in the solver's checkpoints), fully correct, crossing conflicts, and
    (confidence, right) pairs for ECE."""
    cells: dict[tuple[int, int], set[str]] = {}
    gold_cells: dict[tuple[int, int], str] = {}
    for s in grid.slots:
        k = slot_key(s)
        w = answers.get(k, ("", None))[0]
        for i, c in enumerate(s.cells):
            gold_cells[c] = gold[k][i]
            cells.setdefault(c, set()).add(w[i] if len(w) == s.length else "")
    ok = sum(len(v) == 1 and next(iter(v)) == gold_cells[c] for c, v in cells.items())
    conflicts = sum(len(v - {""}) > 1 for v in cells.values())
    right = {k: answers.get(k, ("", None))[0] == g for k, g in gold.items()}
    return {"clues": sum(right.values()) / len(right), "clues_right": sum(right.values()),
            "slots": len(right), "letters": ok / len(gold_cells),
            "fully_correct": ok == len(gold_cells), "conflicts": conflicts,
            "missing": sum(k not in answers for k in gold),
            "wrong_length": sum(len(answers[k][0]) != len(gold[k]) for k in answers),
            "calibration": [[answers[k][1], right[k]] for k in gold
                            if k in answers and answers[k][1] is not None]}


def grids_for(arm: str) -> list[tuple[str, str]]:
    """(brief, grid) for the 40 grids, dropping those not post-cutoff for the
    arm's model under 012's rule."""
    from .e2e import grids, split
    from .last_slots import reserve_split

    ok = {p.stem for p in grids(CFG["arms"][arm]["model"])[0]}
    pairs = ([("013", n) for n in split(grids()[0])["evaluation"]]
             + [("014", n) for n in reserve_split()])
    return [(b, n) for b, n in pairs if n in ok]


def run(arm: str, names: Sequence[tuple[str, str]], backend: Instrument,
        paths: Mapping[str, pathlib.Path] | None = None) -> list[dict[str, Any]]:
    from .e2e import grids

    paths = paths or {p.stem: p for p in grids()[0]}
    cfg = CFG["arms"][arm]

    def one(bn: tuple[str, str]) -> dict[str, Any]:
        brief, name = bn
        grid, clues = load_grid(paths[name])
        gold = {k: normalise(c.answer) for k, c in clues.items()}
        clue_lines, grid_lines = puzzle_text(grid, clues)
        try:
            out = solve_grid(clue_lines, grid_lines if cfg.get("grid", True) else None,
                             cfg["model"], cfg["effort"], cfg["max_tokens"], backend=backend,
                             prompt=cfg.get("prompt", CFG["prompt"]))
        except Exception as e:  # noqa: BLE001 - recorded, never silently dropped
            return {"brief": brief, "puzzle": name, "unfinished": f"{type(e).__name__}: {e}"}
        return {"brief": brief, "puzzle": name, "stop_reason": out.get("_stop_reason"),
                **score_grid(answers_of(out, grid), grid, gold)}

    with ThreadPoolExecutor(max_workers=CFG["grid_workers"]) as pool:
        return list(pool.map(one, names))


# --- the stored results to pair against ---------------------------------------------------


def stored(runs: pathlib.Path) -> dict[str, dict[str, bool]]:
    """arm -> grid -> fully correct, from 013's and 014's run files."""
    out: dict[str, dict[str, bool]] = {}
    for arm, ids in CFG["paired_against"].items():
        out[arm] = {}
        for run_id in ids:
            doc = json.loads((runs / f"{run_id}.json").read_text())
            out[arm].update({g["puzzle"]: bool(g["fully_correct"]) for g in doc["grids"]})
    return out


def paired(d: Mapping[str, bool], s: Mapping[str, bool]) -> dict[str, Any]:
    both = sorted(set(d) & set(s))
    x, y = sum(d[g] for g in both), sum(s[g] for g in both)
    return {"n": len(both), "direct": x, "solver": y,
            "both": sum(d[g] and s[g] for g in both),
            "neither": sum(not d[g] and not s[g] for g in both),
            "only_direct": sum(d[g] and not s[g] for g in both),
            "only_solver": sum(s[g] and not d[g] for g in both),
            "p_direct_greater": p_greater(x, len(both), y, len(both))}


def summary(docs: Mapping[str, Mapping[str, Any]], runs: pathlib.Path) -> dict[str, Any]:
    base = stored(runs)
    out: dict[str, Any] = {"arms": {}}
    for arm, doc in sorted(docs.items()):
        done = [g for g in doc["grids"] if "unfinished" not in g]
        fc = {g["puzzle"]: g["fully_correct"] for g in done}
        cal = [c for g in done for c in g["calibration"]]
        e, _bins = ece_of([c for c, _y in cal], [y for _c, y in cal], PARAMS["bins"])
        out["arms"][arm] = {
            "grids": len(doc["grids"]), "unfinished": len(doc["grids"]) - len(done),
            "dropped_by_cutoff_rule": CFG["n_grids"] - len(doc["grids"]),
            "fully_correct": sum(fc.values()),
            "clues": sum(g["clues_right"] for g in done) / max(1, sum(g["slots"] for g in done)),
            "usd": doc["usd"], "usd_per_grid": doc["usd"] / max(1, len(doc["grids"])),
            "conflicts_per_grid": sum(g["conflicts"] for g in done) / max(1, len(done)),
            "grids_with_conflicts": sum(g["conflicts"] > 0 for g in done),
            "ece": e, "n_calibration": len(cal),
            "stop_reasons": sorted({str(g.get("stop_reason")) for g in done}),
            "vs": {k: paired(fc, v) for k, v in base.items()},
        }
    arms = out["arms"]
    if arms:
        # lead's amendment: the rule reads D1 on all 40; D2 (12 grids) decides nothing
        arm = CFG["decision"]["arm"]
        p = arms[arm]["vs"]["full_solver"]["p_direct_greater"] if arm in arms else None
        band = (None if p is None else
                "direct_beats_bespoke" if p >= CFG["decision"]["direct_wins"] else
                "bespoke_beats_direct" if p <= CFG["decision"]["bespoke_wins"] else "no_change")
        out["decision"] = {"arm": arm, "p_vs_full_solver": p, "band": band}
    return out


def vs_d1(c_doc: Mapping[str, Any], d1_doc: Mapping[str, Any]) -> dict[str, Any]:
    """Brief 018: arm (c) against 015's stored D1 outcomes, paired, with
    016's statistic theta ~ Beta(1 + only D1, 1 + only (c))."""
    from .hybrid import p_paired

    c = {g["puzzle"]: g for g in c_doc["grids"] if "unfinished" not in g}
    a = {g["puzzle"]: g["fully_correct"] for g in d1_doc["grids"] if g["puzzle"] in c}
    only_a = sum(a[k] and not c[k]["fully_correct"] for k in a)
    only_c = sum(c[k]["fully_correct"] and not a[k] for k in a)
    p = p_paired(only_a, only_c)
    rule = CFG["no_grid_decision"]
    cal = [x for g in c.values() for x in g["calibration"]]
    return {"n": len(a), "unfinished": len(c_doc["grids"]) - len(c),
            "clues_only": {"fully_correct": sum(g["fully_correct"] for g in c.values()),
                           "clues": sum(g["clues_right"] for g in c.values())
                           / max(1, sum(g["slots"] for g in c.values())),
                           "usd": c_doc["usd"], "usd_per_grid": c_doc["usd"] / max(1, len(c)),
                           "conflicts_per_grid": sum(g["conflicts"] for g in c.values())
                           / max(1, len(c)),
                           "grids_with_conflicts": sum(g["conflicts"] > 0 for g in c.values()),
                           "ece": ece_of([x for x, _y in cal], [bool(y) for _x, y in cal],
                                         PARAMS["bins"])[0] if cal else None,
                           "wrong_slots_per_imperfect_grid": sorted(
                               g["slots"] - g["clues_right"] for g in c.values()
                               if not g["fully_correct"])},
            "with_grid_d1": {"fully_correct": sum(a.values())},
            "paired": {"both": sum(a[k] and c[k]["fully_correct"] for k in a),
                       "only_with_grid": only_a, "only_clues_only": only_c,
                       "neither": sum(not a[k] and not c[k]["fully_correct"] for k in a),
                       "p_theta_gt_half": p},
            "decision": ("grid_is_load_bearing" if p >= rule["grid_matters"] else
                         "grid_does_little" if p <= rule["grid_idle"] else "no_claim")}


def main(argv: Sequence[str] | None = None) -> int:
    from .policy import _backend

    p = argparse.ArgumentParser(prog="python -m ximenes.direct")
    p.add_argument("step", choices=("grids", "run", "summary", "vs-d1"))
    p.add_argument("--run", default=None, help="vs-d1: the arm C run JSON")
    p.add_argument("--arm", choices=sorted(CFG["arms"]), default="D1")
    p.add_argument("--smoke", action="store_true", help="014's grid #1 only")
    p.add_argument("--backend", choices=("anthropic", "stub"), default="anthropic")
    p.add_argument("--log", nargs="*", default=[])
    p.add_argument("--offline", action="store_true")
    p.add_argument("--max-usd", type=float, default=CFG["cap_usd"])
    p.add_argument("--runs-dir", default="runs")
    args = p.parse_args(argv)
    runs = pathlib.Path(args.runs_dir)
    if args.step == "grids":
        print(json.dumps({a: len(grids_for(a)) for a in sorted(CFG["arms"])}))
        return 0
    if args.step == "vs-d1":
        d1 = json.loads((runs / f"{CFG['d1_run']}.json").read_text())
        print(json.dumps(vs_d1(json.loads(pathlib.Path(args.run).read_text()), d1), indent=1))
        return 0
    if args.step == "summary":
        docs = {}
        for f in sorted(runs.glob("*-direct-*-anthropic-*.json")):
            doc = json.loads(f.read_text())
            if not doc["smoke"] and doc["arm"] in ("D1", "D2"):
                docs[doc["arm"]] = doc
        print(json.dumps(summary(docs, runs), indent=1))
        return 0
    from .last_slots import reserve_split

    names = [("014", reserve_split()[0])] if args.smoke else grids_for(args.arm)
    started = datetime.now(UTC)
    run_id = (f"{started.strftime('%Y%m%dT%H%M%SZ')}-direct-{args.arm}-{args.backend}-"
              f"{uuid.uuid4().hex}")
    backend, totals, _memo = _backend(args, runs / f"{run_id}.jsonl")
    out = run(args.arm, names, backend)
    doc = {"run_id": run_id, "arm": args.arm, "settings": CFG["arms"][args.arm],
           "smoke": args.smoke, "usd": totals[0], "grids": out}
    (runs / f"{run_id}.json").write_text(json.dumps(doc, indent=1))
    print(json.dumps({"run_id": run_id, "usd": totals[0], "grids": len(out),
                      "fully_correct": sum(g.get("fully_correct", False) for g in out),
                      "unfinished": sum("unfinished" in g for g in out),
                      "clues": [g.get("clues") for g in out] if args.smoke else None,
                      "stop_reasons": [g.get("stop_reason") for g in out][:CFG["show"]]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
