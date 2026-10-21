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
import sys
import uuid
from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from fractions import Fraction
from typing import Any

from .clue import normalise
from .data import DATA, SPLITS, CryptoniteClue, format_enumeration, load_cryptonite, read_cryptonite
from .instruments import (
    SETTINGS,
    Instrument,
    anthropic_backend,
    logged,
    ollama_backend,
    propose_answers,
    read_log,
    replay_then,
    stub_backend,
)

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
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    out = cmd_vote(args)
    keys = ("run_id", "set", "run_date", "clue_dates", "n", "k", "model", "backend", "seed",
            "top1", "ece", "enum_fail_share", "refusals", "excluded_by_date", "cost_usd", "log")
    print(json.dumps({k: out[k] for k in keys}, indent="  "))
    return 0


if __name__ == "__main__":
    sys.exit(main())
