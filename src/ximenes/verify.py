"""Non-executing verifier (DESIGN D2–C4).

Stage 1 (`surface`) is complete and law-tested: parse with `ast`, accept only
the allowlisted node types, and resolve every call to the operator table.
Stages 2–5 are brief 001's job; their signatures are fixed here so the laws
can be written against them.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from .clue import Clue
from .dsl import OPERATORS, Op
from .verdict import Reject, Verdict

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
    elif len(args) != len(op.args):
        return Reject(f"arity:{name}:expected_{len(op.args)}_got_{len(args)}")
    return CallNode(op, tuple(args))


# --- Stages 2–5: brief 001 --------------------------------------------------


def verify(clue: Clue, answer: str, src: str) -> Verdict:
    """Full pipeline. Brief 001 implements typing, evaluation, provenance,
    coverage and the answer/enumeration check. Until then every surface-valid
    parse is rejected with a named rule so nothing is silently accepted."""
    tree = surface(src)
    if isinstance(tree, Reject):
        return tree
    return Reject("unimplemented:brief-001", hint="verifier stages 2-5 not built")
