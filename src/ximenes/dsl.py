"""The operator table. This is the whole language.

Each operator has fixed arity, argument sorts, a result sort, and a flag for
whether it is mechanical (-> Ok) or oracle-backed (-> Quarantine). Adding an
operator is a design change: it must come with a test.

Sorts
  TOK   a reference to clue token(s)        tok("word")
  STR   a concrete string
  SEM   a token whose value is a meaning     (resolved by syn/defn)
  PHON  a sound                               (resolved by homophone)
  NULL  declared non-contributing material   link(...)
  CLAIM a string literal the parse states and the operator checks
        (a result, or a synonym/abbreviation value); never fodder
  MODE  a declared mode                       double_duty(...)

Top-level forms (`clue`, `double_def`, `cryptic_def`, `andlit`) take their
fixed arguments, then any number of trailing `link(...)` / `double_duty(...)`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .verdict import Reason


class Sort(Enum):
    TOK = "Tok"
    STR = "Str"
    SEM = "Sem"
    PHON = "Phon"
    NULL = "Null"
    MODE = "Mode"
    CLAIM = "Claim"


@dataclass(frozen=True)
class Op:
    name: str
    args: tuple[Sort, ...]  # fixed arity; use VARARGS sentinel for n-ary
    result: Sort
    oracle: Reason | None = None  # None => mechanical
    variadic: bool = False
    extras: frozenset[Sort] = frozenset()  # sorts allowed after the fixed args
    indicated: bool = False  # first arg is an indicator, checked against the table


_DECL = frozenset({Sort.NULL, Sort.MODE})


# n-ary operators take >= 2 args of the single listed sort
OPERATORS: dict[str, Op] = {
    # --- references and declarations ---
    "tok": Op("tok", (Sort.CLAIM,), Sort.TOK, variadic=True),  # tok("a","b") = span
    "link": Op("link", (Sort.TOK,), Sort.NULL),
    "defn": Op("defn", (Sort.TOK,), Sort.STR, oracle=Reason.DEFINITION),
    # --- leaves ---
    "lit": Op("lit", (Sort.TOK,), Sort.STR),  # the token's own letters
    "abbr": Op("abbr", (Sort.TOK, Sort.CLAIM), Sort.STR),  # table lookup
    "syn": Op("syn", (Sort.TOK, Sort.CLAIM), Sort.STR, oracle=Reason.SYNONYM),
    # --- mechanical transforms (indicator token, then fodder) ---
    "anagram": Op("anagram", (Sort.TOK, Sort.STR, Sort.CLAIM), Sort.STR, indicated=True),
    "reverse": Op("reverse", (Sort.TOK, Sort.STR), Sort.STR, indicated=True),
    # ind, inner, outer, result
    "insert": Op("insert", (Sort.TOK, Sort.STR, Sort.STR, Sort.CLAIM), Sort.STR, indicated=True),
    # ind, fodder span, result
    "hidden": Op("hidden", (Sort.TOK, Sort.TOK, Sort.CLAIM), Sort.STR, indicated=True),
    "delete_first": Op("delete_first", (Sort.TOK, Sort.STR), Sort.STR, indicated=True),
    "delete_last": Op("delete_last", (Sort.TOK, Sort.STR), Sort.STR, indicated=True),
    "delete_middle": Op("delete_middle", (Sort.TOK, Sort.STR), Sort.STR, indicated=True),
    "initials": Op("initials", (Sort.TOK, Sort.TOK), Sort.STR, indicated=True),
    "alternate": Op("alternate", (Sort.TOK, Sort.TOK), Sort.STR, indicated=True),
    "concat": Op("concat", (Sort.STR,), Sort.STR, variadic=True),
    # --- oracle transforms ---
    "homophone": Op("homophone", (Sort.TOK, Sort.STR, Sort.CLAIM), Sort.STR,
                    oracle=Reason.HOMOPHONE, indicated=True),
    "double_def": Op("double_def", (Sort.TOK, Sort.TOK, Sort.CLAIM), Sort.STR,
                     oracle=Reason.DOUBLE_DEF, extras=_DECL),
    "cryptic_def": Op("cryptic_def", (Sort.TOK, Sort.CLAIM), Sort.STR,
                      oracle=Reason.CRYPTIC_DEF, extras=_DECL),
    # --- clue-level forms and modes (explicit, never inferred) ---
    # clue(defn(...), wordplay, *declarations) -> answer
    "clue": Op("clue", (Sort.STR, Sort.STR), Sort.STR, extras=_DECL),
    # whole clue is both definition and wordplay
    "andlit": Op("andlit", (Sort.STR,), Sort.STR, oracle=Reason.DEFINITION, extras=_DECL),
    "double_duty": Op("double_duty", (Sort.TOK,), Sort.MODE),
}

TOP_LEVEL = frozenset({"clue", "double_def", "cryptic_def", "andlit"})


def is_oracle(name: str) -> bool:
    return OPERATORS[name].oracle is not None
