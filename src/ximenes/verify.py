"""Non-executing verifier (DESIGN D2–D4).

Stage 1 (`surface`): parse with `ast`, accept only the allowlisted node
types, and resolve every call to the operator table. Stages 2–5 (brief 001):
sorts, token resolution and evaluation, coverage, answer.
"""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass

from .clue import Clue, normalise
from .data import abbreviations, indicators
from .dsl import OPERATORS, TOP_LEVEL, Op, Sort
from .verdict import Ok, Provenance, Quarantine, Reason, Reject, Verdict

# --- Stage 1: surface -------------------------------------------------------

_ALLOWED = (ast.Expression, ast.Call, ast.Name, ast.Constant, ast.Load)


@dataclass(frozen=True)
class CallNode:
    op: Op
    args: tuple[CallNode | str, ...]


def surface(src: str) -> CallNode | Reject:
    """Parse source to a tree of operator calls, or Reject at the first rule broken.

    Impossible by construction: comments-only bodies (not an expression),
    conditionals, boolean/comparison operators (so `x == False` has no
    meaning), assignments, attribute access, keywords, star-args, imports.
    """
    try:
        tree = ast.parse(src.strip(), mode="eval")
    except SyntaxError as e:
        return Reject(f"surface:SyntaxError:{e.msg}")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED):
            return Reject(f"surface:{type(node).__name__}")
        if isinstance(node, ast.Constant) and not isinstance(node.value, str):
            return Reject(f"surface:Constant:{type(node.value).__name__}")
        if isinstance(node, ast.Call):
            if node.keywords:
                return Reject("surface:keyword")
            if not isinstance(node.func, ast.Name):
                return Reject(f"surface:func:{type(node.func).__name__}")
    body = tree.body
    if not isinstance(body, ast.Call):
        return Reject(f"surface:top:{type(body).__name__}")
    return _lower(body)


def _lower(node: ast.expr) -> CallNode | str | Reject:
    if isinstance(node, ast.Constant):
        return node.value
    assert isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    name = node.func.id
    op = OPERATORS.get(name)
    if op is None:
        return Reject(f"surface:unknown_operator:{name}")
    args: list[CallNode | str] = []
    for a in node.args:
        if isinstance(a, ast.Name):
            return Reject(f"surface:bare_name:{a.id}")
        low = _lower(a)
        if isinstance(low, Reject):
            return low
        args.append(low)
    if op.variadic:
        if len(args) < 1:
            return Reject(f"arity:{name}")
    elif len(args) < len(op.args) or (len(args) > len(op.args) and not op.extras):
        return Reject(f"arity:{name}:expected_{len(op.args)}_got_{len(args)}")
    return CallNode(op, tuple(args))


# --- Stages 2–5 -------------------------------------------------------------
#
# 2 sorts: arguments match the operator table; a bare string is a Claim and
#   may stand only where a Claim is expected (never as fodder).
# 3 tokens: tok(...) spans are resolved to clue token ids (the k-th use of a
#   word sequence takes its k-th occurrence), then operators are evaluated over
#   sets of candidate strings; indicator and abbreviation tables are consulted.
# 4 coverage (DESIGN D3): every clue token consumed exactly once, twice if
#   declared with double_duty(...).
# 5 answer: the top-level candidates contain the answer, which fits the
#   enumeration.


class _Broken(Exception):
    """A rule was broken; becomes Reject(rule, hint). Internal to this module."""

    def __init__(self, rule: str, hint: str = "") -> None:
        super().__init__(rule)
        self.rule = rule
        self.hint = hint


@dataclass(frozen=True)
class Tok:
    ids: tuple[int, ...]
    words: tuple[str, ...]

    @property
    def phrase(self) -> str:
        return " ".join(self.words).lower()

    @property
    def letters(self) -> str:
        return normalise("".join(self.words))


@dataclass(frozen=True)
class Val:
    sort: Sort
    cands: frozenset[str] = frozenset()
    tok: Tok | None = None
    reasons: frozenset[Reason] = frozenset()
    uses: tuple[int, ...] = ()
    links: frozenset[int] = frozenset()
    definition: frozenset[int] = frozenset()
    double: frozenset[int] = frozenset()


def _sort_of(arg: CallNode | str) -> Sort:
    return Sort.CLAIM if isinstance(arg, str) else arg.op.result


def _typecheck(node: CallNode, parent: str | None = None, index: int = 0) -> None:
    op = node.op
    if parent is None and op.name not in TOP_LEVEL:
        raise _Broken(f"sort:top:{op.name}",
                      "a parse is clue(...), double_def(...), cryptic_def(...) or andlit(...)")
    if parent is not None and op.name in TOP_LEVEL:
        raise _Broken(f"sort:nested:{op.name}")
    if op.name == "defn" and not (parent == "clue" and index == 0):
        raise _Broken("sort:defn:placement", "defn(...) is only the first argument of clue(...)")
    if op.name == "clue" and _sort_of(node.args[0]) == Sort.STR:
        first = node.args[0]
        if not (isinstance(first, CallNode) and first.op.name == "defn"):
            raise _Broken("sort:clue:first_arg_not_defn")
    fixed = tuple(op.args[0] for _ in node.args) if op.variadic else op.args
    for i, (arg, want) in enumerate(zip(node.args, fixed, strict=False)):
        got = _sort_of(arg)
        if got != want:
            raise _Broken(f"sort:{op.name}:arg{i}:expected_{want.value}_got_{got.value}")
    for arg in node.args[len(fixed):]:
        if _sort_of(arg) not in op.extras:
            raise _Broken(f"sort:{op.name}:extra:{_sort_of(arg).value}",
                          "only link(...) and double_duty(...) may follow the fixed arguments")
    for i, arg in enumerate(node.args):
        if isinstance(arg, CallNode):
            _typecheck(arg, op.name, i)


def _key(word: str) -> str:
    return word.lower().replace("’", "'")


def _resolve(node: CallNode | str, clue: Clue, seen: dict[tuple[str, ...], int]
             ) -> tuple[CallNode | str | Tok, dict[tuple[str, ...], int]]:
    """Replace tok(...) nodes by Tok, in preorder; `seen` counts uses per span."""
    if isinstance(node, str):
        return node, seen
    if node.op.name == "tok":
        words = tuple(_key(w) for a in node.args for w in str(a).split())
        tokens = clue.tokens
        starts = [i for i in range(len(tokens) - len(words) + 1)
                  if all(tokens[i + j].key.replace("’", "'") == w for j, w in enumerate(words))]
        k = seen.get(words, 0)
        if k >= len(starts):
            raise _Broken(f"tok:not_found:{' '.join(words)}",
                          f"no{' further' if k else ''} contiguous clue tokens {' '.join(words)!r}")
        start = starts[k]
        ids = tuple(range(start, start + len(words)))
        return Tok(ids, tuple(tokens[i].text for i in ids)), {**seen, words: k + 1}
    args: list[CallNode | str | Tok] = []
    for a in node.args:
        r, seen = _resolve(a, clue, seen)
        args.append(r)
    return CallNode(node.op, tuple(args)), seen  # type: ignore[arg-type]


def _merge(vals: tuple[Val, ...]) -> Val:
    return Val(
        sort=Sort.STR,
        reasons=frozenset().union(*(v.reasons for v in vals)),
        uses=tuple(i for v in vals for i in v.uses),
        links=frozenset().union(*(v.links for v in vals)),
        definition=frozenset().union(*(v.definition for v in vals)),
        double=frozenset().union(*(v.double for v in vals)),
    )


def _claim(s: str) -> str:
    c = normalise(s)
    if not c:
        raise _Broken("claim:empty", f"claimed string {s!r} has no letters")
    return c


def _middle_removed(s: str) -> str:
    half = len(s) >> 1
    return s[:half] + s[half + 1:] if len(s) & 1 else s[:half - 1] + s[half + 1:]


def _insertions(inner: str, outer: str) -> frozenset[str]:
    return frozenset(outer[:i] + inner + outer[i:] for i in range(1, len(outer)))


def _alternates(s: str) -> frozenset[str]:
    return frozenset(
        x for x in ("".join(c for i, c in enumerate(s) if not i & 1),
                    "".join(c for i, c in enumerate(s) if i & 1)) if x
    )


def _abbr_ok(t: Tok, claim: str) -> bool:
    table = abbreviations()
    keys = {t.phrase, t.phrase.replace("’", "'").removesuffix("'s")}
    return any(claim in table.get(k, frozenset()) for k in keys)


def _eval(node: CallNode | str | Tok) -> Val:
    if isinstance(node, Tok):
        return Val(Sort.TOK, tok=node, uses=node.ids)
    if isinstance(node, str):
        return Val(Sort.CLAIM)
    name = node.op.name
    vals = tuple(map(_eval, node.args))
    base = _merge(vals)
    if node.op.indicated:
        ind = vals[0].tok
        assert ind is not None
        if ind.phrase not in indicators().get(name, frozenset()):
            base = Val(**{**base.__dict__, "reasons": base.reasons | {Reason.INDICATOR}})
    if node.op.oracle is not None:
        base = Val(**{**base.__dict__, "reasons": base.reasons | {node.op.oracle}})
    cands = _OPS[name](node, vals)
    toks = [v.tok for v in vals if v.tok is not None]
    if name == "link":
        return Val(Sort.NULL, uses=toks[0].ids, links=frozenset(toks[0].ids))
    if name == "double_duty":
        return Val(Sort.MODE, double=frozenset(toks[0].ids))
    if name in ("defn", "double_def", "cryptic_def"):
        span = (toks[0], toks[1]) if name == "double_def" else (toks[0],)
        base = Val(**{**base.__dict__,
                      "definition": base.definition | {i for t in span for i in t.ids}})
    if name == "andlit":
        base = Val(**{**base.__dict__, "definition": frozenset(base.uses)})
    return Val(**{**base.__dict__, "cands": cands})


def _one(vals: tuple[Val, ...], i: int) -> frozenset[str]:
    return vals[i].cands


def _check_some(cands: frozenset[str], op: str, hint: str) -> frozenset[str]:
    if not cands:
        raise _Broken(f"{op}:no_result", hint)
    return cands


def _anagram(n: CallNode, v: tuple[Val, ...]) -> frozenset[str]:
    c = _claim(str(n.args[-1]))
    if not any(sorted(f) == sorted(c) for f in v[1].cands):
        raise _Broken("anagram:letters",
                      f"no fodder {sorted(v[1].cands)} has the letters of {c}")
    return frozenset({c})


def _insert(n: CallNode, v: tuple[Val, ...]) -> frozenset[str]:
    c = _claim(str(n.args[-1]))
    _ind, inner, outer, _res = v
    if not any(c in _insertions(i, o) for i in inner.cands for o in outer.cands):
        raise _Broken("insert:no_position", f"{c} is not {sorted(inner.cands)} placed "
                      f"strictly inside {sorted(outer.cands)}")
    return frozenset({c})


def _hidden(n: CallNode, v: tuple[Val, ...]) -> frozenset[str]:
    c = _claim(str(n.args[-1]))
    span = v[1].tok
    assert span is not None
    if c not in span.letters or c == span.letters:
        raise _Broken("hidden:not_found", f"{c} is not a proper substring of {span.letters}")
    return frozenset({c})


def _abbr(n: CallNode, v: tuple[Val, ...]) -> frozenset[str]:
    t = v[0].tok
    assert t is not None
    c = _claim(str(n.args[1]))
    if not _abbr_ok(t, c):
        raise _Broken("abbr:not_in_table",
                      f"{t.phrase!r} -> {c} is not in the abbreviation table; "
                      "for a looser equivalence write syn(...)")
    return frozenset({c})


def _claimed(n: CallNode, v: tuple[Val, ...]) -> frozenset[str]:
    return frozenset({_claim(str(n.args[-1]))})


def _span_letters(v: tuple[Val, ...], i: int) -> Tok:
    t = v[i].tok
    assert t is not None
    return t


def _concat(n: CallNode, v: tuple[Val, ...]) -> frozenset[str]:
    out: frozenset[str] = frozenset({""})
    for x in v:
        out = frozenset(a + b for a in out for b in x.cands)
    return out


def _clue(n: CallNode, v: tuple[Val, ...]) -> frozenset[str]:
    return v[1].cands


_OPS = {
    "tok": lambda n, v: frozenset(),
    "link": lambda n, v: frozenset(),
    "double_duty": lambda n, v: frozenset(),
    "defn": lambda n, v: frozenset(),
    "lit": lambda n, v: frozenset({_span_letters(v, 0).letters}),
    "abbr": _abbr,
    "syn": lambda n, v: frozenset({_claim(str(n.args[1]))}),
    "anagram": _anagram,
    "reverse": lambda n, v: frozenset(f[::-1] for f in _one(v, 1)),
    "insert": _insert,
    "hidden": _hidden,
    "delete_first": lambda n, v: _check_some(
        frozenset(f[1:] for f in _one(v, 1) if len(f) > 1), "delete_first", "fodder too short"),
    "delete_last": lambda n, v: _check_some(
        frozenset(f[:-1] for f in _one(v, 1) if len(f) > 1), "delete_last", "fodder too short"),
    "delete_middle": lambda n, v: _check_some(
        frozenset(_middle_removed(f) for f in _one(v, 1) if len(f) > 1 + 1),
        "delete_middle", "fodder too short"),
    "initials": lambda n, v: frozenset(
        {"".join(normalise(w)[:1] for w in _span_letters(v, 1).words)}),
    "alternate": lambda n, v: _check_some(
        _alternates(_span_letters(v, 1).letters), "alternate", "fodder too short"),
    "concat": _concat,
    "homophone": _claimed,
    "double_def": _claimed,
    "cryptic_def": _claimed,
    "clue": _clue,
    "andlit": lambda n, v: v[0].cands,
}


def _coverage(clue: Clue, top: Val) -> None:
    counts = Counter(top.uses)
    for t in clue.tokens:
        allowed = 1 + (t.id in top.double)
        m = counts[t.id]
        if m == 0:
            raise _Broken(f"coverage:unused:{t.id}:{t.text}",
                          f"token {t.text!r} is not consumed; use it or declare link(tok(...))")
        if m > allowed:
            raise _Broken(f"coverage:reused:{t.id}:{t.text}",
                          f"token {t.text!r} is consumed {m} times; declare double_duty "
                          "only if the setter intends it")


def verify(clue: Clue, answer: str, src: str) -> Verdict:
    """Full pipeline: Ok | Quarantine(reasons) | Reject(first broken rule, hint)."""
    tree = surface(src)
    if isinstance(tree, Reject):
        return tree
    try:
        _typecheck(tree)
        resolved, _ = _resolve(tree, clue, {})
        top = _eval(resolved)
        _coverage(clue, top)
        a = normalise(answer)
        if not clue.enumeration.matches(answer):
            raise _Broken("answer:enumeration", f"{a} does not fit the enumeration")
        if a not in top.cands:
            raise _Broken("answer:mismatch",
                          f"wordplay gives {sorted(top.cands)}, expected {a}")
    except _Broken as e:
        return Reject(e.rule, e.hint)
    prov = Provenance(
        consumed=tuple(sorted(Counter(top.uses).items())),
        links=top.links,
        definition=top.definition,
    )
    reasons = tuple(r for r in Reason if r in top.reasons)
    return Quarantine(a, prov, reasons) if reasons else Ok(a, prov)
