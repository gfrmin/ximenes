"""Prompt texts for instruments. Plain strings; examples use original clues
written for this repo (no dataset text)."""

from __future__ import annotations

ANSWER_ONLY_V1 = (
    "Solve this cryptic crossword clue. The numbers in brackets give the "
    "answer's word lengths. Reply with the answer only, in capital letters, "
    "and nothing else.\n\n{clue_text} ({enumeration})"
)

ANSWER_PATTERN_V1 = (
    "Solve this cryptic crossword clue. The numbers in brackets give the "
    "answer's word lengths. Some letters are known from crossing answers: "
    "{pattern} (? = unknown). Reply with the answer only, in capital letters, "
    "and nothing else.\n\n{clue_text} ({enumeration})"
)

# Brief 011: one call, a ranked list of candidates
LIST_V1 = (
    "Solve this cryptic crossword clue. The numbers in brackets give the "
    "answer's word lengths. Give up to {n} candidate answers that fit, best "
    "first, one per line, in capital letters, and nothing else.\n\n"
    "{clue_text} ({enumeration})"
)

LIST_PATTERN_V1 = (
    "Solve this cryptic crossword clue. The numbers in brackets give the "
    "answer's word lengths. Some letters are known from crossing answers: "
    "{pattern} (? = unknown). Give up to {n} candidate answers that fit, best "
    "first, one per line, in capital letters, and nothing else.\n\n"
    "{clue_text} ({enumeration})"
)

# Examples here are also checked by tests/test_001_*.py: each must verify.
FORMALISE_EXAMPLES: tuple[tuple[str, str, str], ...] = (
    (
        "{Listen} to broken tinsel (6)",
        "LISTEN",
        'clue(defn(tok("Listen")), anagram(tok("broken"), lit(tok("tinsel")), "LISTEN"), '
        'link(tok("to")))',
    ),
    (
        "Vehicle beside animal makes {rug} (6)",
        "CARPET",
        'clue(defn(tok("rug")), concat(syn(tok("Vehicle"), "CAR"), syn(tok("animal"), "PET")), '
        'link(tok("beside")), link(tok("makes")))',
    ),
    (
        "Queen in prohibition gives {husk} (4)",
        "BRAN",
        'clue(defn(tok("husk")), insert(tok("in"), abbr(tok("Queen"), "R"), '
        'syn(tok("prohibition"), "BAN"), "BRAN"), link(tok("gives")))',
    ),
    (
        "{Fruit} some deli meshes (4)",
        "LIME",
        'clue(defn(tok("Fruit")), hidden(tok("some"), tok("deli", "meshes"), "LIME"))',
    ),
    (
        "{Celebrity} rats returned (4)",
        "STAR",
        'clue(defn(tok("Celebrity")), reverse(tok("returned"), lit(tok("rats"))))',
    ),
    (
        "{Fine} {penalty} (4)",
        "FINE",
        'double_def(tok("Fine"), tok("penalty"), "FINE")',
    ),
)

FORMALISE_SPEC = """You translate a cryptic crossword clue's informal wordplay \
explanation into a small formal language (a DSL), so a strict checker can verify it.

The DSL is Python call syntax only: one expression, nested calls, string \
literals. No variables, keywords, comments, numbers, operators or anything else.

Tokens. The clue's words are given as a numbered token list. tok("w1", "w2") \
names a run of adjacent tokens by their exact text (case-insensitive; a \
hyphenated word is two tokens). Every token must be used exactly once in the \
whole parse: by the definition, by an operator (as fodder or as its indicator), \
or declared as a link word with link(tok(...)). If a word is repeated in the \
clue, the first tok() naming it takes its first occurrence, the next takes the \
next.

Top level, exactly one of:
  clue(defn(tok(...definition words...)), WORDPLAY, link(tok(...)), ...)
  double_def(tok(...first definition...), tok(...second...), "ANSWER", link(...), ...)
  cryptic_def(tok(...all the clue's words...), "ANSWER")
  andlit(WORDPLAY, link(...), ...)   # the whole clue is also the definition
Trailing link(tok(...)) arguments declare link words (e.g. "for", "with", \
"makes", "is", "in" when it only joins). double_duty(tok(...)) declares a token \
that is deliberately used twice.

WORDPLAY operators (each returns a string of capital letters):
  lit(tok(...))                         the tokens' own letters
  abbr(tok(...), "X")                   standard crossword abbreviation, \
checked against a table (queen -> R, doctor -> DR, five -> V)
  syn(tok(...), "WORD")                 synonym or looser equivalence (a \
judgement; use it when abbr does not apply)
  concat(A, B, ...)                     charade: A then B ...
  anagram(tok(indicator), FODDER, "RESULT")    RESULT is FODDER's letters rearranged
  reverse(tok(indicator), A)            A backwards
  insert(tok(indicator), INNER, OUTER, "RESULT")   INNER placed strictly \
inside OUTER gives RESULT (for "A around B" the inner is B)
  hidden(tok(indicator), tok(...fodder words...), "RESULT")  RESULT hidden \
in the fodder words' letters
  delete_first(tok(indicator), A)       A without its first letter
  delete_last(tok(indicator), A)        A without its last letter
  delete_middle(tok(indicator), A)      A without its middle letter(s)
  initials(tok(indicator), tok(...words...))   first letters of those words
  alternate(tok(indicator), tok(...words...))  odd or even letters of those words
  homophone(tok(indicator), A, "RESULT")       RESULT sounds like A
FODDER, A, INNER, OUTER are themselves WORDPLAY expressions; never a bare \
string. A bare string appears only as a stated result or value: the last \
argument of anagram/insert/hidden/homophone/double_def/cryptic_def, and the \
second argument of abbr/syn. The top-level wordplay must produce the answer \
(spaces and punctuation ignored).

If the explanation needs an operation this DSL does not have (for example \
taking last letters, or removing a particular letter), still write the \
parse, using a short descriptive new operator name in the same style, e.g. \
last_letters(tok("ends"), lit(tok("word"))). It will be rejected, and that \
tells us which operator to add.

Reply with the expression only: no prose, no code fences.

Examples (definition shown in braces):
"""


def formalise_system() -> str:
    """The system prompt: spec plus worked examples. Stable text, so it caches."""
    shots = "\n".join(
        f"Clue: {clue}\nAnswer: {answer}\nParse: {src}\n"
        for clue, answer, src in FORMALISE_EXAMPLES
    )
    return FORMALISE_SPEC + "\n" + shots


FORMALISE_USER = """Clue: {clue}
Tokens: {tokens}
Answer: {answer}
Definition: {definition}
Wordplay explanation: {wordplay}
{previous}Parse:"""


# --- brief 002 --------------------------------------------------------------
# formalise-v1 above stays frozen (brief 001's logs were made with it).

_NEW_OPERATORS = """  first_letters(tok(indicator), tok(...words...))  first letter of each word
  last_letters(tok(indicator), tok(...words...))   last letter of each word
  outer_letters(tok(indicator), A)      first and last letter of A
  middle_letters(tok(indicator), A, "RESULT")   A with equal numbers of \
letters stripped from both ends
  remove(tok(indicator), A, B, "RESULT")   A with one contiguous occurrence of B deleted
  strip_outer(tok(indicator), A)        A without its first and last letter
  half(tok(indicator), A, "first")      first or "second" half of A (A of even length)
"""

FORMALISE_SPEC_V2 = (
    FORMALISE_SPEC.replace(
        "  homophone(tok(indicator), A, \"RESULT\")       RESULT sounds like A\n",
        "  homophone(tok(indicator), A, \"RESULT\")       RESULT sounds like A\n" + _NEW_OPERATORS,
    ).replace(
        "the last argument of anagram/insert/hidden/homophone/double_def/cryptic_def",
        "the last argument of anagram/insert/hidden/homophone/middle_letters/remove/"
        "double_def/cryptic_def",
    ).replace(
        "(for example taking last letters, or removing a particular letter)",
        "(for example a spoonerism)",
    ).replace(
        "last_letters(tok(\"ends\"), lit(tok(\"word\")))",
        "spoonerism(tok(\"Spooner\"), lit(tok(\"word\")))",
    )
)


def formalise_clue_system() -> str:
    """Brief 002: parse a clue for a *candidate* answer, with no explanation given."""
    shots = "\n".join(
        f"Clue: {clue}\nAnswer: {answer}\nParse: {src}\n"
        for clue, answer, src in FORMALISE_EXAMPLES
    )
    return (FORMALISE_SPEC_V2
            .replace("You translate a cryptic crossword clue's informal wordplay "
                     "explanation into a small formal language (a DSL)",
                     "You explain how a cryptic crossword clue produces a given answer, "
                     "writing the explanation in a small formal language (a DSL)")
            + "\nFind the definition (at the start or end of the clue) and the wordplay "
            "yourself. If you cannot make the answer work, reply NONE.\n\n" + shots)


FORMALISE_CLUE_USER = """Clue: {clue}
Tokens: {tokens}
Answer: {answer}
{previous}Parse:"""

_JUDGE_TAIL = (
    '\nReply with JSON only: {"score": <number from 0 to 1>, "reason": "<one short line>"}. '
    "The score is your probability that the judgement holds, as a careful crossword "
    "editor would rule."
)

JUDGES = {
    "judge-synonym-v1": (
        "In cryptic crosswords, a word or phrase in the clue may stand for another word "
        "(a synonym, a looser equivalent, or a conventional crossword substitution). "
        "Judge whether the clue phrase can fairly stand for the value, in the context of "
        "the clue." + _JUDGE_TAIL,
        "Clue: {context}\nClue phrase: {phrase}\nValue: {value}",
    ),
    "judge-definition-v1": (
        "In cryptic crosswords, part of the clue is a definition of the answer. Judge "
        "whether the given span is a fair definition of the answer (allowing the usual "
        "crossword latitude: a part of speech must match, an example may define a class "
        "if signalled)." + _JUDGE_TAIL,
        "Clue: {context}\nDefinition span: {phrase}\nAnswer: {value}",
    ),
    "judge-indicator-v1": (
        "In cryptic crosswords, an indicator word or phrase tells the solver which "
        "operation to apply to nearby letters (anagram, reversal, insertion, hidden word, "
        "deletion, first/last letters, and so on). Judge whether the phrase can fairly "
        "indicate the named operation in this clue." + _JUDGE_TAIL,
        "Clue: {context}\nPhrase: {phrase}\nOperation: {value}",
    ),
    "judge-homophone-v1": (
        "In cryptic crosswords, a homophone indicator says one word sounds like another. "
        "Judge whether the two sound alike in standard British pronunciation (near-"
        "homophones that setters commonly use count, with a lower score)." + _JUDGE_TAIL,
        "Spoken: {phrase}\nHeard: {value}",
    ),
}
