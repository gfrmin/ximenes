# Models and workflows: a method for problems with a right answer

Draft by `fable`, 2026-10-24, from what ximenes measured (briefs 000–014)
and what other projects of the author's showed. It covers problems where
right and wrong are clear: a grid has one solution, an address one
premises, a proof checks or doesn't. It does not cover open-ended
judgement.

## 1. The division of labour

**The model reads and proposes.** Don't build a workflow that competes
with it on language: meaning, recall, paraphrase.
- In ximenes, the sound-by-grammar wordplay verifier (a theory of how
  clues work, built over five briefs) added no accuracy over a calibrated
  frontier model: 7 vs 8 of 20 grids fully correct, P(verifier better) =
  0.375 (014).
- In a separate address-resolution project, a frontier model's reading of
  casual text did at least as well as the hand-built parser.

**The workflow holds the world.** That means finite sets the model can't
recall exactly: the grid's crossings, a word list, a gazetteer, a game's
state, a schema.
- Crossing letters and belief propagation took the same candidates from
  0.78 to 0.97 of clues right (013).
- In the address project, every key comes from the gazetteer by
  construction, so an invented key is impossible, not merely unlikely.
- A finite world also turns *recall* into *coverage*: is the answer in
  the list? That can be measured for $0 (015 A0).

**The workflow enforces the exact constraints the model is bad at.** This
covers letters rather than tokens, consistency across many slots, counts,
provenance, and any operation that is mechanical once stated.

**The workflow decides: calibrated probabilities, commit, stop.**
- Raw model shares were underconfident (ECE 0.177, against 0.064 fitted),
  so the uncalibrated solver committed 341 slots instead of 495 and ran
  out of crossing letters (013).
- Calibration, fitted on held-out data, was the largest single
  contribution after the crossing letters.

**Checking is for trust, not accuracy, unless the checker generates.**
- A verifier that admits none of ~3,000 mutant parses is worth having,
  because each verified answer names what it rests on. It still didn't
  raise the score.
- A checker raises the score when it works top-down from a finite set:
  enumerate what fits, then check each item. That is the direction the
  constraints make cheap.
- OpenAI's October 2026 maths release shows the same split at scale: the
  model reasoned, and Lean checked. Lean checks the statement *as
  encoded*, so fidelity of the specification is the remaining risk.
  ximenes has the same risk: the verifier checks the wordplay, and the
  definition is only reported alongside (DESIGN D4).

**Corollary.** Build the workflow around what the model lacks (the world,
exactness, calibration), not around a theory of the domain. The elaborate
grammar was a theory of the domain. The grid was something the model
lacked.

## 2. Choosing what to build: the decision-theoretic loop

1. **Write the loss first.** Pick one number the decision reads: fully
   correct grids, or expected loss under the label posterior. Where the
   task fixes the loss (one right answer, submit once), don't elicit a
   utility; ximenes needs no u_wrong.
2. **Measure the strongest simple baseline before building.** That means
   the frontier model given the whole problem and allowed to think, with
   its cost. ximenes measured "just ask" only clue by clue with a small
   model (000), and gets to the whole-puzzle baseline only at 015 D.
   That was the most expensive omission in the plan.
3. **Decompose the residual.** Where does the loss live?
   - Use a failure taxonomy: never proposed / proposed but not chosen /
     committed wrong.
   - Or use a bounds table, which prices each class of loss as an upper
     bound on what fixing it is worth.
   - Bound before build: never build a fix whose upper bound is below its
     cost.
4. **Order by value of information per dollar, and per minute of the
   author's time.**
   - Ask of each measurement: which decision would each outcome change?
     If none, don't buy it. Labelling more rows, or measuring a sample
     whose labels can't be used, often fails this test.
   - Free measurements come first (015 A0).
5. **Pre-register.**
   - Decision rule: three bands (promote / drop / no change), written
     before the data exists.
   - Data splits: fixed before reading.
   - Evaluation data: read once.
   - Tables: committed before evaluation, checked from git history.
   - Amendments: dated, and made before the data they govern.
   - A stop rule for the whole line of work (013: at least 10% of grids
     fully correct at ≤ $5 per grid, or the product becomes an assistant).
   - Check that the rule's success case can occur under the brief's own
     model. Two ximenes briefs had a bar that could not be met.
6. **Watch for shared error.** If the labeller, judge or reviewer is the
   same model family as the proposer, their agreement is inflated. Refit
   the truth without them, or use another family for cold reads.
7. **Breadth is not depth.** More samples at low effort returned the same
   misses on the hard slots: persistence did not help (014). Depth (one
   call that thinks longer, a stronger model) or a different generator
   (enumeration) are the candidates, and 015 measures them.
8. **Report receipts.** Publish every denominator (including what was
   excluded and what failed), the cost, the prompts and replayable logs.
   That is what the field now asks of AI results, and what makes a small
   result credible.

## 3. Building with coding agents

- **Match the weight of governance to what an undetected error would
  cost.**
  - ximenes dropped the cage, charter and signatures, and ran on `master`
    with a mechanical kit in CI. It did 15 briefs in three days.
  - Heavy governance earns its keep where the system modifies itself, or
    an error is irreversible.
- **Mechanical checks over prose.** Lints (no numbers in the kernel, no
  forbidden calls), tests from earlier briefs that can't be edited, and a
  git-history check that tables precede evaluation. A rule that isn't
  checked is a hope.
- **The repo is the only channel.** `AGENTS.md`, claims in `STATUS.md`,
  one file per message in `comms/`, questions by brief.
- **A brief is a measurement:** one headline number, the decision rule,
  a cap, a smoke test.
- **Log every model call and make it replayable.** A run stopped by an
  account limit was resumed at $0 by replaying its logs (014).
- **Delegate spend by envelope,** with a cap per brief.
- **Separate the lead from the builder.** For anything irreversible, the
  reviewer should come from another model family.
- **Each incident becomes a mechanism** (`docs/INCIDENTS.md`): a hook, a
  lint or a test, not a reminder.

## 4. What the agent itself should embody
The same division applies inside an agent that solves such problems:
- **Model outputs are evidence, weighed by a likelihood and calibrated on
  held-out data.** They are never taken as fact, and never as a fixed
  rewrite of the input.
- **The hypothesis space is explicit and finite where possible.** The
  mass on "none of the above" is estimated, not floored.
- **Acts are scored by a proper scoring rule,** and abstaining or
  committing is an act with a cost.
- **Metacomputation is buying the next computation by its value.** In
  ximenes it beat attempting everything, but tied a simple heuristic
  (005, 006). Expect a good heuristic to sit near the optimum, and
  measure where exactness pays before building machinery for it.
- **Generators where the world is finite, checkers everywhere else.**

## 5. Checklist for a new problem
1. Is right and wrong clear? Is there an oracle, or labels you trust?
   (If not, this method applies only in part.)
2. What is the loss, and what single number does the decision read?
3. What does the frontier model achieve if simply asked, with thinking,
   and at what cost?
4. What does the model lack here: a finite world, exact constraints,
   calibration? Build those, in that order of measured value.
5. Where does the residual loss live? Bound each fix before building it.
6. Next measurement: the one with the highest value per dollar, with its
   decision rule written now.
7. Receipts: denominators, costs, prompts, logs.
