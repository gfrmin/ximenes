# Brief 015: depth or enumeration on the residual

**Status: open (2026-10-24).** The Phase 3 envelope of $60 is recorded in
ROADMAP's Spending section. The lead for this brief is `lead`
(`docs/LEAD.md`). Order: A0, then D, then A, then B only if A meets its
bar. Caps: A0 $0, D $25, A $15. B gets its own cap (~$50) from the author
if A triggers it.

Headline number: on the **stuck slots** of 013 and 014 (the slots where the
gold answer was never proposed), **gold-in-5 per proposer arm**, with
Beta posteriors and $ per slot. If the bar below is met, also **fully
correct grids** on 20 never-read post-cutoff grids, for the calibrated
frontier with and without escalation, paired.

## Why
014's failures are 21 guessed slots where gold was "still not proposed
after up to 20 pattern samples and the list fallback", plus 11 committed
wrong. Persistence was **breadth at low effort**: every proposer call in
`data/instruments.json` runs at `effort: low`. More low-effort samples on
a hard slot returned the same misses.

The untested lever is **depth**: one call that thinks for longer, or a
stronger model. OpenAI's 2026-10-06 release of 372 families of maths
results is evidence that depth matters more than breadth. By its account,
nearly all of them came from one prompt to one agent, at about three hours
of thinking per kept result. Its September Navier–Stokes run used 10,000
agents instead. That is a different domain at a vastly larger scale, so it
moves the prior and settles nothing. This brief measures depth here, on the
slots that need it.

The other route is the author's (2026-10-24). The answer is in a
finite word list, and the crossing letters cut that list to a few entries.
So a slot's candidates can be *enumerated*, and the model only has to
*choose* among them, which is easier than recalling the answer. That
changes three things:
- Recall becomes the word list's coverage, a number we can measure for $0.
- OTHER in BP becomes P(gold not in the list), which is small and can be
  estimated. Today it is a floor.
- The DSL gets a job it didn't have in 014. Checking each enumerated word
  against the clue, top-down, is the verifier's natural direction. The
  mechanical operations on literal fodder (anagram, hidden word, reversal,
  letter selection) are exactly where models are weakest, because they see
  tokens, not letters. There, the DSL can *generate* candidates, and
  generate them completely.

## Stage D: ask the model directly (cap $25; run after A0)
"Just ask the model" was measured only clue by clue, with Haiku on
Cryptonite (brief 000). Nobody has measured a frontier model given the
whole puzzle and allowed to think. This is the baseline any reader will ask
for. It is also the honest answer to whether the bespoke solver beats
asking directly.
- **Grids:** the 40 evaluation grids of 013 and 014, paired against their
  stored results. Use 014's 8/20 for the calibrated frontier. Use 013's
  10/20 and 014's 7/20 for the full solver. The direct arm has no tunable
  parameters. Commit its prompt and settings before any of these grids is
  called. Smoke-test on 014's grid #1 only, which is already a smoke grid,
  and don't revise the prompt after that.
- **Input:** the clue list (numbers, clues, enumerations) and the grid as
  text: each slot with its length and its crossings ("1A letter 3 = 2D
  letter 1"). Nothing from our solver.
- **Arms:** one call per puzzle, structured output
  `{slot: {answer, confidence}}`:
  - D1: `claude-opus-5-5` at high effort.
  - D2: `claude-fable-5-1` at high effort, if the account can call it.
    Apply 012's post-cutoff rule to its knowledge cutoff and report any
    grids dropped.
  - If the smoke test projects D1 + D2 over $25, run D1 only.
- **Free checks on D's output:** crossing conflicts per grid, and the ECE
  of its stated confidences.
- **Report:**
  - fully correct grids, clues and $ per grid;
  - the paired tables and P(direct > solver) under Beta(1,1), against the
    full solver over 40 grids and against the calibrated frontier over
    014's 20.
- **Decision, written now:**
  - "D's best arm" is D1 or D2, whichever has more fully correct grids
    (ties: D1). With two arms this picks the winner after the fact, so
    the report gives each arm's P separately as well; the rule reads
    the best (amended by `lead`, 2026-10-24, before any data). P is
    computed as in 014: independent Beta(1,1) posteriors on each rate.
  - If P(D's best arm > full solver) ≥ 0.8: asking directly beats the
    bespoke route. The next brief feeds D's answers in as the calibrated
    solver's first-round proposals (a hybrid), and the note's headline
    becomes that comparison.
  - If ≤ 0.2: the note adds "a bespoke solver beats asking the model
    directly", with the paired numbers.
  - Otherwise, report both, with no change of plan.

## Stage A0: enumeration ($0, no calls)
On the same stuck slots as Stage A (defined below):
- **Word list W:** Open English WordNet's lemmas ∪ Moby's headwords and
  entries, both already fetched by `setup.sh` (brief 008). Reduce each to
  letters and key it by enumeration, so (4,5) matches only two-word
  entries of 4 and 5 letters. Add no new data source in this brief.
- **Report per slot:**
  - gold ∈ W (the coverage, with a Beta interval);
  - |W ∩ pattern|, as a distribution;
  - whether the mechanical generators on the clue's literal fodder produce
    gold (anagram of contiguous words with the right letter count; hidden
    word, forwards and reversed);
  - which words in W ∩ pattern the verifier admits, as Ok or Quarantine,
    and whether gold is one of them.
- **Report by kind of miss:** split the misses into those not in W and
  those in W but not chosen. That split decides between arm 5 and the
  depth arms.

## Stage A: slot-level recall (dev data; cap $15)
- **Slots.** Every slot in 013's and 014's evaluation grids whose gold was
  not among the candidates at the end state (gold never proposed in any
  round; committed-wrong slots are not stuck slots). Take each slot's final
  crossing pattern from the logs. Those grids are already read, so from
  now on they are dev data and never an evaluation set again. Say so in
  `data/eval.json`.
- **Arms.** One structured-output call per slot per arm, top 5 with shares.
  Arms 1–4 use the same prompt as `propose_pattern`, with only the model and
  effort changed:
  1. `claude-opus-5-5` at low effort, 5 resamples: the control. This is
     how often plain resampling finds gold.
  2. `claude-opus-5-5`, high effort.
  3. `claude-opus-5-5`, max effort.
  4. `claude-fable-5-1`, high effort. Drop this arm, and say so, if the
     smoke test shows the account can't call it.
  5. **Choose from the list:** `claude-opus-5-5` at low effort, given the
     clue, the pattern and W ∩ pattern (with the words the verifier
     admitted marked). It returns up to 5 words from the list, with
     shares, plus OTHER. Run it only where |W ∩ pattern| ≤ 300; above
     that, count the slot as a miss for this arm and report how many
     there were.
  6. **Union:** arm 5 ∪ the best of arms 2–4. This costs nothing to compute.
- **Smoke test:** 3 slots per arm. Report the cost per call. If the
  projected cost of the full Stage A exceeds $15, cut arm 3 first.
- **Report:** gold-in-1 and gold-in-5 per arm, with Beta(1,1) 90%
  intervals; $ per slot; and the arm's top share on slots where it is
  wrong, because Stage B's calibration needs it.

**Decision rule, written before any call.** Let r be gold-in-5 on the stuck
slots for the best of arms 1–6. A0's generator-plus-verifier counts as
an arm at $0.
- If r's lower bound is ≥ 0.25, run Stage B with that arm. Where two arms
  tie within their intervals, use the cheaper one.
- If every arm's upper bound is < 0.10, depth does not reach the residual.
  The note says so, and 016 (other model families) is the last lever.
- Otherwise, report and stop; `lead` decides.

## Stage B: end to end (only if triggered; cap set by the author then, ~$50)
- **Grids:** 20 post-cutoff grids that have never been read. Use 013's
  reserve if any remains. Otherwise use a new harvest of posts after
  2026-10-22 under 012's protocol (REST API, 20 s delay, blind parser,
  nothing committed), with linked-clue puzzles excluded as before. Fix the
  seed and the list in `data/eval.json` before any grid is read.
- **Arms, paired:**
  - (a) 014's `frontier_calibrated`, unchanged.
  - (b) The same, plus **escalation**. When (a) would stop (no new
    candidates, or budget), take the uncommitted slot with the most known
    letters. Try the cheapest arm that met the bar first (arm 5 if it
    did), then the depth arm, then re-run BP. Repeat until every slot is
    committed or the budget is spent. If arm 5 is used, OTHER for that
    slot is A0's estimate of P(gold ∉ W).
- **Calibration of escalated candidates:** fit the same logistic form as
  013, on Stage A's slots, and write it to `data/` before Stage B. Note
  that those slots are selected (stuck only). Stage B's paired outcome is
  what decides, not this fit.
- **Budget:** $3 per grid, as in 014, with a second readout at $5.
- **Report:** fully correct grids per arm, the paired table, P(b > a)
  under Beta(1,1), the paired clue difference with a bootstrap interval,
  and $ per grid. If P(b > a) ≥ 0.9, escalation becomes the solver's
  default, and the note's headline is rerun on the pooled grids.

## Not in this brief
Open-weight models on `steel` (the old 015) move to 016, still low
priority. The prior that a model weaker than Opus proposes what a
deep-thinking Opus misses is lower than the prior for depth.
