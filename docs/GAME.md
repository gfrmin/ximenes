# The game

A cryptic crossword is a puzzle, not a question. That one word changes the
decision theory. This note replaces the earlier "selective answering with
`u_wrong`" framing.

## 1. Why there is no `u_wrong`

A puzzle has a unique intended solution and the wordplay is a *proof* of it.
Entering an answer in the grid is not a terminal act: it is a hypothesis you
can retract. The only terminal act is **submit**, and its payoff is fixed by
whoever is scoring:

| setting | terminal payoff |
|---|---|
| Times Championship | 1[all correct]; ties broken by time |
| Cryptonite single-clue benchmark | 1[top-1 correct] (wrong = blank = 0) |
| daily solve for yourself | 1[all correct], no time price |
| assisting a human mid-solve | the one case a cost of a wrong suggestion is real, and must be elicited |

So the utility is not a parameter to pre-register. What *is* uncertain is
epistemic: which hypotheses are consistent, and whether the parts of a
solution that rest on oracle judgements (synonyms, definitions, homophones)
are actually sound. Probabilities live there, in **beliefs about oracle
leaves**, not in utilities over outcomes.

The decision-theoretic content of the whole problem is then
**metacomputation**: which computation to run next, when to call an
expensive oracle, when to stop and submit. That is `wald`'s question,
exactly.

## 2. Sudoku, exactly and inexactly

Sudoku: candidates per cell, constraint propagation, branch on a hypothesis
when stuck, backtrack on contradiction. The solution is *proven* when every
step was a deduction; a guess shows up as a branch in the trace.

Cryptics are the same game with two things broken:

1. **The constraint checker is incomplete.** String algebra (anagram,
   reversal, insertion, deletion, hidden, abbreviations) is exact. Synonymy,
   definitions and homophones are judgements. So a hypothesis can pass every
   mechanical check and still be wrong (SCARF vs SNARF: same definition
   "wolf", same crossers, only the glyph-level wordplay separates them).
2. **The candidate generator is incomplete.** If the answer is never
   proposed, no search finds it. An empty domain is therefore not a
   contradiction; it is a cue to propose again with the crosser pattern and
   a stronger model.

Consequence: the search can terminate with a solution that is *proven* (every
leaf mechanical, every slot crossed) or one that is *quarantined* (rests on
named oracle calls). The trace says which. That distinction is the product.

## 3. State, moves, terminal

**State** (a database; see §5)
- `Token(clue, pos, text)`
- `Slot(id, enum, orientation, cells)`
- `Hyp(slot, answer, parse_src, status, prov)` with
  `status ∈ {Unverified, Reject, Quarantine(reasons), Ok}` and
  `prov` = tokens consumed (with multiplicity) + the set of oracle calls
  the parse depends on
- `Dom(cell, letter)` derived from `Hyp` by projection
- `Nogood(set of (slot, answer))` learned from conflicts

**Moves** are all computations. The environment never answers.

| move | effect | price |
|---|---|---|
| `propose(slot, k, tier, pattern)` | new `Hyp` rows, `Unverified` | tokens, seconds |
| `explain(h)` | parse source for `h` | tokens |
| `verify(h)` | `status`, `prov` | ~0, plus any oracle calls |
| `oracle(leaf)` | a logged judgement with a score | tokens |
| `propagate()` | arc consistency over crossers; prune unsupported `Hyp` rows | ~0 |
| `branch(h)` | assume `h`, propagate; on dead end, record a `Nogood` and undo | the computation spent on the branch |
| `submit()` | terminal | — |

"Wrong answer" costs nothing per se. A wrong *branch* costs the computation
spent under it. That cost is what the metareasoner prices, not a utility.

**Confidence to "bung it in".** Three independent confirmations exist for a
slot: wordplay proven (`Ok`), definition judged (oracle), crossers consistent
with verified neighbours. Any two suffice for a human; the kernel records
which two. In particular, `Ok` wordplay + verified crossers means the
definition oracle was never needed.

## 4. Metacomputation (the `wald` pack)

Value of a computation = expected improvement in the terminal payoff of the
best subsequent *stopping* decision, minus its price (Hay, Russell, Tolpin,
Shimony 2012). With payoff 1[all correct]:

- a computation on slot *s* is worth
  E[Δ P(all correct)] − λ·seconds − μ·tokens;
- P(all correct) = product over slots of P(slot correct), where a slot with
  `Ok` wordplay and verified crossers contributes ≈1 and a quarantined slot
  contributes the calibrated reliability of the oracle leaves it rests on.

Baselines to beat, in this order: smallest-domain-first (MRV, the sudoku
heuristic); Dr.Fill's confidence gap; Darmok's "attempt every clue before
entering any". A negative result against MRV is still a result.

Why this is a purer testbed than Wordle: Wordle's observations come from
the environment (coloured tiles); here every observation is produced by the
agent's own computations. All uncertainty is about the agent's own
inference, which is the thing the metacomputation amendment must model.

## 5. `tannen`: the state is a relation, the solve is a query

Each `Hyp` row carries an annotation from a commutative semiring. The same
propagation query, under different semirings, answers different questions:

| semiring | annotation | the query answers |
|---|---|---|
| Boolean | consistent? | is there a full assignment |
| N | count | how many consistent assignments (ideally 1) |
| Viterbi / probability | weight | best assignment; marginals (what BCS computes with BP) |
| N[X] over tokens | multiplicity | the coverage law: every non-link token exactly once |
| Why-provenance over oracle calls | which judgements | what the solution rests on; empty = proven |
| product (Z × Why, `tannen`'s default) | both | counting *and* audit, in one run |

This is Goodman's semiring parsing applied to the grid, with
Green–Karvounarakis–Tannen provenance as the audit channel. `propagate()` is a
semi-join of `Hyp` against the crosser domains; `branch(h)` is a filter;
`Nogood` is an anti-join. Ok/Quarantine is `tannen`'s existing outcome type:
Quarantine ⇔ non-empty oracle provenance.

## 6. `hkaddresses`: the flat version of the same game

| cryptic | address |
|---|---|
| clue string | address string |
| intended answer (unique, setter's intent) | gazetteer entry (unique, if the address is real) |
| tokens: fodder, indicators, synonyms, link words | tokens: numbers, unit words (座/Block/Flat), names, noise |
| mechanical ops (anagram, reversal…) | mechanical normalisation (numerals, 樓/F, ordering) |
| oracle leaves: synonym, homophone | oracle leaves: fuzzy name match, transliteration, OCR fixes |
| crossers: letters shared with other slots | hierarchy constraints: this block exists in this estate; this floor exists in this block |
| coverage law: every token consumed once | every token consumed once; leftover ⇒ Quarantine(residual) |
| Ok / Quarantine / Reject | the same |
| alternative tokenisations kept alive (lattice) | the same |
| "which clue next" under a time price | "when to call the expensive fuzzy matcher" |

Difference: address parses are flat labelled chunks; clue parses are nested
operator trees. Everything in the table above transfers; the grammar does
not. The two projects should share the `Hyp`-relation kernel, the lattice
tokeniser, the alias-table mechanism and the outcome type, and nothing else.

## 7. Game-playing agents, for orientation

- **CSP/SAT solvers**: propagation + branching heuristic (MRV, VSIDS) +
  conflict-driven nogood learning. Directly applicable; the twist is noisy
  constraints and an incomplete generator.
- **AlphaZero shape**: the LLM is the policy prior (proposals), the kernel
  is the rules engine (verification), the search controller orders
  expansions. We do not learn a value function; we compute beliefs from
  oracle calibration.
- **MCTS with VOI** (Tolpin & Shimony 2012; Sezener & Dayan 2020): node
  selection by value of computation rather than UCT. Our "rollouts" are
  LLM proposals; our "exact evaluations" are verifier runs.

## 8. What changes in the roadmap

- Brief 003 is no longer a selective-answering solver. It is the `Hyp`
  relation, `verify` → `status`/`prov`, `propagate`, and **oracle
  calibration on val** (P(leaf correct | oracle, score)). Headline number:
  exact-solve rate (surviving set is a singleton containing the truth) and
  the calibration curve for quarantined solutions.
- Brief 004 adds `Slot`, `Dom`, arc consistency and nogoods on post-cutoff
  grids. Headline: fully-correct grid rate, and the share of solved grids
  whose trace is *proven* vs *quarantined*.
- Brief 005 is the `wald` pack: price the moves, implement VOC, beat MRV.
- `life-agent` contributes only the stopping rule and the calibration
  machinery. No `u_wrong`.
