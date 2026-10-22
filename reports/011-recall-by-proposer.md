# Report — brief 011 (recall by proposer)

Status: **complete (2026-10-22).** Built by `opus`. Spend: smoke tests
**$8.74**, full run **$10.95** (another $1.53 of smoke calls replayed);
**$19.69 in all.** The author approved the run as amended ("go 011").
Cumulative across briefs 000–011: **$122.87**.

## Headline numbers

150 fresh Cryptonite test clues (seed 20261026; brief 000's 1,000 excluded;
Times 88, Telegraph 62, in proportion). Every call returns structured output
(below), at `effort: low`. Gold-in-k is the share of clues whose answer is
among the top k candidates. `sample` candidates are ranked by vote share;
`list` candidates keep the model's order.

| proposer · prompt · pattern | n | k=1 | k=3 | **k=5** | k=10 | all | $ / clue |
|---|---|---|---|---|---|---|---|
| Haiku · sample (k=20) · none | 150 | 0.460 | 0.633 | 0.673 | 0.693 | 0.700 | 0.0095 |
| Haiku · sample · half | 150 | 0.880 | 0.933 | **0.953** | 0.960 | 0.960 | 0.0074 |
| Haiku · list · none | 150 | 0.360 | 0.413 | 0.440 | 0.447 | 0.447 | 0.0005 |
| Haiku · list · half | 150 | 0.800 | 0.833 | 0.840 | 0.847 | 0.847 | 0.0004 |
| Opus · sample (k=5) · none | 50* | 0.900 | 0.920 | 0.920 | 0.920 | 0.920 | 0.0378 |
| **Opus · sample · half** | 150 | **0.987** | 1.000 | **1.000** | 1.000 | 1.000 | **0.0261** |
| Opus · list · none | 150 | 0.793 | 0.813 | 0.840 | 0.847 | 0.847 | 0.0067 |
| Opus · list · half | 150 | 0.960 | 0.973 | 0.973 | 0.973 | 0.973 | 0.0060 |
| Sonnet · list · none | 150 | 0.547 | 0.600 | 0.600 | 0.607 | 0.607 | 0.0057 |
| Sonnet, thinking off · sample (k=10) · half | 150 | 0.740 | 0.747 | 0.747 | 0.747 | 0.747 | 0.0073 |
| Sonnet, thinking off · list · half | 150 | 0.647 | 0.693 | 0.707 | 0.713 | 0.713 | 0.0009 |

\* The first 50 of the sorted sample. **These turned out to be all 2000–09
clues**, because the sample is in date order. On the same 50, Opus `list/none`
is about 4 points above its full-sample figure, so read 0.92 as ~0.88.

**Crossing letters nearly close recall.** With half the letters revealed,
Opus sampling has the gold answer in its top 5 for every one of the 150
clues, and top-1 for 148. Haiku reaches 0.953 at a third of the price. With
no letters, the best measured recall is Opus at ~0.88–0.92. Brief 010 found
that Haiku's 20 samples missed gold for a third of clues; that gap belongs to
the no-pattern round 1, not to re-proposal.

## The pre-registered pick, applied

- **Pattern `half`** (max gold-in-5 at ≤ $0.06 per clue; ties within 2
  points go to the cheaper cell): **Opus · sample · half**, 1.000 at
  $0.026. Opus · list · half is 0.973, 2.7 points behind, so outside the tie
  margin.
- **Pattern `none`** (round 1): Opus · sample · none (0.92, $0.038). But it
  rests on 50 older clues; the next cell, Opus · list · none (0.840 at
  $0.0067), is 6× cheaper.
- **Early stop:** gold-in-5 at `half` is **1.000, 95% bootstrap
  [1.000, 1.000]** (degenerate at 150/150; a Wilson lower bound is ≈ 0.975).
  That is ≥ 0.85, so **013 runs in full.** It is not ambiguous.

For 013's budget: a 30-slot grid costs ~$1.1 for round-1 proposals (Opus
`sample/none`; ~$0.20 with Opus `list/none`), plus ~$0.026 per slot each
time a slot is re-proposed with letters.

## Year-of-clue probe (contamination), top-1 at pattern `none`

| cell | 2000–04 (n=22) | 2005–09 (33) | 2010–14 (47) | 2015–20 (48) |
|---|---|---|---|---|
| Haiku · sample | 0.59 | 0.48 | 0.49 | 0.35 |
| Haiku · list | 0.41 | 0.45 | 0.38 | 0.25 |
| Sonnet · list | 0.77 | 0.55 | 0.55 | 0.44 |
| Opus · list | 0.73 | 0.91 | 0.74 | 0.79 |
| Opus · sample (first 50 only) | 0.82 | 0.96 | — | — |

Haiku and Sonnet fall 20–30 points from the oldest clues to the newest;
Opus is flat. Two readings fit:
- the smaller models remember old clues and Opus solves;
- older clues are easier, and Opus is strong enough not to care.

At these n neither can be excluded. Opus's 0.79–0.91 on Cryptonite is an
upper bound until the post-cutoff grids (012/013) measure it.

## Failures, refusals, tokens

| cell | enumeration fails (raw answers) | pattern fails (valid answers) | refusals | output tokens / message |
|---|---|---|---|---|
| Haiku sample none / half | 0.125 / 0.041 | — / 0.275 | 0 | 900 / 680 |
| Haiku list none / half | 0.395 / 0.125 | — / 0.192 | 0 | 869 / 740 |
| Opus sample none / half | 0.008 / 0.007 | — / 0.006 | 0 | 325 / 203 |
| Opus list none / half | 0.157 / 0.008 | — / 0.024 | 0 | 274 / 234 |
| Sonnet list none | 0.319 | — | 0 | 513 |
| Sonnet thinking off, sample / list half | 0.111 / 0.125 | 0.294 / 0.172 | 0 | 15 / 28 |

The list rates count every listed answer, and lists run long. Haiku often
ignores the given letters (27% of its valid answers don't fit the pattern).
Opus almost never does.

## Amendments made before the run (all committed first)

1. **Answer extraction.** The first smoke kept each reply's first line.
   Sonnet 5.5 reasons in text before answering, so all 200 of its samples
   were prose and scored 0. The author asked for something better than "last
   line", and fable chose structured output: `output_config.format` with a
   JSON schema, `{"answer"}` for `sample` cells and `{"candidates"}` for
   `list` cells, for every model (`data/instruments.json` `formats`). This
   also makes the format a property the solver can rely on.
2. **Cells.** Under the schema, Sonnet thinks about 3× longer at
   `effort: low` (~2,000 output tokens per sample, against Opus's ~800) and
   sometimes returns nothing. Its `sample` cells (unpickable at
   $0.13–0.21 per clue) and `list/half` (Opus is cheaper and stronger) were
   dropped. Opus `sample/none` was cut to the first 50 clues. Sonnet with
   thinking off (`thinking: between_tools`, the only model of the three that
   allows it) was added at `sample/half` and `list/half`. Plan:
   `data/eval.json` `recall.cells` (`f8f77bc`).
3. `instruments._answer_line` (the last non-empty line) replaces the
   first-line rule for free-text replies. One-line replies, and so every
   earlier brief's logs, are unaffected.

## What was built

- **`ximenes.proposers`:**
  - `sample_clues` (excludes seed 20261021's clues, publisher-proportional
    by largest remainder);
  - `half_pattern` (alternate letters from a seeded offset, never more
    than half);
  - `parse_list`, `candidates` and `pick` (the pre-registered rule);
  - a clue-level bootstrap, the year probe, the cell plan and the CLI
    (`--plan`, `--n`, `--log` replay, `--thinking`).
- **Instruments:**
  - `propose_list` (prompts `list-v1` / `list-pattern-v1`);
  - an optional structured format and thinking type on all three proposer
    instruments; both keys are absent from every earlier logged input.
- **Tests** (`tests/test_011_proposers.py`):
  - sample exclusion and proportions;
  - the pattern rule;
  - a parser case table;
  - candidate filtering;
  - the pick rule;
  - structured-reply extraction;
  - the cell plan;
  - **replay of a logged run reproduces every number** (the real run also
    replays exactly: `20261022T084100Z-proposers-stub-…`).

## Supersessions (D8)

None.

## Reproduce

```bash
uv run python -m ximenes.proposers --plan --max-usd 20 \
  --log runs/20261022T064250Z-proposers-anthropic-c490dff33fa344b98d088d0ce1dfbaa2.jsonl \
        runs/20261022T082456Z-proposers-anthropic-8bd0b39c9f5341309fd1acfbbc449217.jsonl
# run 20261022T082945Z-proposers-anthropic-a0270d4d2f2a41c2ae5ad17b91e9f2ae; replay:
uv run python -m ximenes.proposers --plan --backend stub --log runs/<that run>.jsonl
```

## Kit output

```
== lint: forbidden constructs in src/
== lint: numeric literals in src/
== lint: postcutoff must never be committed
== ruff
All checks passed!
== pytest
........................................................................ [ 26%]
........................................................................ [ 53%]
........................................................................ [ 80%]
...................................................                      [100%]
267 passed in 18.14s
== kit: GREEN
```

## Open questions

See `QUESTIONS.md` § Brief 011.

## Probability complete

**0.8.** Every build item and test exists, the run replays exactly, and the
pick and early stop were applied as pre-registered. Doubts:
- the cell plan was amended twice before the run (both amendments are
  recorded);
- the 50-clue Opus `sample/none` cell is all older clues, which biases the
  round-1 pick upward;
- the `half` result is at the ceiling, so its interval says little beyond
  "≥ ~0.97".
