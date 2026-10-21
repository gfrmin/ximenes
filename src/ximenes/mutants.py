"""Mutation suite (brief 001): small edits to an accepted parse that must make
the verifier Reject. A mutant the verifier still accepts is a false accept.

Mutants are built on the surface tree and rendered back to source, so they go
through the whole pipeline like any proposer output.
"""

from __future__ import annotations

from collections.abc import Callable

from .clue import normalise
from .dsl import OPERATORS
from .verify import CallNode, surface

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
Mutant = tuple[str, str, str]  # (kind, answer, src)


def render(node: CallNode | str) -> str:
    if isinstance(node, str):
        return repr(node)
    return f"{node.op.name}({', '.join(map(render, node.args))})"


def _shift(s: str) -> str:
    """Change the first letter to the next one in the alphabet."""
    i = next((k for k, c in enumerate(s) if c.upper() in ALPHABET), None)
    if i is None:
        return s
    c = s[i].upper()
    return s[:i] + ALPHABET[(ALPHABET.index(c) + 1) % len(ALPHABET)] + s[i + 1:]


def _replace_first_claim(node: CallNode) -> tuple[CallNode, bool]:
    """Shift a letter in the first stated string (preorder), outside tok()."""
    if node.op.name == "tok":
        return node, False
    args = list(node.args)
    for i, a in enumerate(args):
        if isinstance(a, str):
            args[i] = _shift(a)
            return CallNode(node.op, tuple(args)), True
        new, done = _replace_first_claim(a)
        if done:
            args[i] = new
            return CallNode(node.op, tuple(args)), True
    return node, False


def _wrong_answer(answer: str, tree: CallNode) -> Mutant | None:
    a = normalise(answer)
    rotated = a[1:] + a[:1]
    return ("answer", rotated, render(tree)) if rotated != a else None


def _drop_decl(answer: str, tree: CallNode) -> Mutant | None:
    if len(tree.args) <= len(tree.op.args):
        return None
    return ("drop_decl", answer, render(CallNode(tree.op, tree.args[:-1])))


def _extra_link(answer: str, tree: CallNode, first_word: str) -> Mutant:
    link = CallNode(OPERATORS["link"], (CallNode(OPERATORS["tok"], (first_word,)),))
    return ("extra_link", answer, render(CallNode(tree.op, (*tree.args, link))))


def _claim(answer: str, tree: CallNode) -> Mutant | None:
    new, done = _replace_first_claim(tree)
    return ("claim", answer, render(new)) if done else None


def _shrink_defn(answer: str, tree: CallNode) -> Mutant | None:
    if tree.op.name != "clue":
        return None
    defn = tree.args[0]
    assert isinstance(defn, CallNode)
    span = defn.args[0]
    if not isinstance(span, CallNode) or len(span.args) <= 1:
        return None
    shorter = CallNode(defn.op, (CallNode(span.op, span.args[:-1]),))
    return ("shrink_defn", answer, render(CallNode(tree.op, (shorter, *tree.args[1:]))))


def mutants(first_word: str, answer: str, src: str) -> tuple[Mutant, ...]:
    """Every applicable mutant of an accepted parse. `first_word` is the clue's
    first token (used for the extra-link mutant)."""
    tree = surface(src)
    if not isinstance(tree, CallNode):
        return ()
    makers: tuple[Callable[[], Mutant | None], ...] = (
        lambda: _wrong_answer(answer, tree),
        lambda: _drop_decl(answer, tree),
        lambda: _extra_link(answer, tree, first_word),
        lambda: _claim(answer, tree),
        lambda: _shrink_defn(answer, tree),
    )
    return tuple(m for m in (f() for f in makers) if m is not None)
