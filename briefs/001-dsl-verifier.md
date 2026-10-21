# Brief 001 — Typed DSL and non-executing verifier

Branch: `b/001-dsl-verifier`. Headline number: **gold-parse coverage** —
the share of Wordplay-dataset explanations (val split) that can be written in
the DSL and accepted as `Ok` or `Quarantine` by the verifier. This is the
honest ceiling of a sound-by-grammar approach. Also report the
**false-accept rate** on the mutation suite (must be 0).

## The DSL (surface = Python syntax, parsed never executed)
A parse is a single Python expression tree built only from names in
`src/ximenes/dsl.py:OPERATORS`. Sorts: `Str`, `Phon`, `Sem`, `Tok`, `Null`.

```python
# Clue: "Support broadcast for propaganda? (8)"  →  PROPOSAL
charade(
  syn(tok("Support"), "PROP"),            # Sem -> Str (oracle leaf)
  anagram(tok("broadcast"), tok("also"))  # NB: example only; see dataset
)
```
Every leaf names the clue token(s) it consumes via `tok(...)`; `link(...)`
declares link words; `defn(tok(...))` declares the definition span; `mode`
flags (`andlit`, `double_duty`) are explicit wrapper calls.

Operators (minimum set; each has fixed arity and sorts):
`tok, link, defn, lit, abbr, syn, anagram, reverse, insert, concat, hidden,
delete_first, delete_last, delete_middle, initials, alternate, homophone,
double_def, cryptic_def, andlit`.
Each oracle-backed operator (`syn, defn, homophone, double_def, cryptic_def`)
produces `Quarantine` not `Ok`.

## The verifier (`src/ximenes/verify.py`)
1. `ast.parse(src, mode="eval")`; walk; any node type outside the allowlist
   → `Reject("surface:<nodetype>")`. Allowlist: `Expression, Call, Name,
   Constant(str)`. Nothing else. No keywords, no starargs.
2. Type-check sorts and arities against the operator table.
3. Evaluate mechanical operators over strings; call indicator/abbreviation
   tables; call oracle instruments (logged) for oracle leaves.
4. Build provenance: a multiset (N[X]) of consumed token ids. Apply the
   coverage law (CHARTER C3). Report residual and reused tokens.
5. Check final string == answer (normalised) and matches enumeration.
6. Return `Ok | Quarantine(reasons) | Reject(first_broken_rule)` plus a
   hinted error string in the Andrews & Witteveen style for the proposer.

## Laws (tests/laws/001/)
- The four A&W exploits are `Reject`ed at the surface step (see
  `tests/test_exploits.py`, already present; extend it).
- A token used twice, or left over, cannot be `Ok`.
- Every operator has a property test with random fodder.
- Coverage number computed only on val; test untouched.

## Not in scope
Grid, probabilities, metacomputation, fine-tuning. Do not try to raise
coverage by adding operators beyond the list without an author note.

## Report
Coverage on val (overall, quick, hard), the breakdown of `Reject` reasons for
the uncovered gold parses (this tells the author what the next operator
should be), false-accept rate on mutants, kit output, probability complete.
