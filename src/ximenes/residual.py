"""Brief 015, Stages A0 and A: depth or enumeration on the residual.

The stuck slots are the uncommitted slots of 013's and 014's evaluation
grids whose gold the full solver's proposers never returned in any round,
with the final crossing pattern (the letters of committed crossers). The end state is
rebuilt by replaying each run's own log through the stub backend (no calls).

A0 ($0): the word list W (`data.load_wordlist`) cut by the enumeration and
the pattern; the mechanical generators on the clue's literal fodder (anagram
of contiguous words; hidden word, forwards and reversed), each generated
word given a DSL parse and verified. A: one proposer arm per slot.

    python -m ximenes.residual stuck        # counts only
    python -m ximenes.residual a0           # writes runs/015-a0.json; prints the summary
    python -m ximenes.residual arms --arm opus_high [--n N] [--log ...]
    python -m ximenes.residual summary      # Stage A table from the arm runs
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
import uuid
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .clue import Clue, Enumeration, normalise
from .data import format_enumeration, load_wordlist
from .eval import PARAMS
from .gridsolve import fits, load_grid, pattern_of
from .instruments import (
    SETTINGS,
    Instrument,
    choose_from_list,
    propose_pattern,
    propose_top,
)
from .verdict import Ok, Quarantine, Reject
from .verify import verify

CFG = PARAMS["residual"]
ARMS: dict[str, dict[str, Any]] = SETTINGS["residual_arms"]


# --- statistics (pure; integer Beta parameters) ------------------------------------------


def beta_cdf(x: float, a: int, b: int) -> float:
    """I_x(a, b) for integer a, b: P(Binomial(a + b - 1, x) >= a)."""
    n = a + b - 1
    return sum(math.comb(n, j) * x ** j * (1 - x) ** (n - j) for j in range(a, n + 1))


def beta_quantile(q: float, a: int, b: int) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(CFG["bisection_iters"]):
        mid = (lo + hi) / (1 + 1)
        lo, hi = (mid, hi) if beta_cdf(mid, a, b) < q else (lo, mid)
    return (lo + hi) / (1 + 1)


def beta_interval(hits: int, n: int, level: float = CFG["interval"]) -> tuple[float, float]:
    """Equal-tailed interval of Beta(1 + hits, 1 + n - hits)."""
    tail = (1 - level) / (1 + 1)
    a, b = 1 + hits, 1 + n - hits
    return beta_quantile(tail, a, b), beta_quantile(1 - tail, a, b)


def _lbeta(a: int, b: int) -> float:
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def p_greater(x: int, n: int, y: int, m: int) -> float:
    """P(p1 > p2) for p1 ~ Beta(1 + x, 1 + n - x), p2 ~ Beta(1 + y, 1 + m - y)
    (independent; the closed form for an integer first parameter)."""
    a1, b1, a2, b2 = 1 + y, 1 + m - y, 1 + x, 1 + n - x  # P(p2 < p1) = sum over a1
    return 1 - sum(math.exp(_lbeta(a2 + i, b1 + b2) - math.log(b1 + i) - _lbeta(1 + i, b1)
                            - _lbeta(a2, b2)) for i in range(a1))


# --- the stuck slots ---------------------------------------------------------------------


@dataclass(frozen=True)
class StuckSlot:
    grid: str
    key: str
    clue_text: str
    enumeration: Enumeration
    pattern: str  # final crossing pattern, "?" unknown
    gold: str

    @property
    def id(self) -> str:
        return f"{self.grid}|{self.key}"

    @property
    def parts(self) -> tuple[int, ...]:
        return self.enumeration.parts


def proposed_answers(instrument: str, output: Any) -> list[str]:
    """Every answer a proposer call returned (sample lists, ranked lists
    one per line); [] for any other instrument."""
    from .instruments import PROPOSE_ANSWERS, PROPOSE_LIST, PROPOSE_PATTERN

    if instrument in (PROPOSE_ANSWERS, PROPOSE_PATTERN):
        return [normalise(str(a)) for a in output]
    if instrument == PROPOSE_LIST:
        return [normalise(a) for a in str(output).splitlines()]
    return []


def _end_state(brief: str, gdoc: Mapping[str, Any], path: pathlib.Path,
               log: pathlib.Path) -> tuple[Any, dict[str, set[str]]]:
    """The full solver's final GridRun for one grid, by stub replay, and
    every answer proposed for each clue text in any round."""
    from . import last_slots
    from .e2e import CFG as E2E
    from .e2e import e2e_tables
    from .instruments import memoized, metered, stub_backend

    grid, clues = load_grid(path)
    replay = stub_backend(log, on_conflict="first")
    seen: dict[str, set[str]] = {}

    def recording(instrument: str, model: str, inp: Mapping[str, Any]) -> Any:
        output, cost = replay(instrument, model, inp)
        seen.setdefault(str(inp.get("clue_text")), set()).update(
            proposed_answers(instrument, output))
        return output, cost

    memo = memoized(recording)
    backend, totals = metered(memo)
    tables, gain = e2e_tables()
    models = {"proposer": SETTINGS["solve_models"]["proposer"],
              "formaliser": SETTINGS["solve_models"]["formaliser"],
              "judge": SETTINGS["judges"]["model"]}
    if brief == "013":
        from .policy import GridRun

        g = GridRun(gdoc["puzzle"], grid, clues, backend, totals, tables, models, warm=memo,
                    proposer=E2E["proposer"])
        g.run("voc", gain, gain["rho"]["rho"], E2E["budget_usd"])
    else:
        g = last_slots.PersistentSolver(gdoc["puzzle"], grid, clues, backend, totals, tables,
                                        models, warm=memo, proposer=E2E["proposer"])
        budget = last_slots.CFG["budget_usd"]
        g.run("voc", gain, gain["rho"]["rho"], budget)
        g.persist(budget)
    if abs(totals[0] - gdoc["usd"]) > CFG["replay_usd_tol"]:
        raise ValueError(f"{gdoc['puzzle']}: replay spent {totals[0]}, the run {gdoc['usd']}")
    return g, seen


def stuck_of(g: Any, proposed: Mapping[str, set[str]]) -> list[tuple[str, str]]:
    """(slot, final pattern) for uncommitted slots whose gold no proposer
    call returned in any round (lead's amendment: committed-wrong slots are
    not stuck)."""
    letters = {c: g.commits[o][i] for o in g.commits for i, c in enumerate(g.s[o].slot.cells)}
    return [(k, pattern_of(s.slot, letters)) for k, s in g.s.items()
            if k not in g.commits and g.gold[k] not in proposed.get(s.clue.text, set())
            and g.gold[k] not in {a for a, _ in s.votes} | {h["answer"] for h in s.cands}]


def stuck_slots(runs_dir: pathlib.Path = pathlib.Path("runs")) -> list[StuckSlot]:
    """Every stuck slot of the two full-solver runs named in data/eval.json,
    cached in runs/015-stuck.json (slot ids and patterns only)."""
    from .e2e import grids

    paths = {p.stem: p for p in grids()[0]}
    cache = runs_dir / CFG["stuck_cache"]
    if not cache.exists():
        found: list[dict[str, str]] = []
        for brief, run_id in sorted(CFG["stuck_runs"].items()):
            doc = json.loads((runs_dir / f"{run_id}.json").read_text())
            log = runs_dir / f"{run_id}.jsonl"

            def one(gdoc: Mapping[str, Any], brief: str = brief,
                    log: pathlib.Path = log) -> list[dict[str, str]]:
                g, proposed = _end_state(brief, gdoc, paths[gdoc["puzzle"]], log)
                return [{"brief": brief, "grid": gdoc["puzzle"], "slot": k, "pattern": p}
                        for k, p in stuck_of(g, proposed)]

            with ThreadPoolExecutor(max_workers=CFG["replay_workers"]) as pool:
                found += [r for rs in pool.map(one, doc["grids"]) for r in rs]
        cache.write_text(json.dumps(found, indent=1))
    out = []
    for r in json.loads(cache.read_text()):
        _grid, clues = load_grid(paths[r["grid"]])
        c = clues[r["slot"]]
        out.append(StuckSlot(r["grid"], r["slot"], c.text, c.enumeration, r["pattern"],
                             normalise(c.answer)))
    return out


# --- A0: enumeration and the DSL as generator ----------------------------------------------


def in_pattern(words: frozenset[str], pattern: str) -> list[str]:
    return sorted(w for w in words if fits(w, pattern))


def _q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def _tok(clue: Clue, ids: Sequence[int]) -> str:
    return f"tok({', '.join(_q(clue.tokens[i].text) for i in ids)})"


def _letters(clue: Clue, ids: Sequence[int]) -> str:
    return normalise("".join(clue.tokens[i].text for i in ids))


def spans(n: int) -> Iterator[tuple[int, int]]:
    return ((i, j) for i in range(n) for j in range(i + 1, n + 1))


def anagram_words(clue: Clue, length: int) -> list[tuple[str, tuple[int, int]]]:
    """(sorted letters, span) for every contiguous token span with the
    answer's letter count: an anagram of it is a generated candidate."""
    n = len(clue.tokens)
    return [("".join(sorted(_letters(clue, range(i, j)))), (i, j)) for i, j in spans(n)
            if len(_letters(clue, range(i, j))) == length]


def hidden_words(clue: Clue, length: int) -> list[tuple[str, tuple[int, int], bool]]:
    """(word, span, reversed) for every run of `length` letters inside a
    contiguous token span, starting in its first token and ending in its
    last, forwards and reversed; a whole single token is a literal, not a
    hidden word."""
    out = []
    n = len(clue.tokens)
    for i, j in spans(n):
        s = _letters(clue, range(i, j))
        first, last = len(_letters(clue, [i])), len(_letters(clue, [j - 1]))
        for o in range(len(s) - length + 1):
            if o >= first or o + length <= len(s) - last or (j - i == 1 and length == len(s)):
                continue
            w = s[o:o + length]
            out += [(w, (i, j), False), (w[::-1], (i, j), True)]
    return out


def _layouts(n: int, a: int, b: int) -> Iterator[tuple[list[int], list[int], list[int]]]:
    """(indicator ids, definition ids, link ids) around a fodder span [a, b):
    an indicator of up to CFG's tokens touching the fodder, the definition
    at the clue's other end, and at most CFG's link tokens between."""
    for k in range(1, CFG["indicator_max_tokens"] + 1):
        for ind in (list(range(a - k, a)), list(range(b, b + k))):
            if not ind or min(ind) < 0 or max(ind) >= n:
                continue
            lo, hi = min(a, *ind), max(b - 1, *ind)
            for links in range(CFG["link_max_tokens"] + 1):
                if lo == 0 and hi + 1 + links < n:  # definition at the end
                    yield ind, list(range(hi + 1 + links, n)), list(range(hi + 1, hi + 1 + links))
                if hi == n - 1 and lo - links > 0:  # definition at the start
                    yield ind, list(range(0, lo - links)), list(range(lo - links, lo))


def _wrap(clue: Clue, d: list[int], links: list[int], wordplay: str) -> str:
    tail = "".join(f", link({_tok(clue, [i])})" for i in links)
    return f"clue(defn({_tok(clue, d)}), {wordplay}{tail})"


def parses(clue: Clue, word: str, how: str, span: tuple[int, int]) -> Iterator[str]:
    """DSL sources giving `word` from a generator hit: `anagram`, `hidden`
    or `hidden_reversed` (two indicator tokens, reversal then hidden)."""
    a, b = span
    fodder = _tok(clue, range(a, b))
    for ind, d, links in _layouts(len(clue.tokens), a, b):
        if how == "anagram":
            yield _wrap(clue, d, links, f"anagram({_tok(clue, ind)}, lit({fodder}), {_q(word)})")
        elif how == "hidden":
            yield _wrap(clue, d, links, f"hidden({_tok(clue, ind)}, {fodder}, {_q(word)})")
        elif len(ind) == 1 + 1:
            for r, h in ((ind[0], ind[1]), (ind[1], ind[0])):
                inner = f"hidden({_tok(clue, [h])}, {fodder}, {_q(word[::-1])})"
                yield _wrap(clue, d, links, f"reverse({_tok(clue, [r])}, {inner})")


_RANK = {"Ok": 0, "Quarantine": 1}


def best_verdict(clue: Clue, word: str, hits: Sequence[tuple[str, tuple[int, int]]]
                 ) -> str | None:
    """The best status ("Ok" before "Quarantine") of any generated parse of
    `word`, or None if every parse is rejected."""
    best = None
    for how, span in hits:
        for src in parses(clue, word, how, span):
            v = verify(clue, word, src)
            if isinstance(v, Ok):
                return "Ok"
            if isinstance(v, Quarantine):
                best = "Quarantine"
            assert isinstance(v, Ok | Quarantine | Reject)
    return best


def generated(clue: Clue, length: int, words: frozenset[str] | None
              ) -> dict[str, list[tuple[str, tuple[int, int]]]]:
    """word -> generator hits. Anagrams are listed only for words in
    `words` (an anagram has no other finite candidate set); hidden words
    are listed whether or not they are in it (None: no filter)."""
    out: dict[str, list[tuple[str, tuple[int, int]]]] = {}
    if words is not None:
        index: dict[str, list[str]] = {}
        for w in words:
            index.setdefault("".join(sorted(w)), []).append(w)
        for key, span in anagram_words(clue, length):
            for w in index.get(key, []):
                out.setdefault(w, []).append(("anagram", span))
    for w, span, rev in hidden_words(clue, length):
        if words is None or w in words:
            out.setdefault(w, []).append(("hidden_reversed" if rev else "hidden", span))
    return out


def a0_row(s: StuckSlot, wordlist: Mapping[tuple[int, ...], frozenset[str]]) -> dict[str, Any]:
    """One stuck slot's A0 numbers, and its admitted words (kept in runs/
    only: they are post-cutoff-derived)."""
    clue = Clue(s.clue_text, s.enumeration)
    w = wordlist.get(s.parts, frozenset())
    cut = frozenset(in_pattern(w, s.pattern))
    gen = generated(clue, s.enumeration.length, cut)
    admitted = {x: st for x in sorted(gen) if x in cut
                and (st := best_verdict(clue, x, gen[x])) is not None}
    gold_anagram = any(k == "".join(sorted(s.gold))
                       for k, _ in anagram_words(clue, s.enumeration.length))
    gold_hidden = any(x == s.gold for x, _sp, _r in hidden_words(clue, s.enumeration.length))
    return {"id": s.id, "in_w": s.gold in w, "fits_pattern": fits(s.gold, s.pattern),
            "in_w_pattern": s.gold in cut, "n_w_pattern": len(cut),
            "known_letters": sum(ch != "?" for ch in s.pattern),
            "gold_anagram": gold_anagram, "gold_hidden": gold_hidden,
            "n_admitted": len(admitted), "n_ok": sum(v == "Ok" for v in admitted.values()),
            "gold_admitted": admitted.get(s.gold), "admitted": admitted,
            "gold_in_a0_top": s.gold in a0_ranked({"admitted": admitted})[:CFG["top"]]}


def a0_ranked(row: Mapping[str, Any]) -> list[str]:
    """The generator-plus-verifier arm's ranked list: Ok before Quarantine,
    then alphabetical."""
    return sorted(row["admitted"], key=lambda x: (_RANK[row["admitted"][x]], x))


def _dist(xs: Sequence[int]) -> dict[str, Any]:
    ys = sorted(xs)
    if not ys:
        return {}
    return {"min": ys[0], "median": ys[(len(ys) - 1) >> 1], "max": ys[-1],
            "bins": {f"<={edge}": sum(y <= edge for y in ys) for edge in CFG["size_bins"]}}


def a0_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    n = len(rows)

    def rate(key: str, sel: Sequence[Mapping[str, Any]] = rows) -> dict[str, Any]:
        hits = sum(bool(r[key]) for r in sel)
        return {"hits": hits, "n": len(sel), "interval": beta_interval(hits, len(sel))}

    top = CFG["top"]
    arm_hits = sum(r["gold_in_a0_top"] for r in rows)
    return {
        "n": n,
        "gold_in_w": rate("in_w"),
        "gold_fits_pattern": rate("fits_pattern"),
        "gold_in_w_pattern": rate("in_w_pattern"),
        "w_pattern_size": _dist([r["n_w_pattern"] for r in rows]),
        "gold_anagram_of_fodder": rate("gold_anagram"),
        "gold_hidden_in_fodder": rate("gold_hidden"),
        "admitted_size": _dist([r["n_admitted"] for r in rows]),
        "gold_admitted": {**rate("gold_admitted"),
                          "ok": sum(r["gold_admitted"] == "Ok" for r in rows)},
        "a0_arm_gold_in_top": {"top": top, "hits": arm_hits, "n": n,
                               "interval": beta_interval(arm_hits, n)},
        "misses": {"not_in_w": sum(not r["in_w"] for r in rows),
                   "in_w_but_pattern_excludes": sum(r["in_w"] and not r["in_w_pattern"]
                                                    for r in rows),
                   "in_w_pattern_not_admitted": sum(r["in_w_pattern"]
                                                    and not r["gold_admitted"] for r in rows),
                   "in_w_pattern_admitted": sum(bool(r["gold_admitted"]) for r in rows)},
        "list_max": CFG["list_max"],
        "over_list_max": sum(r["n_w_pattern"] > CFG["list_max"] for r in rows),
    }


# --- Stage A: the arms ------------------------------------------------------------------


def _valid(s: StuckSlot, answers: Sequence[str]) -> list[str]:
    return [a for a in map(normalise, answers) if s.enumeration.matches(a)]


def ask(arm: str, s: StuckSlot, backend: Instrument,
        wordlist: Mapping[tuple[int, ...], frozenset[str]] | None = None,
        admitted: Mapping[str, str] | None = None) -> dict[str, Any]:
    """One arm on one slot: its ranked answers with shares (enumeration-valid
    only; not filtered by the pattern, which may hold a wrong letter), and
    the OTHER share where the arm states one."""
    cfg = ARMS[arm]
    enum = format_enumeration(s.enumeration)
    if cfg["kind"] == "resample":
        assert cfg["effort"] == SETTINGS["propose_pattern"]["effort"]  # 014's instrument
        samples = propose_pattern(s.clue_text, enum, s.pattern, cfg["k"], cfg["model"],
                                  backend=backend, fmt=cfg["format"])
        valid = _valid(s, samples)
        counts = Counter(valid)
        first = {a: i for i, a in reversed(list(enumerate(valid)))}
        ranked = sorted(counts, key=lambda a: (-counts[a], first[a]))
        return {"ranked": ranked, "shares": [counts[a] / len(samples) for a in ranked],
                "other": None}
    if cfg["kind"] == "top":
        out = propose_top(s.clue_text, enum, s.pattern, cfg["n"], cfg["model"], cfg["effort"],
                          cfg["max_tokens"], backend=backend)
        return _shares(s, out["candidates"], None)
    assert wordlist is not None and admitted is not None
    words = in_pattern(wordlist.get(s.parts, frozenset()), s.pattern)
    if len(words) > CFG["list_max"]:
        return {"ranked": [], "shares": [], "other": None, "skipped": "list_over_max"}
    shown = [_spaced(w, s.parts) + (f" [{admitted[w]}]" if w in admitted else "")
             for w in words]
    out = choose_from_list(s.clue_text, enum, s.pattern, shown, cfg["n"], cfg["model"],
                           cfg["effort"], cfg["max_tokens"], backend=backend)
    res = _shares(s, out["candidates"], out.get("other"))
    listed = set(words)
    res["off_list"] = [a for a in res["ranked"] if a not in listed]
    keep = [i for i, a in enumerate(res["ranked"]) if a in listed]
    res["ranked"] = [res["ranked"][i] for i in keep]
    res["shares"] = [res["shares"][i] for i in keep]
    return res


def _spaced(word: str, parts: Sequence[int]) -> str:
    out, i = [], 0
    for p in parts:
        out.append(word[i:i + p])
        i += p
    return " ".join(out)


def _shares(s: StuckSlot, cands: Sequence[Mapping[str, Any]], other: float | None
            ) -> dict[str, Any]:
    seen: dict[str, float] = {}
    for c in cands:
        a = normalise(str(c.get("answer", "")))
        if s.enumeration.matches(a) and a not in seen:
            seen[a] = float(c.get("share") or 0.0)
    ranked = sorted(seen, key=lambda a: -seen[a])  # stable: the model's order breaks ties
    return {"ranked": ranked, "shares": [seen[a] for a in ranked], "other": other}


def union(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, Any]:
    """Arm 6: two arms' answers with their shares averaged (absent = 0),
    ranked by the average; ties go to `a`'s order."""
    sa = dict(zip(a["ranked"], a["shares"], strict=True))
    sb = dict(zip(b["ranked"], b["shares"], strict=True))
    words = list(dict.fromkeys([*a["ranked"], *b["ranked"]]))
    avg = {w: (sa.get(w, 0.0) + sb.get(w, 0.0)) / (1 + 1) for w in words}
    ranked = sorted(words, key=lambda w: -avg[w])
    return {"ranked": ranked, "shares": [avg[w] for w in ranked], "other": None}


def score(results: Mapping[str, Mapping[str, Any]], gold: Mapping[str, str],
          ks: Sequence[int]) -> dict[str, Any]:
    """gold-in-k with Beta(1,1) intervals, and the top share where the top
    answer is wrong (Stage B's calibration needs it)."""
    n = len(results)
    out: dict[str, Any] = {"n": n}
    for k in ks:
        hits = sum(gold[i] in r["ranked"][:k] for i, r in results.items())
        out[f"gold_in_{k}"] = {"hits": hits, "rate": hits / n if n else None,
                               "interval": beta_interval(hits, n)}
    wrong = [r["shares"][0] for i, r in results.items() if r["ranked"]
             and r["ranked"][0] != gold[i]]
    right = [r["shares"][0] for i, r in results.items() if r["ranked"]
             and r["ranked"][0] == gold[i]]
    out["top_share_when_wrong"] = {"n": len(wrong), "mean": sum(wrong) / len(wrong)
                                   if wrong else None}
    out["top_share_when_right"] = {"n": len(right), "mean": sum(right) / len(right)
                                   if right else None}
    out["empty"] = sum(not r["ranked"] for r in results.values())
    return out


def run_arm(arm: str, slots: Sequence[StuckSlot], backend: Instrument,
            a0: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    wordlist = load_wordlist() if ARMS[arm]["kind"] == "choose" else None

    def one(s: StuckSlot) -> tuple[str, dict[str, Any]]:
        try:
            return s.id, ask(arm, s, backend, wordlist, a0[s.id]["admitted"])
        except Exception as e:  # noqa: BLE001 - recorded per slot, never silently dropped
            return s.id, {"ranked": [], "shares": [], "other": None,
                          "error": f"{type(e).__name__}: {e}"}

    with ThreadPoolExecutor(max_workers=CFG["slot_workers"]) as pool:
        return dict(pool.map(one, slots))


def eligible(arm: str, slots: Sequence[StuckSlot]) -> list[StuckSlot]:
    """012's post-cutoff rule for the arm's model (brief 015: applied to
    Fable's knowledge cutoff, an upper bound in data/instruments.json)."""
    from .e2e import grids

    ok = {p.stem for p in grids(ARMS[arm]["model"])[0]}
    return [s for s in slots if s.grid in ok]


def main(argv: Sequence[str] | None = None) -> int:
    from .policy import _backend

    p = argparse.ArgumentParser(prog="python -m ximenes.residual")
    p.add_argument("step", choices=("stuck", "a0", "arms", "summary"))
    p.add_argument("--arm", choices=sorted(ARMS), default=None)
    p.add_argument("--n", type=int, default=None, help="first n stuck slots (the smoke test)")
    p.add_argument("--backend", choices=("anthropic", "stub"), default="anthropic")
    p.add_argument("--log", nargs="*", default=[])
    p.add_argument("--offline", action="store_true")
    p.add_argument("--max-usd", type=float, default=CFG["cap_usd"])
    p.add_argument("--runs-dir", default="runs")
    args = p.parse_args(argv)
    runs = pathlib.Path(args.runs_dir)
    slots = stuck_slots(runs)
    if args.step == "stuck":
        print(json.dumps({"n": len(slots), "by_brief": dict(Counter(
            r["brief"] for r in json.loads((runs / CFG["stuck_cache"]).read_text())))}))
        return 0
    a0_path = runs / CFG["a0_file"]
    if args.step == "a0":
        wl = load_wordlist()
        rows = [a0_row(s, wl) for s in slots]
        a0_path.write_text(json.dumps(rows, indent=1))
        print(json.dumps(a0_summary(rows), indent=1))
        return 0
    a0 = {r["id"]: r for r in json.loads(a0_path.read_text())}
    if args.step == "summary":
        print(json.dumps(stage_a_summary(slots, a0, runs), indent=1))
        return 0
    assert args.arm is not None
    todo = eligible(args.arm, slots)[:args.n]
    started = datetime.now(UTC)
    run_id = (f"{started.strftime('%Y%m%dT%H%M%SZ')}-residual-{args.arm}-{args.backend}-"
              f"{uuid.uuid4().hex}")
    backend, totals, _memo = _backend(args, runs / f"{run_id}.jsonl")
    results = run_arm(args.arm, todo, backend, a0)
    doc = {"run_id": run_id, "arm": args.arm, "settings": ARMS[args.arm], "usd": totals[0],
           "n": len(todo), "full": args.n is None, "slots": results}
    (runs / f"{run_id}.json").write_text(json.dumps(doc, indent=1))
    gold = {s.id: s.gold for s in todo}
    print(json.dumps({"run_id": run_id, "usd": totals[0],
                      "usd_per_slot": totals[0] / max(1, len(todo)),
                      "errors": sum("error" in r for r in results.values()),
                      **score(results, gold, CFG["ks"])}, indent=1))
    return 0


def latest_runs(runs: pathlib.Path) -> dict[str, dict[str, Any]]:
    """Per arm, the last live run over all its eligible slots."""
    out: dict[str, dict[str, Any]] = {}
    for f in sorted(runs.glob("*-residual-*-anthropic-*.json")):
        doc = json.loads(f.read_text())
        if doc.get("full"):
            out[doc["arm"]] = doc
    return out


def stage_a_summary(slots: Sequence[StuckSlot], a0: Mapping[str, Mapping[str, Any]],
                    runs: pathlib.Path) -> dict[str, Any]:
    gold = {s.id: s.gold for s in slots}
    docs = latest_runs(runs)
    table: dict[str, Any] = {}
    for arm, doc in sorted(docs.items()):
        table[arm] = {**score(doc["slots"], gold, CFG["ks"]), "usd": doc["usd"],
                      "usd_per_slot": doc["usd"] / max(1, doc["n"]),
                      "skipped": sum(r.get("skipped") is not None
                                     for r in doc["slots"].values()),
                      "errors": sum("error" in r for r in doc["slots"].values())}
    a0_arm = {i: {"ranked": a0_ranked(r), "shares": [1.0] * len(r["admitted"]),
                  "other": None} for i, r in a0.items()}
    table["a0_generator_verifier"] = {**score(a0_arm, gold, CFG["ks"]), "usd": 0.0}
    depth = [a for a in CFG["depth_arms"] if a in docs]
    if "choose_list" in docs and depth:
        best = max(depth, key=lambda a: (table[a][f"gold_in_{CFG['top']}"]["hits"],
                                         -table[a]["usd"]))
        both = {i: union(docs["choose_list"]["slots"][i], docs[best]["slots"][i])
                for i in docs[best]["slots"] if i in docs["choose_list"]["slots"]}
        table["union"] = {**score(both, gold, CFG["ks"]), "with": best, "usd": 0.0}
    return {"arms": table, "decision": decide(table)}


def decide(table: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """The brief's rule on r = gold-in-5 of the best arm (A0 counts, at $0)."""
    key = f"gold_in_{CFG['top']}"
    rule = CFG["decision"]
    lows = {a: t[key]["interval"][0] for a, t in table.items()}
    highs = {a: t[key]["interval"][1] for a, t in table.items()}
    best = max(table, key=lambda a: (table[a][key]["hits"] / max(1, table[a]["n"]),
                                     -table[a]["usd"]))
    if lows[best] >= rule["run_b_lower"]:
        tied = [a for a in table if highs[a] >= table[best][key]["rate"]
                and lows[a] >= rule["run_b_lower"]]
        pick = min(tied, key=lambda a: (table[a]["usd"], a))
        return {"band": "run_b", "best": best, "arm_for_b": pick}
    if all(h < rule["no_reach_upper"] for h in highs.values()):
        return {"band": "depth_does_not_reach", "best": best}
    return {"band": "report_and_stop", "best": best}

if __name__ == "__main__":
    sys.exit(main())
