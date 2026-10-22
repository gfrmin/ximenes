"""Brief 005: grid policies over priced moves.

State: every slot gets proposals first (the vote-only floor). Moves:
`solve(slot)` formalises and judges its top-m vote candidates;
`formalise_more(slot)` the next vote candidate; `repropose(slot)` asks for
samples given committed crossing letters, then solves the new ones. After
every move: BP, commit at marginal ≥ τ, and a checkpoint of cumulative spend
and of what would be submitted if the policy stopped there.

Policies: `vote` (no moves), `attempt_all` (solve every slot in number
order), `voc` (largest predicted gain / price until below ρ or out of
budget), and `fit` (attempt_all, then formalise_more and repropose rounds,
logging every move as an event for the gain model).
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
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from . import posterior as post
from .bp import OTHER, Var, committed, map_assignment, propagate
from .clue import Clue, normalise
from .data import CryptoniteClue, format_enumeration
from .eval import PARAMS
from .grid import Grid, Slot
from .gridsolve import edges_of, fits, load_grid, pattern_of, slot_key
from .hyp import hyp_of
from .instruments import (
    SETTINGS,
    BudgetExceeded,
    Instrument,
    anthropic_backend,
    budgeted,
    logged,
    memoized,
    metered,
    propose_answers,
    propose_list,
    propose_pattern,
    replay_then,
    stub_backend,
)
from .solve import formalise_and_verify, indicator_min, judged, min_score
from .verdict import Reject
from .voc import (
    GAIN_MODEL,
    MARGINAL_CALIBRATION,
    MOVE_FEATURES,
    VOC,
    choose,
    commit_rule,
    fit_gain,
    preregister_rho,
    slot_prior,
)

BP = PARAMS["bp"]


class _Spent(Exception):
    """The grid budget is used up (a policy stops and submits)."""


@dataclass
class SlotState:
    key: str
    slot: Slot
    clue: CryptoniteClue
    votes: list[tuple[str, float]]  # enumeration-valid answers, ranked by vote share
    cands: list[dict[str, Any]] = field(default_factory=list)  # formalised Hyp records
    formalised: int = 0  # how many vote candidates have been formalised
    solved: bool = False
    seen_pattern: str = ""
    moves: int = 0


@dataclass
class Tables:
    full: dict[str, Any]
    vote: dict[str, Any]
    other: dict[str, Any]
    other_vote: dict[str, Any]


def load_tables() -> Tables:
    return Tables(post.load(post.load("binned")["chosen"]),
                  json.loads(post.VOTE_TABLE.read_text()),
                  json.loads((post.DATA / "other-prior.json").read_text()),
                  json.loads((post.DATA / "other-prior-vote.json").read_text()))


def _pseudo(answer: str, share: float, rank: int) -> dict[str, Any]:
    """A vote candidate before formalising, in the Hyp shape posteriors read."""
    return {"answer": answer, "vote_share": share, "candidate_rank": rank, "status": "none",
            "reasons": [], "scores": {"definition": None, "leaves": [], "min_score": None}}


def domain(s: SlotState, t: Tables) -> tuple[list[str], tuple[float, ...]]:
    """A slot's words and prior: formalised candidates under the full posterior
    once solved, else its top-m vote candidates under the vote posterior."""
    if s.solved:
        cands = s.cands
        ps = [post.posterior(t.full, h, cands[:i] + cands[i + 1:]) for i, h in enumerate(cands)]
        return [h["answer"] for h in cands], slot_prior(ps, t.other)
    pseudo = [_pseudo(a, sh, r) for r, (a, sh) in enumerate(s.votes[:PARAMS["candidates"]])]
    ps = [post.posterior(t.vote, h, pseudo[:i] + pseudo[i + 1:]) for i, h in enumerate(pseudo)]
    return [h["answer"] for h in pseudo], slot_prior(ps, t.other_vote)


class GridRun:
    """One policy on one grid. Orchestration state lives here; every decision
    function it calls is pure."""

    def __init__(self, name: str, grid: Grid, clues: dict[str, CryptoniteClue],
                 backend: Instrument, totals: list[float], tables: Tables,
                 models: dict[str, str], warm: Instrument | None = None,
                 commit_table: dict[str, Any] | None = None,
                 proposer: dict[str, Any] | None = None) -> None:
        self.name, self.grid, self.backend, self.totals = name, grid, backend, totals
        self.warm_backend = warm
        self.commit_table = commit_table  # brief 006: None = commit on the raw marginal
        self.proposer = proposer  # brief 013: None = brief 005's Haiku votes
        self.t, self.models = tables, models
        self.edges = edges_of(grid)
        self.crossers = {slot_key(Slot(n, o, ())): [slot_key(Slot(on, oo, ()))
                                                    for _i, (on, oo), _j in cx]
                         for (n, o), cx in grid.crossers().items()}
        slots = {slot_key(s): s for s in grid.slots}
        self.gold = {k: normalise(clues[k].answer) for k in slots}
        with ThreadPoolExecutor(max_workers=PARAMS["workers"]) as pool:
            votes = dict(zip(slots, pool.map(lambda k: self._round1(clues[k], slots[k]), slots),
                             strict=True))
        self.s = {k: SlotState(k, slots[k], clues[k], votes[k],
                               seen_pattern="?" * slots[k].length) for k in slots}
        self.commits: dict[str, str] = {}
        self.marg: dict[str, list[float]] = {}
        self.events: list[dict[str, Any]] = []
        self.checkpoints: list[dict[str, Any]] = []
        self.refresh("proposals", None)

    def _round1(self, clue: CryptoniteClue, slot: Slot) -> list[tuple[str, float]]:
        enum = format_enumeration(clue.enumeration)
        r1 = (self.proposer or {}).get("round1")
        if r1 is None:
            return self._votes(propose_answers(clue.text, enum, PARAMS["k"],
                                               self.models["proposer"], backend=self.backend),
                               clue, slot)
        if r1["prompt"] == "list":
            from .proposers import parse_list  # proposers -> recall -> policy: import late

            return self._listed(parse_list(propose_list(
                clue.text, enum, None, r1["model"], backend=self.backend, fmt=r1["format"])),
                clue, slot)
        return self._votes(propose_answers(clue.text, enum, r1["k"], r1["model"],
                                           backend=self.backend, fmt=r1["format"]), clue, slot)

    @staticmethod
    def _listed(answers: Sequence[str], clue: CryptoniteClue, slot: Slot
                ) -> list[tuple[str, float]]:
        """Brief 013: a ranked list has no vote counts; each valid candidate
        gets a position share proportional to 1 / (rank + 1), summing to 1."""
        c = Clue(clue.text, clue.enumeration, clue.orientation)
        valid = [a for a in answers if c.enumeration.matches(a) and len(a) == slot.length]
        weights = [1 / (r + 1) for r in range(len(valid))]
        return [(a, w / sum(weights)) for a, w in zip(valid, weights, strict=True)]

    @staticmethod
    def _votes(samples: Sequence[str], clue: CryptoniteClue, slot: Slot) -> list[tuple[str, float]]:
        c = Clue(clue.text, clue.enumeration, clue.orientation)
        answers = [a for a in map(normalise, samples)
                   if a and c.enumeration.matches(a) and len(a) == slot.length]
        counts = Counter(answers)
        first = {a: i for i, a in reversed(list(enumerate(answers)))}
        return [(a, counts[a] / len(samples)) for a in sorted(counts, key=lambda a: (-counts[a],
                                                                                    first[a]))]

    # --- state, BP, checkpoints -----------------------------------------------------------

    def variables(self) -> dict[str, Var]:
        out = {}
        for k, s in self.s.items():
            if k in self.commits:
                out[k] = committed(self.commits[k])
            else:
                words, prior = domain(s, self.t)
                out[k] = Var(tuple(words), prior)
        return out

    def refresh(self, move: str, slot: str | None) -> None:
        vs = self.variables()
        self.marg = propagate(vs, self.edges)
        # each slot's top candidate at this step, read before this step's commits
        # (the marginal a commit decision sees): [marginal, right?, committed?]
        tops = {}
        for k, v in vs.items():
            if v.words:
                i = max(range(len(v.words)), key=lambda j: self.marg[k][j])
                tops[k] = [self.marg[k][i], v.words[i] == self.gold[k], False]
        for k, v in vs.items():
            if k not in self.commits and v.words:
                best = max(range(len(v.words)), key=lambda i: self.marg[k][i])
                if commit_rule(self.marg[k][best], self.commit_table, BP["tau"]):
                    self.commits[k] = v.words[best]
        final = map_assignment(self.variables(), self.edges)
        vs = self.variables()
        sub = {}
        for k, v in vs.items():
            w = final[k]
            if w is OTHER and v.words:  # a blank scores 0: enter the best candidate
                w = v.words[max(range(len(v.words)), key=lambda i: self.marg[k][i])]
            sub[k] = w
        cells: dict[tuple[int, int], set[str]] = {}
        gold_cells: dict[tuple[int, int], str] = {}
        for k, s in self.s.items():
            for i, c in enumerate(s.slot.cells):
                gold_cells[c] = self.gold[k][i]
                cells.setdefault(c, set()).add(sub[k][i] if sub[k] else "")
        ok = sum(len(v) == 1 and next(iter(v)) == gold_cells[c] for c, v in cells.items())
        for k in tops:
            tops[k][-1] = k in self.commits
        self.checkpoints.append({
            "slot_tops": tops,
            "move": move, "slot": slot, "usd": self.totals[0], "seconds": self.totals[-1],
            "clues_correct": sum(sub[k] == self.gold[k] for k in self.s) / len(self.s),
            "letters_correct": ok / len(gold_cells),
            "committed": len(self.commits),
            "committed_correct": sum(w == self.gold[k] for k, w in self.commits.items()),
            "committed_only_grid": len(self.commits) == len(self.s),
        })

    def max_marginal(self, k: str) -> float:
        words = self.variables()[k].words
        return max(self.marg[k][:len(words)], default=0.0)

    def features(self, k: str) -> dict[str, float]:
        s = self.s[k]
        letters = {c: self.commits[o][i] for o in self.commits
                   for i, c in enumerate(self.s[o].slot.cells)}
        pattern = pattern_of(s.slot, letters)
        shares = [sh for _a, sh in s.votes]
        return {
            "top_vote_share": shares[0] if shares else 0.0,
            "vote_margin": (shares[0] - (shares[1] if len(shares) > 1 else 0.0)) if shares else 0.0,
            "length": float(s.slot.length),
            "committed_crossers": sum(o in self.commits for o in self.crossers[k])
            / max(1, len(self.crossers[k])),
            "pattern_density": sum(ch != "?" for ch in pattern) / s.slot.length,
            "round": float(s.moves),
            "max_marginal": self.max_marginal(k),
            "other_mass": self.marg[k][-1],
            "n_candidates": float(len(s.cands)),
        }

    # --- moves --------------------------------------------------------------------------

    def available(self) -> list[tuple[str, str, dict[str, float]]]:
        letters = {c: self.commits[o][i] for o in self.commits
                   for i, c in enumerate(self.s[o].slot.cells)}
        out = []
        for k, s in self.s.items():
            if k in self.commits:
                continue
            f = self.features(k)
            if not s.solved:
                if s.votes:
                    out.append(("solve", k, f))
                continue
            if s.formalised < len(s.votes):
                out.append(("formalise_more", k, f))
            pattern = pattern_of(s.slot, letters)
            if pattern.count("?") < s.seen_pattern.count("?"):
                out.append(("repropose", k, f))
        return out

    def _formalise(self, s: SlotState, answer: str, share: float, rank: int) -> dict[str, Any]:
        c = Clue(s.clue.text, s.clue.enumeration, s.clue.orientation)
        src, verdict, attempts = formalise_and_verify(c, answer, self.models["formaliser"],
                                                      self.backend, PARAMS["formalise_retries"])
        if not isinstance(verdict, Reject):
            verdict = judged(verdict, c, self.models["judge"], self.backend)
        return hyp_of(s.key, answer, src, verdict, vote_share=share, rank=rank,
                      attempts=attempts, min_score=min_score(verdict),
                      indicator_min=indicator_min(verdict)).to_record()

    def apply(self, kind: str, k: str) -> None:
        s = self.s[k]
        before_f = self.features(k)
        before_mm = before_f["max_marginal"]
        usd0, sec0 = self.totals[0], self.totals[-1]
        if kind == "solve":
            top = s.votes[:PARAMS["candidates"]]
            s.cands = [self._formalise(s, a, sh, r) for r, (a, sh) in enumerate(top)]
            s.formalised, s.solved = len(top), True
        elif kind == "formalise_more":
            a, sh = s.votes[s.formalised]
            s.cands.append(self._formalise(s, a, sh, s.formalised))
            s.formalised += 1
        elif kind == "repropose":
            letters = {c: self.commits[o][i] for o in self.commits
                       for i, c in enumerate(self.s[o].slot.cells)}
            pattern = pattern_of(s.slot, letters)
            s.seen_pattern = pattern
            rp = (self.proposer or {}).get("repropose")
            samples = (propose_pattern(s.clue.text, format_enumeration(s.clue.enumeration),
                                       pattern, BP["repropose_k"], self.models["proposer"],
                                       backend=self.backend) if rp is None else
                       propose_pattern(s.clue.text, format_enumeration(s.clue.enumeration),
                                       pattern, rp["k"], rp["model"], backend=self.backend,
                                       fmt=rp["format"]))
            known = {h["answer"] for h in s.cands}
            new = [(a, sh) for a, sh in self._votes(samples, s.clue, s.slot)
                   if fits(a, pattern) and a not in known][:PARAMS["candidates"]]
            s.cands += [self._formalise(s, a, sh, len(s.cands) + i)
                        for i, (a, sh) in enumerate(new)]
        s.moves += 1
        self.refresh(kind, k)
        self.events.append({"grid": self.name, "kind": kind, "slot": k,
                            "features": {f: before_f[f] for f in MOVE_FEATURES[kind]},
                            "delta": (1.0 if k in self.commits else self.max_marginal(k))
                            - before_mm,
                            "usd": self.totals[0] - usd0, "seconds": self.totals[-1] - sec0})

    # --- policies ----------------------------------------------------------------------

    def warm_solves(self) -> None:
        """Make every slot's solve calls concurrently through the memo (not the
        meter), so the sequential moves replay them instantly; spend is still
        metered move by move, in order."""
        if self.warm_backend is None:
            return
        saved = self.backend
        self.backend = self.warm_backend
        try:
            with ThreadPoolExecutor(max_workers=PARAMS["workers"]) as pool:
                list(pool.map(lambda kv: [self._formalise(kv[1], a, sh, r) for r, (a, sh) in
                                          enumerate(kv[1].votes[:PARAMS["candidates"]])],
                              self.s.items()))
        finally:
            self.backend = saved

    def run(self, policy: str, gain: dict[str, Any] | None = None, rho: float = 0.0,
            budget: float = float("inf"),
            moves: Sequence[tuple[str, str]] | None = None) -> None:
        try:
            if policy in ("attempt_all", "fit", "crossers_first"):
                self.warm_solves()
                for k in sorted(self.s, key=lambda k: (self.s[k].slot.number,
                                                       self.s[k].slot.orientation.value)):
                    if self.s[k].votes and k not in self.commits:
                        if policy == "crossers_first" and self.totals[0] >= budget:
                            raise _Spent
                        self.apply("solve", k)
            if policy == "fit":
                for _ in range(BP["max_rounds"]):
                    moves = [m for m in self.available() if m[0] != "solve"]
                    if not moves:
                        break
                    for kind, k, _f in moves:
                        if k not in self.commits:
                            self.apply(kind, k)
            if policy == "crossers_first":  # brief 004's heuristic, under a budget
                for _ in range(BP["max_rounds"]):
                    order = sorted((m for m in self.available() if m[0] == "repropose"),
                                   key=lambda m: -m[-1]["committed_crossers"])
                    if not order:
                        break
                    for kind, k, _f in order:
                        if self.totals[0] >= budget:
                            raise _Spent
                        if k not in self.commits:
                            self.apply(kind, k)
            if policy == "replay_moves":  # re-apply a logged move sequence (another rule)
                for kind, k in moves or []:
                    if k not in self.commits and any(
                            m[:-1] == (kind, k) for m in self.available()):
                        self.apply(kind, k)
            if policy == "voc":
                assert gain is not None
                while True:
                    pick = choose(self.available(), gain, rho, budget - self.totals[0])
                    if pick is None:
                        break
                    self.apply(*pick)
        except BudgetExceeded:
            self.checkpoints.append({**self.checkpoints[-1], "move": "budget_exceeded"})
        except _Spent:
            pass


def score_at(checkpoints: Sequence[dict[str, Any]], budget: float) -> dict[str, Any]:
    """The submission a policy would have made had it stopped at this budget:
    the last checkpoint whose cumulative spend is within it."""
    within = [c for c in checkpoints if c["usd"] <= budget]
    return within[-1] if within else checkpoints[0]


def _backend(args: argparse.Namespace, log_path: pathlib.Path
             ) -> tuple[Instrument, list[float], Instrument]:
    """(metered backend for the policy, its totals, the memo underneath for
    warming the cache concurrently without touching the meter)."""
    if args.backend == "stub":
        replay: Instrument = stub_backend(pathlib.Path(args.log[0]), on_conflict="first")
        for extra in args.log[1:]:
            replay = replay_then(pathlib.Path(extra), replay, on_conflict="first")
        if args.offline:
            from .gridsolve import offline
            replay = offline(replay)
        inner = logged(replay, log_path)
    else:
        live: Instrument = budgeted(anthropic_backend(), args.max_usd)
        for extra in reversed(args.log or []):
            live = replay_then(pathlib.Path(extra), live, on_conflict="first")
        inner = logged(live, log_path)
    memo = memoized(inner)
    meter, totals = metered(memo)
    return meter, totals, memo


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m ximenes.policy")
    p.add_argument("--policy", required=True,
                   choices=("vote", "attempt_all", "voc", "fit", "crossers_first",
                            "replay_moves"))
    p.add_argument("--calibrated", action="store_true",
                   help="brief 006: commit on the calibrated marginal")
    p.add_argument("--offline", action="store_true",
                   help="stub only: a call missing from the logs produces nothing")
    p.add_argument("--moves-from", default=None,
                   help="replay_moves: a policy run JSON whose move sequence to re-apply")
    p.add_argument("--grids", required=True)
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--budget-usd", type=float, default=float("inf"))
    p.add_argument("--backend", choices=("anthropic", "stub"), default="anthropic")
    p.add_argument("--log", nargs="*", default=[])
    p.add_argument("--max-usd", type=float, default=PARAMS["max_usd"])
    p.add_argument("--runs-dir", default="runs")
    args = p.parse_args(argv)
    grids_dir = pathlib.Path(args.grids)
    summary = json.loads((grids_dir / "_summary.json").read_text())
    names = [r["puzzle"] for r in summary["puzzles"]
             if r["outcome"] == "unique" and r["clues"] >= PARAMS["grid"]["min_clues"]][:args.n]
    gain = json.loads(GAIN_MODEL.read_text()) if args.policy == "voc" else None
    if gain is not None and summary["seed"] == gain["fit_seed"]:
        raise SystemExit("VOC must not be evaluated on its fit grids")
    started = datetime.now(UTC)
    run_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}-{args.policy}-{args.backend}-{uuid.uuid4().hex}"
    runs = pathlib.Path(args.runs_dir)
    log_path = runs / f"{run_id}.jsonl"
    tables = load_tables()
    commit_table = json.loads(MARGINAL_CALIBRATION.read_text()) if args.calibrated else None
    source_moves = {}
    if args.moves_from:
        src = json.loads(pathlib.Path(args.moves_from).read_text())
        source_moves = {g["puzzle"]: [(c["move"], c["slot"]) for c in g["checkpoints"]
                                      if c["move"] in ("solve", "formalise_more", "repropose")]
                        for g in src["grids"]}
    models = {"proposer": SETTINGS["solve_models"]["proposer"],
              "formaliser": SETTINGS["solve_models"]["formaliser"],
              "judge": SETTINGS["judges"]["model"]}
    out_grids = []
    for name in names:
        grid, clues = load_grid(grids_dir / f"{name}.json")
        backend, totals, memo = _backend(args, log_path)  # fresh meter and memo per grid
        g = GridRun(name, grid, clues, backend, totals, tables, models, warm=memo,
                    commit_table=commit_table)
        g.run(args.policy, gain, gain["rho"]["rho"] if gain else 0.0, args.budget_usd,
              source_moves.get(name))
        out_grids.append({"puzzle": name, "checkpoints": g.checkpoints, "events": g.events,
                          "proposal_usd": g.checkpoints[0]["usd"]})
    out = {"run_id": run_id, "policy": args.policy, "grids_seed": summary["seed"],
           "calibrated_commit": args.calibrated, "moves_from": args.moves_from,
           "budget_usd": args.budget_usd, "log": str(log_path), "grids": out_grids}
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{run_id}.json").write_text(json.dumps(out, indent=1))
    if args.policy == "fit" and args.backend == "anthropic":  # a replay never rewrites it
        events = [e for g in out_grids for e in g["events"]]
        model = fit_gain(events, summary["seed"])
        model["rho"] = preregister_rho(events, model, {g["puzzle"]: g["proposal_usd"]
                                                      for g in out_grids}, VOC["target_spend"])
        model["fit_grid_spend"] = sorted(g["checkpoints"][-1]["usd"] for g in out_grids)
        GAIN_MODEL.write_text(json.dumps({"source": f"fitted by `python -m ximenes.policy "
                                          f"--policy fit` on fit-seed grids (run {run_id}); "
                                          "briefs/005", **model}, indent=1) + "\n")
    print(json.dumps([{"puzzle": g["puzzle"], **{k: g["checkpoints"][-1][k] for k in (
        "usd", "clues_correct", "letters_correct", "committed")}} for g in out_grids], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
