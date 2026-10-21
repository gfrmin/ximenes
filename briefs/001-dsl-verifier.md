# Brief 001 — Typed DSL and non-executing verifier

Headline number: **gold-parse coverage** — the share of
`data/wordplay/sample_teacow_val.jsonl` explanations (300 FT clues,
Cryptonite-val answers) that can be written in the DSL and accepted as `Ok`
or `Quarantine` by the verifier; report the 5,412-line train sample as a
secondary number. This is the honest ceiling of a sound-by-grammar approach.
Also report the **false-accept rate** on the mutation suite (must be 0).

## What is already there (from brief 000)
`ximenes.data` loads both datasets; `ximenes.instruments` is the only door
to LLMs (anthropic / stub backends, JSONL logs, exact replay, resume);
`ximenes.eval` has the vote baseline. `ximenes.verify.surface` (stage 1) and
`ximenes.dsl.OPERATORS` exist and are tested. Build on these; don't
restructure them.

## How gold explanations become DSL (the one new LLM use in this brief)
The wordplay strings are informal (`PROP (support) + (ALSO)* (*broadcast)`),
so a **formaliser** instrument, `formalise_gold(clue, answer, definition,
wordplay, model) -> dsl_source`, rewrites each one in the DSL, with the DSL
spec and six hand-written examples in the prompt. Up to two retries, each
fed the verifier's hinted error. Model: `claude-sonnet-5-5` (strong enough
that a Reject is more likely the DSL's limit than the formaliser's); ~900
calls, a few dollars. Logged and replayable like every instrument. Add a
`max_usd` per run to `data/eval.json`; a run stops when its logged cost
passes it.

Coverage therefore conflates "the DSL can express it" with "the formaliser
managed to". To separate them: hand-audit 30 Rejects (seeded sample) and
report how many are DSL limits vs formaliser misses. The 30 hand-written
gold parses used for that audit and the prompt examples live in
`tests/fixtures/gold-dsl.jsonl` (original wording only: the clue and
wordplay text are from the dataset and stay out of the repo; store the
split, index and DSL source).

Oracle leaves (`syn`, `defn`, `homophone`, `double_def`, `cryptic_def`) are
**not** called in this brief: the verifier returns `Quarantine` with the
typed reason and moves on. Calling oracles is brief 002.

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
   coverage law (DESIGN D3). Report residual and reused tokens.
5. Check final string == answer (normalised) and matches enumeration.
6. Return `Ok | Quarantine(reasons) | Reject(first_broken_rule)` plus a
   hinted error string in the Andrews & Witteveen style for the proposer.

## Tests (tests/test_001_*.py)
- The four A&W exploits are `Reject`ed at the surface step (see
  `tests/test_exploits.py`, already present; extend it, never prune it).
- A token used twice, or left over, cannot be `Ok`.
- Every operator has a property test with random fodder.
- Coverage number computed only on val; test untouched.
- Replaying the formaliser log reproduces the coverage number exactly.
- The 30 hand-written gold parses in `tests/fixtures/gold-dsl.jsonl` all
  verify (as `Ok` or `Quarantine`, each with the expected status).

## Not in scope
Grid, probabilities, metacomputation, fine-tuning. Do not try to raise
coverage by adding operators beyond the list without a note in the report.

## Report
Coverage on val (overall, quick, hard) and on train; the breakdown of
`Reject` reasons for the uncovered gold parses (this tells the author what
the next operator should be); the 30-Reject audit split (DSL limit vs
formaliser miss); false-accept rate on mutants; formaliser cost; kit output;
probability complete.

Stop rule (`briefs/ROADMAP.md`): if coverage on val is far below ~30%, say
so plainly; the author decides whether the strict verifier continues.
