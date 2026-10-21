"""The operator table. This is the whole language.

Each operator has fixed arity, argument sorts, a result sort, and a flag for
whether it is mechanical (-> Ok) or oracle-backed (-> Quarantine). Adding an
operator is a charter-visible change: it must come with a law.

Sorts
  TOK   a reference to clue token(s)        tok("word")
  STR   a concrete string
  SEM   a token whose value is a meaning     (resolved by syn/defn)
  PHON  a sound                               (resolved by homophone)
  NULL  declared non-contributing material   link(...)
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


@dataclass(frozen=True)
class Op:
    name: str
    args: tuple[Sort, ...]  # fixed arity; use VARARGS sentinel for n-ary
    result: Sort
    oracle: Reason | None = None  # None => mechanical
    variadic: bool = False


# n-ary operators take >= 2 args of the single listed sort
OPERATORS: dict[str, Op] = {
    # --- references and declarations ---
    "tok": Op("tok", (Sort.STR,), Sort.TOK, variadic=True),  # tok("a","b") = span
    "link": Op("link", (Sort.TOK,), Sort.NULL),
    "defn": Op("defn", (Sort.TOK,), Sort.STR, oracle=Reason.DEFINITION),
    # --- leaves ---
    "lit": Op("lit", (Sort.TOK,), Sort.STR),  # the token's own letters
    "abbr": Op("abbr", (Sort.TOK, Sort.STR), Sort.STR),  # table lookup
    "syn": Op("syn", (Sort.TOK, Sort.STR), Sort.STR, oracle=Reason.SYNONYM),
    # --- mechanical transforms (indicator token, then fodder) ---
    "anagram": Op("anagram", (Sort.TOK, Sort.STR, Sort.STR), Sort.STR),  # ind, fodder, result
    "reverse": Op("reverse", (Sort.TOK, Sort.STR), Sort.STR),
    # ind, inner, outer, result
    "insert": Op("insert", (Sort.TOK, Sort.STR, Sort.STR, Sort.STR), Sort.STR),
    "hidden": Op("hidden", (Sort.TOK, Sort.TOK, Sort.STR), Sort.STR),  # ind, fodder span, result
    "delete_first": Op("delete_first", (Sort.TOK, Sort.STR), Sort.STR),
    "delete_last": Op("delete_last", (Sort.TOK, Sort.STR), Sort.STR),
    "delete_middle": Op("delete_middle", (Sort.TOK, Sort.STR), Sort.STR),
    "initials": Op("initials", (Sort.TOK, Sort.TOK), Sort.STR),
    "alternate": Op("alternate", (Sort.TOK, Sort.TOK), Sort.STR),
    "concat": Op("concat", (Sort.STR,), Sort.STR, variadic=True),
    # --- oracle transforms ---
    "homophone": Op("homophone", (Sort.TOK, Sort.STR, Sort.STR), Sort.STR, oracle=Reason.HOMOPHONE),
    "double_def": Op(
        "double_def", (Sort.TOK, Sort.TOK, Sort.STR), Sort.STR, oracle=Reason.DOUBLE_DEF
    ),
    "cryptic_def": Op("cryptic_def", (Sort.TOK, Sort.STR), Sort.STR, oracle=Reason.CRYPTIC_DEF),
    # --- clue-level modes (explicit, never inferred) ---
    "clue": Op("clue", (Sort.STR, Sort.STR), Sort.STR),  # clue(defn(...), wordplay) -> answer
    "andlit": Op("andlit", (Sort.STR,), Sort.STR),  # whole clue is both; relaxes coverage
    "double_duty": Op("double_duty", (Sort.TOK,), Sort.MODE),
}


def is_oracle(name: str) -> bool:
    return OPERATORS[name].oracle is not None
