# ximenes — design rules

These are the rules the code is built to. Change them when you learn
something; note what changed and why in the commit. The ones that are
mechanically checked say so.

## D1. Separation of powers
A clue solve has three parties. **Proposers** (LLMs, lexicon lookups) emit
*observations*. The **kernel** holds the hypothesis relation and issues
*verdicts*. The **search controller** holds beliefs and chooses *computations*.
No party writes to another's state. An LLM output is never a belief.

## D2. Nothing is executed  *(checked: `tests/test_exploits.py`, `kit/lint_forbidden.py`)*
A parse is Python *syntax* parsed to an AST and walked by the kernel. No
`exec`, `eval`, `import`, conditionals, loops, comprehensions, lambdas,
attribute access, or calls to anything outside the operator table. A parse
using a construct outside the surface grammar is `Reject`ed before any
operator runs. (Andrews & Witteveen 2025's verifier was defeated by
comment-only proofs, `if` routing, `assert X == False`, and disconnected
steps. Each is impossible here by grammar.)

## D3. The coverage law  *(checked from brief 001)*
A parse is `Ok` only if its provenance shows every non-link clue token
consumed **exactly once** (multiplicity 1 in the N[X] annotation). Link words
are declared, not inferred. `&lit` and double-duty are declared modes that
change the law explicitly.

## D4. Three verdicts, honestly named
- `Ok`: every step is mechanical (string algebra, abbreviation table,
  indicator table) and coverage holds.
- `Quarantine(reasons)`: mechanics and coverage hold but at least one leaf
  rests on an oracle — `synonym`, `definition`, `homophone`, `cryptic_def`,
  `double_def` — or there is a declared residual. Reasons are typed.
- `Reject(first_broken_rule)`: name the first rule broken, nothing more.
The word "proof" is never used for a `Quarantine`.

## D5. Numbers live in tables  *(checked: `kit/lint_numbers.py`)*
Probabilities, prices and lexicon weights live in `data/` tables with a
`source` field. No numeric literal in kernel code except 0 and 1.

## D6. Oracles are instruments
Synonym/definition/homophone judgements are deterministic given
(input, model-id, seed), logged with inputs and outputs, replayable. A solve
must replay bit-for-bit from its log without network access.

## D7. Evaluation is contamination-aware  *(checked: `kit/check.sh`, split hashes from brief 000)*
Cryptonite splits are used as published and their hashes frozen. A rolling
post-cutoff set exists, is dated, is never committed, and never appears in a
prompt, fine-tune, or lexicon. Every reported number names its set and date.

## D8. One stage, one number
Each brief has one headline number and its acceptance tests. Tests from
earlier briefs are not edited, only superseded by a later brief that says so.
This is the only guard against quietly weakening the verifier to raise a
number; CI runs them on every push.

## D9. It is a puzzle, not a question
The solution is unique and the wordplay proves it. Entering an answer is a
reversible hypothesis; **submit** is the only terminal act, and its payoff
is the scoring rule of the setting, never a tuned parameter. Probabilities
are beliefs about oracle leaves, calibrated on validation data. A finished
solve is either *proven* (empty oracle provenance) or *quarantined* (names
the judgements it rests on). See `docs/GAME.md`.

## D10. Scope
In: single clues (with enumeration, orientation, optional crossers); later
grids. Out for now: clue *setting*, UI, scraping beyond the eval harness,
RL/distillation.
