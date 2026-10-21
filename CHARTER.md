# ximenes — Charter v0 (draft, unsigned)

One page. Changes only by a sitting with a dated amendment. The author is the
sole signing authority. The builder may propose; it may not rule.

## C1. Separation of powers
A clue solve has exactly three parties. **Proposers** (LLMs, lexicon lookups)
emit *observations*. The **kernel** holds the parse forest and issues
*verdicts*. The **decider** holds beliefs and chooses *acts*. No party writes
to another's state. An LLM output is never a belief.

## C2. Nothing is executed
A parse is Python *syntax* parsed to an AST and walked by the kernel. No
`exec`, `eval`, `import`, conditionals, loops, comprehensions, lambdas,
attribute access, or calls to anything outside the operator table.
A parse that uses a construct outside the surface grammar is `Reject`ed
before any operator runs. (Prior art: Andrews & Witteveen 2025, whose
verifier was defeated by comment-only proofs, `if` routing,
`assert X == False`, and disconnected steps. Each is impossible here by grammar.)

## C3. The coverage law
A parse is `Ok` only if its provenance shows every non-link clue token
consumed **exactly once** (multiplicity 1 in the N[X] annotation). Link words
are declared, not inferred. `&lit` and double-duty are declared modes that
change the law explicitly; they are not inferred.

## C4. Three verdicts, honestly named
- `Ok`: every step is mechanical (string algebra, abbreviation table,
  indicator table) and coverage holds.
- `Quarantine(reasons)`: mechanics and coverage hold but at least one leaf
  rests on an oracle — `synonym`, `definition`, `homophone`, `cryptic_def`,
  `double_def` — or there is a declared residual. Reasons are typed.
- `Reject(first_broken_rule)`: name the first rule broken, nothing more.
The word "proof" is never used for a `Quarantine`.

## C5. Numbers live in tables
Probabilities, utilities, prices and lexicon weights live in data tables with
a declared source. No numeric literal in kernel code except 0 and 1.

## C6. Oracles are instruments
Synonym/definition/homophone judgements are `host` instruments: deterministic
given (input, model-id, seed), logged with inputs and outputs, replayable.
A solve must replay bit-for-bit from its log without network access.

## C7. Evaluation is pre-registered and contamination-aware
Cryptonite splits are used as published and their hashes frozen. A rolling
post-cutoff set exists, is dated, is never committed, and never appears in a
prompt, fine-tune, or lexicon. Every reported number names its set and date.

## C8. One brief, one number
Each brief has one headline number and one mechanical acceptance check in
`kit/check.sh`. Laws under `tests/laws/<brief>/` are frozen when the brief's
PR merges and are never edited, only superseded by a later brief.

## C9. It is a puzzle, not a question
The solution is unique and the wordplay proves it. Entering an answer is a
reversible hypothesis; **submit** is the only terminal act, and its payoff
is the scoring rule of the setting (all-correct, top-1, or elicited for
assisting a human), never a tuned parameter. Probabilities are beliefs about
oracle leaves, calibrated on validation data. A finished solve is either
*proven* (empty oracle provenance) or *quarantined* (names the judgements it
rests on). See `docs/GAME.md`.

## C10. Scope
In: single clues (with enumeration, orientation, optional crossers);
later grids. Out until a sitting says otherwise: clue *setting*, UI,
scraping beyond the eval harness, RL/distillation.

Signed: ____________________  tag: `charter-v0` (pending)
