"""Brief 002: propose -> verify -> decide on single clues (no crossers).

For each clue: candidates from the vote samples (replayed from brief 000's
log), a DSL parse per candidate from the formaliser, the verifier's verdict,
oracle scores for every judgement leaf and for the definition, then a fixed
pre-registered decision rule.

    python -m ximenes.solve --set test --n 1000 --seed 20261021 --candidates 3
        [--backend stub --log runs/<id>.jsonl]
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import sys
import uuid
from collections import Counter
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from .clue import Clue, normalise
from .data import CryptoniteClue, format_enumeration, load_cryptonite
from .eval import PARAMS, sample_indices
from .instruments import (
    JUDGE_DEFINITION,
    JUDGE_HOMOPHONE,
    JUDGE_SYNONYM,
    SETTINGS,
    Instrument,
    anthropic_backend,
    budgeted,
    formalise_clue,
    judge,
    logged,
    propose_answers,
    read_log,
    replay_then,
    stub_backend,
)
from .verdict import Definition, Ok, OracleLeaf, Quarantine, Reason, Reject, Verdict
from .verify import verify

STATUS_RANK = {"Ok": 1 + 1, "Quarantine": 1, "none": 0}
LEAF_JUDGE = {
    Reason.SYNONYM: JUDGE_SYNONYM,
    Reason.HOMOPHONE: JUDGE_HOMOPHONE,
    Reason.DOUBLE_DEF: JUDGE_DEFINITION,
    Reason.CRYPTIC_DEF: JUDGE_DEFINITION,
}


# --- candidates ----------------------------------------------------------------


def candidates(samples: Sequence[str], clue: Clue, m: int) -> tuple[tuple[str, float], ...]:
    """Top m distinct normalised samples that fit the enumeration, by vote
    share among all samples; ties go to the one sampled first."""
    answers = [a for a in map(normalise, samples) if a and clue.enumeration.matches(a)]
    counts = Counter(answers)
    first = {a: i for i, a in reversed(list(enumerate(answers)))}
    ranked = sorted(counts, key=lambda a: (-counts[a], first[a]))
    return tuple((a, counts[a] / len(samples)) for a in ranked[:m])


# --- formalise, verify, judge ------------------------------------------------------


def formalise_and_verify(clue: Clue, answer: str, model: str, backend: Instrument,
                         retries: int) -> tuple[str, Verdict, int]:
    """Formalise with hinted retries; stop early when the reply has no parse."""
    tokens = tuple(t.text for t in clue.tokens)
    enum = format_enumeration(clue.enumeration)
    previous: tuple[dict[str, str], ...] = ()
    for attempt in range(retries + 1):
        src = formalise_clue(clue.text, enum, answer, model, tokens=tokens,
                             previous=previous, backend=backend)
        verdict = verify(clue, answer, src)
        if (not isinstance(verdict, Reject) or not src or attempt == retries
                or verdict.first_broken_rule.startswith("surface:unknown_operator")):
            break
        previous = (*previous, {"src": src, "rule": verdict.first_broken_rule,
                                "hint": verdict.hint})
    return src, verdict, attempt + 1


def judged(verdict: Ok | Quarantine, clue: Clue, model: str, backend: Instrument
           ) -> Ok | Quarantine:
    """Attach oracle scores to every judgement leaf and to the definition.
    The verdict's status never changes (DESIGN D4); scores travel with it."""
    context = clue.text

    def score_leaf(leaf: OracleLeaf) -> OracleLeaf:
        instrument = LEAF_JUDGE[leaf.reason]
        value = verdict.answer if instrument == JUDGE_DEFINITION else leaf.value
        phrase = leaf.value if leaf.reason == Reason.HOMOPHONE else leaf.phrase
        heard = leaf.result if leaf.reason == Reason.HOMOPHONE else value
        out = judge(instrument, phrase, heard, context, model, backend=backend)
        return dataclasses.replace(leaf, score=out["score"])

    definition = verdict.definition
    if definition.span:
        out = judge(JUDGE_DEFINITION, definition.span, verdict.answer, context, model,
                    backend=backend)
        definition = Definition(definition.span, "judged", out["score"], model)
    if isinstance(verdict, Ok):
        return dataclasses.replace(verdict, definition=definition)
    leaves = tuple(map(score_leaf, verdict.leaves))
    return dataclasses.replace(
        verdict, leaves=leaves, definition=definition,
        oracle_scores=tuple((f"{lf.reason.value}:{lf.phrase}", lf.score) for lf in leaves
                            if lf.score is not None))


def min_score(verdict: Verdict) -> float | None:
    """Minimum oracle score over the leaves and the definition; None if no
    judgement exists (an unscored judgement counts as 0: it was not cleared)."""
    if isinstance(verdict, Reject):
        return None
    scores = [lf.score if lf.score is not None else 0.0
              for lf in getattr(verdict, "leaves", ())]
    if verdict.definition.status == "judged":
        scores.append(verdict.definition.score if verdict.definition.score is not None else 0.0)
    return min(scores) if scores else None


# --- decide (pure) -------------------------------------------------------------------


def decide(records: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    """The pre-registered rule: rank by status (Ok > Quarantine > no parse),
    then by minimum oracle score (no judgement ranks above any judged score),
    then by vote share; ties keep candidate order. Pure function of the
    recorded fields `status`, `min_score`, `vote_share`."""
    if not records:
        return None

    def key(ir: tuple[int, dict[str, Any]]) -> tuple[float, ...]:
        i, r = ir
        s = r["min_score"]
        return (STATUS_RANK[r["status"]], 1.0 + 1 if s is None else s, r["vote_share"], -i)

    return max(enumerate(records), key=key)[1]


UNSCORED = frozenset({Reason.INDICATOR.value, Reason.TABLE_UNREVIEWED.value,
                      Reason.RESIDUAL.value})


def verified(record: dict[str, Any] | None, floor: float, strict: bool = True) -> bool:
    """Ok, or Quarantine with every oracle score (definition included) >= floor.
    Strict (the headline): a Quarantine resting on a reason no oracle scores
    (unlisted or unreviewed indicator/table entry) is not verified."""
    if record is None:
        return False
    if record["status"] == "Ok":
        return True
    if strict and UNSCORED & set(record["reasons"]):
        return False
    return record["status"] == "Quarantine" and record["min_score"] is not None \
        and record["min_score"] >= floor


# --- one clue, many clues ---------------------------------------------------------


def _status(v: Verdict) -> str:
    return "none" if isinstance(v, Reject) else type(v).__name__


def solve_clue(c: CryptoniteClue, *, models: dict[str, str], backend: Instrument, k: int,
               m: int, retries: int, floor: float) -> dict[str, Any]:
    clue = Clue(c.text, c.enumeration, c.orientation)
    samples = propose_answers(c.text, format_enumeration(c.enumeration), k, models["proposer"],
                              backend=backend)
    records = []
    for answer, share in candidates(samples, clue, m):
        src, verdict, attempts = formalise_and_verify(clue, answer, models["formaliser"],
                                                      backend, retries)
        if not isinstance(verdict, Reject):
            verdict = judged(verdict, clue, models["judge"], backend)
        records.append({
            "answer": answer, "vote_share": share, "src": src, "attempts": attempts,
            "status": _status(verdict), "min_score": min_score(verdict),
            "reasons": [r.value for r in getattr(verdict, "reasons", ())],
            "rule": getattr(verdict, "first_broken_rule", None),
            "definition": dataclasses.asdict(verdict.definition)
            if not isinstance(verdict, Reject) else None,
            "leaves": [{"reason": lf.reason.value, "score": lf.score}
                       for lf in getattr(verdict, "leaves", ())],
        })
    chosen = decide(records)
    gold = normalise(c.answer)
    top = max(Counter(a for a in map(normalise, samples) if a).items(),
              key=lambda kv: kv[1], default=(None, 0))
    return {
        "answer": gold, "publisher": c.publisher, "is_quick": c.is_quick,
        "chosen": chosen["answer"] if chosen else None,
        "correct": bool(chosen) and chosen["answer"] == gold,
        "chosen_status": chosen["status"] if chosen else "none",
        "chosen_min_score": chosen["min_score"] if chosen else None,
        "chosen_vote_share": chosen["vote_share"] if chosen else 0.0,
        "verified": verified(chosen, floor),
        "verified_lenient": verified(chosen, floor, strict=False),
        "gold_in_candidates": any(r["answer"] == gold for r in records),
        "gold_in_samples": gold in {normalise(s) for s in samples},
        "gold_parsed": any(r["answer"] == gold and r["status"] != "none" for r in records),
        "vote_top": top[0], "vote_top_share": top[1] / len(samples) if samples else 0.0,
        "candidates": records,
    }


def summarise(items: Sequence[dict[str, Any]]) -> dict[str, Any]:
    def acc(xs: Sequence[dict[str, Any]]) -> float | None:
        return sum(x["correct"] for x in xs) / len(xs) if xs else None

    def by(key: str) -> dict[str, Any]:
        groups = sorted({str(x[key]) for x in items})
        return {g: {"n": len([x for x in items if str(x[key]) == g]),
                    "top1": acc([x for x in items if str(x[key]) == g])} for g in groups}

    vset = [x for x in items if x["verified"]]
    high = [x for x in items if x["vote_top_share"] >= PARAMS["vote_high"]]
    return {
        "n": len(items),
        "top1": acc(items),
        "vote_top1": sum(x["vote_top"] == x["answer"] for x in items) / len(items),
        "verified_n": len(vset),
        "verified_top1": acc(vset),
        "complement_top1": acc([x for x in items if not x["verified"]]),
        "verified_lenient_n": sum(x["verified_lenient"] for x in items),
        "verified_lenient_top1": acc([x for x in items if x["verified_lenient"]]),
        "vote_high_n": len(high),
        "vote_high_top1": sum(x["vote_top"] == x["answer"] for x in high) / len(high)
        if high else None,
        "recall_candidates": sum(x["gold_in_candidates"] for x in items) / len(items),
        "recall_samples": sum(x["gold_in_samples"] for x in items) / len(items),
        "gold_parsed": sum(x["gold_parsed"] for x in items) / len(items),
        "chosen_status": dict(Counter(x["chosen_status"] for x in items)),
        "by_publisher": by("publisher"),
        "by_quick": by("is_quick"),
    }


def run(clues: Sequence[CryptoniteClue], *, models: dict[str, str], backend: Instrument,
        k: int, m: int, retries: int, floor: float, workers: int) -> dict[str, Any]:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        items = list(pool.map(lambda c: solve_clue(c, models=models, backend=backend, k=k, m=m,
                                                   retries=retries, floor=floor), clues))
    return {**summarise(items), "items": items}


def spend_by_instrument(log: pathlib.Path) -> dict[str, float]:
    out: Counter[str] = Counter()
    for r in read_log(log) if log.exists() else ():
        out[r["instrument"]] += r["cost"].get("usd") or 0.0
    return dict(out)


def _backend(args: argparse.Namespace, log_path: pathlib.Path) -> Instrument:
    if args.backend == "stub":
        if not args.log:
            raise SystemExit("--backend stub needs --log")
        replay = stub_backend(pathlib.Path(args.log[0]))
        for extra in args.log[1:]:
            replay = replay_then(pathlib.Path(extra), replay)
        return logged(replay, log_path)
    live: Instrument = budgeted(anthropic_backend(), args.max_usd)
    for extra in reversed(args.log or []):
        live = replay_then(pathlib.Path(extra), live)
    return logged(live, log_path)


def cmd_solve(args: argparse.Namespace) -> dict[str, Any]:
    started = datetime.now(UTC)
    run_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}-solve-{args.backend}-{uuid.uuid4().hex}"
    runs = pathlib.Path(args.runs_dir)
    log_path = runs / f"{run_id}.jsonl"
    population = load_cryptonite(args.set)
    indices = sample_indices(len(population), args.n, args.seed)
    models = {"proposer": args.proposer, "formaliser": args.formaliser, "judge": args.judge}
    out = run([population[i] for i in indices], models=models,
              backend=_backend(args, log_path), k=args.k, m=args.candidates,
              retries=args.retries, floor=args.floor, workers=args.workers)
    out = {"run_id": run_id, "set": args.set, "run_date": started.date().isoformat(),
           "seed": args.seed, "indices": list(indices), "models": models,
           "candidates_m": args.candidates, "oracle_floor": args.floor,
           "backend": args.backend, "replayed_from": args.log, "log": str(log_path),
           "max_usd": args.max_usd, "spend_usd": spend_by_instrument(log_path), **out}
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{run_id}.json").write_text(json.dumps(out, indent="  ", ensure_ascii=False))
    return out


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m ximenes.solve")
    p.add_argument("--set", default="test", choices=("val", "test"))
    p.add_argument("--n", type=int, default=PARAMS["n"])
    p.add_argument("--seed", type=int, default=PARAMS["seed"])
    p.add_argument("--k", type=int, default=PARAMS["k"])
    p.add_argument("--candidates", type=int, default=PARAMS["candidates"])
    p.add_argument("--retries", type=int, default=PARAMS["formalise_retries"])
    p.add_argument("--floor", type=float, default=PARAMS["oracle_floor"])
    p.add_argument("--proposer", default=SETTINGS["solve_models"]["proposer"])
    p.add_argument("--formaliser", default=SETTINGS["solve_models"]["formaliser"])
    p.add_argument("--judge", default=SETTINGS["judges"]["model"])
    p.add_argument("--backend", choices=("anthropic", "stub"), default="anthropic")
    p.add_argument("--log", nargs="*", help="logs to replay (stub) or resume from (anthropic); "
                   "e.g. brief 000's vote log for the proposer samples")
    p.add_argument("--max-usd", type=float, default=PARAMS["max_usd"])
    p.add_argument("--workers", type=int, default=PARAMS["workers"])
    p.add_argument("--runs-dir", default="runs")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    out = cmd_solve(parser().parse_args(argv))
    keys = ("run_id", "set", "n", "top1", "vote_top1", "verified_n", "verified_top1",
            "complement_top1", "vote_high_n", "vote_high_top1", "recall_candidates",
            "recall_samples", "gold_parsed", "chosen_status", "spend_usd", "log")
    print(json.dumps({k: out[k] for k in keys}, indent="  "))
    return 0


if __name__ == "__main__":
    sys.exit(main())
