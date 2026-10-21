"""Mutation suite (brief 001): small edits to an accepted parse. Mechanical
mutants must make the verifier Reject; an oracle-claim mutant must not come
back Ok (see `false_accept`).

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


def _replace_first_claim(node: CallNode, oracle: bool) -> tuple[CallNode, bool]:
    """Shift a letter in the first stated string (preorder, outside tok())
    whose operator is oracle-backed (`oracle`) or mechanical (not `oracle`)."""
    if node.op.name == "tok":
        return node, False
    args = list(node.args)
    for i, a in enumerate(args):
        if isinstance(a, str) and (node.op.oracle is not None) == oracle:
            args[i] = _shift(a)
            return CallNode(node.op, tuple(args)), True
        if isinstance(a, CallNode):
            new, done = _replace_first_claim(a, oracle)
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
    """A stated string of a mechanical operator (anagram/insert/hidden result,
    abbreviation value): the mutant must be Rejected."""
    new, done = _replace_first_claim(tree, oracle=False)
    return ("claim", answer, render(new)) if done else None


def _oracle_claim(answer: str, tree: CallNode) -> Mutant | None:
    """A stated string of an oracle operator (syn value, homophone/def result).
    The verifier cannot judge it (DESIGN D4): the mutant must not be Ok, and
    Quarantine naming the oracle is the correct verdict."""
    new, done = _replace_first_claim(tree, oracle=True)
    return ("oracle_claim", answer, render(new)) if done else None


def false_accept(kind: str, verdict: object) -> bool:
    """Whether the verdict on a mutant of this kind is a false accept."""
    from .verdict import Ok, Reject

    if kind == "oracle_claim":
        return isinstance(verdict, Ok)
    return not isinstance(verdict, Reject)


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
        lambda: _oracle_claim(answer, tree),
        lambda: _shrink_defn(answer, tree),
    )
    return tuple(m for m in (f() for f in makers) if m is not None)
