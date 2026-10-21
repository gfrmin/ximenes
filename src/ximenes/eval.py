"""Majority-vote baseline: top-1 and ECE of vote-share confidence (brief 000).

The only module allowed to open `data/postcutoff/`, and only through
`load_postcutoff(allow_postcutoff=True)`.

    python -m ximenes.eval vote --set test --n 1000 --k 20 --model <id>
        [--backend anthropic|ollama|stub --log runs/<id>.jsonl]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import re
import sys
import uuid
from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from fractions import Fraction
from typing import Any

from .clue import Clue, normalise, parse_enumeration
from .data import (
    DATA,
    SPLITS,
    CryptoniteClue,
    WordplayExample,
    format_enumeration,
    load_cryptonite,
    load_wordplay,
    read_cryptonite,
)
from .instruments import (
    SETTINGS,
    Instrument,
    anthropic_backend,
    budgeted,
    formalise_gold,
    logged,
    ollama_backend,
    propose_answers,
    read_log,
    replay_then,
    stub_backend,
)
from .mutants import mutants
from .verdict import Reason, Reject
from .verify import verify

POSTCUTOFF = DATA / "postcutoff"
PARAMS: dict[str, Any] = json.loads((DATA / "eval.json").read_text())


def postcutoff_cutoff(model: str, released: Mapping[str, str | None], floor: str) -> date:
    """Last date a row may carry and still be seen by `model` in training:
    the later of the global floor and the model's release date. Raises if the
    model has no release date in data/instruments.json (the author fills it)."""
    day = released.get(model)
    if day is None:
        raise ValueError(f"no release date for {model!r}: fill `released` in data/instruments.json")
    return max(date.fromisoformat(floor), date.fromisoformat(day))


def load_postcutoff(
    *,
    allow_postcutoff: bool = False,
    model: str | None = None,
    root: pathlib.Path = POSTCUTOFF,
    released: Mapping[str, str | None] | None = None,
) -> tuple[tuple[CryptoniteClue, ...], int]:
    """Rows from every `*.jsonl` under data/postcutoff/ (Cryptonite format)
    dated after `model`'s cutoff, and the count of rows excluded by date."""
    if not allow_postcutoff:
        raise PermissionError("data/postcutoff/ is opened only with allow_postcutoff=True")
    if model is None:
        raise ValueError("post-cutoff rows are filtered per model: pass model=")
    cutoff = postcutoff_cutoff(
        model, SETTINGS["released"] if released is None else released, PARAMS["postcutoff_floor"]
    )
    rows = tuple(c for f in sorted(root.glob("*.jsonl")) for c in read_cryptonite(f))
    kept = tuple(c for c in rows if c.date > cutoff)
    return kept, len(rows) - len(kept)


# --- scoring ---------------------------------------------------------------


@dataclass(frozen=True)
class Vote:
    prediction: str | None  # normalised; None if no sample had letters
    confidence: Fraction  # vote share of the prediction among k samples
    correct: bool


def majority(samples: Sequence[str]) -> tuple[str | None, Fraction]:
    """Most frequent normalised sample; ties go to the one sampled first.
    Confidence is its share of all samples, blanks included."""
    answers = [a for a in map(normalise, samples) if a]
    if not answers:
        return None, Fraction(0)
    counts = Counter(answers)
    first = {a: i for i, a in reversed(list(enumerate(answers)))}
    winner = max(counts, key=lambda a: (counts[a], -first[a]))
    return winner, Fraction(counts[winner], len(samples))


def score(samples: Sequence[str], gold: str) -> Vote:
    prediction, confidence = majority(samples)
    return Vote(prediction, confidence, prediction == normalise(gold))


@dataclass(frozen=True)
class Bin:
    lo: Fraction
    hi: Fraction
    count: int
    mean_confidence: Fraction | None
    accuracy: Fraction | None


def bin_index(confidence: Fraction, n_bins: int) -> int:
    return min(int(confidence * n_bins), n_bins - 1)


def reliability(votes: Sequence[Vote], n_bins: int) -> tuple[Bin, ...]:
    def make(b: int) -> Bin:
        members = [v for v in votes if bin_index(v.confidence, n_bins) == b]
        n = len(members)
        return Bin(
            lo=Fraction(b, n_bins),
            hi=Fraction(b + 1, n_bins),
            count=n,
            mean_confidence=sum((v.confidence for v in members), Fraction(0)) / n if n else None,
            accuracy=Fraction(sum(v.correct for v in members), n) if n else None,
        )

    return tuple(map(make, range(n_bins)))


def ece(votes: Sequence[Vote], n_bins: int) -> Fraction:
    """Expected calibration error, exact: sum over bins of (n_b/N)|acc_b - conf_b|."""
    if not votes:
        return Fraction(0)
    bins = reliability(votes, n_bins)
    return sum(
        (Fraction(b.count, len(votes)) * abs(b.accuracy - b.mean_confidence)
         for b in bins if b.count and b.accuracy is not None and b.mean_confidence is not None),
        Fraction(0),
    )


def top1(votes: Sequence[Vote]) -> Fraction:
    return Fraction(sum(v.correct for v in votes), len(votes)) if votes else Fraction(0)


# --- running ---------------------------------------------------------------


def sample_indices(population: int, n: int, seed: int) -> tuple[int, ...]:
    return tuple(sorted(random.Random(seed).sample(range(population), min(n, population))))


def vote_run(
    clues: Sequence[CryptoniteClue],
    *,
    k: int,
    model: str,
    backend: Instrument,
    n_bins: int,
    workers: int = 1,
) -> dict[str, Any]:
    """Propose k answers per clue, vote, and summarise. Pure given the backend."""

    def one(c: CryptoniteClue) -> list[str]:
        return propose_answers(c.text, format_enumeration(c.enumeration), k, model, backend=backend)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        samples = list(pool.map(one, clues))
    votes = [score(s, c.answer) for s, c in zip(samples, clues, strict=True)]
    return {
        "enum_fail_share": float(enum_fail_share(samples, clues)),
        "n": len(votes),
        "k": k,
        "model": model,
        "top1": float(top1(votes)),
        "ece": float(ece(votes, n_bins)),
        "n_bins": n_bins,
        "bins": [_bin_json(b) for b in reliability(votes, n_bins)],
        "clue_dates": [str(min(c.date for c in clues)), str(max(c.date for c in clues))]
        if clues else None,
        "items": [
            {"clue": c.text, "enumeration": format_enumeration(c.enumeration),
             "answer": c.answer, "prediction": v.prediction,
             "confidence": float(v.confidence), "correct": v.correct}
            for c, v in zip(clues, votes, strict=True)
        ],
    }


def enum_fail_share(samples: Sequence[Sequence[str]], clues: Sequence[CryptoniteClue]) -> Fraction:
    """Diagnostic, not a filter: share of samples with no letters or the wrong
    length for the enumeration (what brief 002's first check would prune)."""
    fails = sum(
        not normalise(a) or not c.enumeration.matches(a)
        for s, c in zip(samples, clues, strict=True) for a in s
    )
    total = sum(map(len, samples))
    return Fraction(fails, total) if total else Fraction(0)


def _bin_json(b: Bin) -> dict[str, Any]:
    def f(x: Fraction | None) -> float | None:
        return None if x is None else float(x)

    return {k: (v if isinstance(v, int) else f(v)) for k, v in asdict(b).items()}


def _total_refusals(log_path: pathlib.Path) -> int:
    records = read_log(log_path) if log_path.exists() else ()
    return sum(r["cost"].get("refusals", 0) for r in records)


def _total_usd(log_path: pathlib.Path) -> float | None:
    """Summed USD over the run's log; None if any call has no price."""
    costs = [r["cost"].get("usd") for r in read_log(log_path)] if log_path.exists() else []
    return None if any(c is None for c in costs) else sum(costs)


def _load_set(args: argparse.Namespace) -> tuple[tuple[CryptoniteClue, ...], int | None]:
    """The population to sample from, and (post-cutoff only) rows excluded by date."""
    if args.set == "postcutoff":
        return load_postcutoff(allow_postcutoff=args.allow_postcutoff, model=args.model)
    return load_cryptonite(args.set), None


def _backend(args: argparse.Namespace, log_path: pathlib.Path) -> Instrument:
    if args.backend == "stub":
        if args.log is None:
            raise SystemExit("--backend stub needs --log runs/<id>.jsonl")
        return logged(stub_backend(pathlib.Path(args.log)), log_path)
    live = ollama_backend() if args.backend == "ollama" else anthropic_backend()
    if args.log is not None:  # resume: replay what the log has, call the API for the rest
        return logged(replay_then(pathlib.Path(args.log), live), log_path)
    return logged(live, log_path)


def cmd_vote(args: argparse.Namespace) -> dict[str, Any]:
    started = datetime.now(UTC)
    run_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}-{args.backend}-{uuid.uuid4().hex}"
    runs = pathlib.Path(args.runs_dir)
    log_path = runs / f"{run_id}.jsonl"
    population, excluded_by_date = _load_set(args)
    if not population:
        raise SystemExit(f"set {args.set!r} is empty")
    indices = sample_indices(len(population), args.n, args.seed)
    clues = [population[i] for i in indices]
    summary = vote_run(
        clues, k=args.k, model=args.model, backend=_backend(args, log_path),
        n_bins=args.bins, workers=args.workers,
    )
    out = {
        "run_id": run_id,
        "set": args.set,
        "run_date": started.date().isoformat(),
        "backend": args.backend,
        "replayed_from": args.log,
        "seed": args.seed,
        "population": len(population),
        "indices": list(indices),
        "log": str(log_path),
        "excluded_by_date": excluded_by_date,
        "cost_usd": _total_usd(log_path),
        "refusals": _total_refusals(log_path),
        **summary,
    }
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{run_id}.json").write_text(json.dumps(out, indent="  ", ensure_ascii=False))
    return out


# --- brief 001: gold-parse coverage -----------------------------------------


def wordplay_clue(ex: WordplayExample) -> Clue:
    """The clue as the verifier sees it: definition braces removed."""
    return Clue(ex.clue.replace("{", "").replace("}", ""), parse_enumeration(ex.pattern))


def definition_text(ex: WordplayExample) -> str:
    return " / ".join(re.findall(r"\{([^}]*)\}", ex.clue))


def formalise_one(ex: WordplayExample, model: str, backend: Instrument, retries: int
                  ) -> dict[str, Any]:
    """Formalise one gold explanation, retrying on Reject with the verifier's
    hint; no retry when the parse names an operator the DSL lacks."""
    clue = wordplay_clue(ex)
    tokens = tuple(t.text for t in clue.tokens)
    previous: tuple[dict[str, str], ...] = ()
    for attempt in range(retries + 1):
        src = formalise_gold(ex.clue, ex.answer, definition_text(ex), ex.wordplay, model,
                             tokens=tokens, previous=previous, backend=backend)
        verdict = verify(clue, ex.answer, src)
        final = (not isinstance(verdict, Reject) or attempt == retries
                 or verdict.first_broken_rule.startswith("surface:unknown_operator"))
        if final:
            break
        previous = (*previous, {"src": src, "rule": verdict.first_broken_rule,
                                "hint": verdict.hint})
    return {"src": src, "verdict": verdict, "attempts": attempt + 1, "clue": clue}


def reject_family(rule: str) -> str:
    """Group Reject rules for the breakdown: the whole rule for an unknown
    operator (it names the missing operator), else just stage:check."""
    if rule.startswith("surface:unknown_operator"):
        return rule
    m = re.match(r"[^:]+(:[^:]+)?", rule)
    return m.group(0) if m else rule


def mutation_false_accepts(results: Sequence[dict[str, Any]]) -> tuple[int, int]:
    """(accepted mutants, mutants) over every accepted parse."""
    trials = [
        not isinstance(verify(r["clue"], answer, src), Reject)
        for r in results if not isinstance(r["verdict"], Reject)
        for _kind, answer, src in mutants(r["clue"].tokens[0].text, r["answer"], r["src"])
    ]
    return sum(trials), len(trials)


def coverage_run(examples: Sequence[WordplayExample], *, model: str, backend: Instrument,
                 retries: int, workers: int) -> dict[str, Any]:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda ex: formalise_one(ex, model, backend, retries),
                                examples))
    results = [{**r, "answer": ex.answer, "is_quick": ex.is_quick}
               for r, ex in zip(results, examples, strict=True)]
    accepted = [r for r in results if not isinstance(r["verdict"], Reject)]

    def share(rs: Sequence[dict[str, Any]]) -> float | None:
        ok = [r for r in rs if not isinstance(r["verdict"], Reject)]
        return len(ok) / len(rs) if rs else None

    false_accepts, n_mutants = mutation_false_accepts(results)
    return {
        "n": len(results),
        "model": model,
        "coverage": share(results),
        "coverage_quick": share([r for r in results if r["is_quick"]]),
        "coverage_hard": share([r for r in results if not r["is_quick"]]),
        "n_quick": sum(r["is_quick"] for r in results),
        "verdicts": dict(Counter(type(r["verdict"]).__name__ for r in results)),
        "wordplay_mechanical": sum(
            set(getattr(r["verdict"], "reasons", ())) <= {Reason.DEFINITION} for r in accepted),
        "quarantine_reasons": dict(Counter(
            reason.value for r in accepted for reason in getattr(r["verdict"], "reasons", ()))),
        "reject_rules": dict(Counter(
            reject_family(r["verdict"].first_broken_rule)
            for r in results if isinstance(r["verdict"], Reject)).most_common()),
        "attempts": dict(Counter(r["attempts"] for r in results)),
        "mutants": n_mutants,
        "mutant_false_accepts": false_accepts,
        "items": [
            {"answer": r["answer"], "src": r["src"], "attempts": r["attempts"],
             "verdict": type(r["verdict"]).__name__,
             "rule": getattr(r["verdict"], "first_broken_rule", None),
             "reasons": [x.value for x in getattr(r["verdict"], "reasons", ())]}
            for r in results
        ],
    }


def _formalise_backend(args: argparse.Namespace, log_path: pathlib.Path) -> Instrument:
    if args.backend == "stub":
        if args.log is None:
            raise SystemExit("--backend stub needs --log runs/<id>.jsonl")
        return logged(stub_backend(pathlib.Path(args.log)), log_path)
    live = budgeted(anthropic_backend(), args.max_usd)
    if args.log is not None:
        return logged(replay_then(pathlib.Path(args.log), live), log_path)
    return logged(live, log_path)


def load_wordplay_set(name: str, root: pathlib.Path | None = None) -> tuple[WordplayExample, ...]:
    return load_wordplay(name) if root is None else load_wordplay(name, root)


def cmd_coverage(args: argparse.Namespace) -> dict[str, Any]:
    started = datetime.now(UTC)
    run_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}-coverage-{args.backend}-{uuid.uuid4().hex}"
    runs = pathlib.Path(args.runs_dir)
    log_path = runs / f"{run_id}.jsonl"
    population = load_wordplay_set(args.set, pathlib.Path(args.root) if args.root else None)
    n = len(population) if args.n is None else args.n
    indices = sample_indices(len(population), n, args.seed)
    summary = coverage_run(
        [population[i] for i in indices], model=args.model,
        backend=_formalise_backend(args, log_path), retries=args.retries, workers=args.workers,
    )
    out = {
        "run_id": run_id, "set": f"wordplay-{args.set}", "run_date": started.date().isoformat(),
        "backend": args.backend, "replayed_from": args.log, "seed": args.seed,
        "population": len(population), "indices": list(indices), "log": str(log_path),
        "max_usd": args.max_usd, "cost_usd": _total_usd(log_path), **summary,
    }
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{run_id}.json").write_text(json.dumps(out, indent="  ", ensure_ascii=False))
    return out


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m ximenes.eval")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("vote", help="majority-vote baseline: top-1 and ECE")
    v.add_argument("--set", required=True, choices=(*SPLITS, "postcutoff"))
    v.add_argument("--n", type=int, default=PARAMS["n"])
    v.add_argument("--k", type=int, default=PARAMS["k"])
    v.add_argument("--model", required=True)
    v.add_argument("--backend", choices=("anthropic", "ollama", "stub"), default="anthropic")
    v.add_argument("--log", help="JSONL log to replay (stub), or to resume from (live backends)")
    v.add_argument("--seed", type=int, default=PARAMS["seed"])
    v.add_argument("--bins", type=int, default=PARAMS["bins"])
    v.add_argument("--workers", type=int, default=PARAMS["workers"])
    v.add_argument("--runs-dir", default="runs")
    v.add_argument("--allow-postcutoff", action="store_true",
                   help="required with --set postcutoff")
    c = sub.add_parser("coverage", help="brief 001: formalise gold wordplay, verify, cover")
    c.add_argument("--set", required=True, choices=("val", "train"),
                   help="wordplay sample split (Cryptonite test is never used here)")
    c.add_argument("--n", type=int, default=None, help="seeded subsample; default all")
    c.add_argument("--model", required=True)
    c.add_argument("--backend", choices=("anthropic", "stub"), default="anthropic")
    c.add_argument("--log", help="JSONL log to replay (stub), or to resume from (anthropic)")
    c.add_argument("--seed", type=int, default=PARAMS["seed"])
    c.add_argument("--retries", type=int, default=PARAMS["formalise_retries"])
    c.add_argument("--max-usd", type=float, default=PARAMS["max_usd"])
    c.add_argument("--workers", type=int, default=PARAMS["workers"])
    c.add_argument("--runs-dir", default="runs")
    c.add_argument("--root", help="directory holding sample_teacow_<set>.jsonl (fixtures)")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.cmd == "coverage":
        out = cmd_coverage(args)
        keys = ("run_id", "set", "run_date", "n", "model", "backend", "coverage",
                "coverage_quick", "coverage_hard", "verdicts", "wordplay_mechanical",
                "mutants", "mutant_false_accepts", "cost_usd", "log")
        print(json.dumps({k: out[k] for k in keys}, indent="  "))
        return 0
    out = cmd_vote(args)
    keys = ("run_id", "set", "run_date", "clue_dates", "n", "k", "model", "backend", "seed",
            "top1", "ece", "enum_fail_share", "refusals", "excluded_by_date", "cost_usd", "log")
    print(json.dumps({k: out[k] for k in keys}, indent="  "))
    return 0


if __name__ == "__main__":
    sys.exit(main())
