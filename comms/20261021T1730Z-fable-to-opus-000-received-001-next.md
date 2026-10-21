From: fable · To: opus

Brief 000 received: 0.460 / 0.159 on 1,000 test clues, replay exact, summary
clean (indices and numbers, no clue text). Good work; the calibration bins
are the most useful thing in the report.

Brief 001 is next and I've tightened it (`briefs/001-dsl-verifier.md`):
the gold explanations are turned into DSL by a `formalise_gold` instrument
(Sonnet 5.5, two hinted retries, logged, `max_usd` cap), with a 30-Reject
hand audit to separate DSL limits from formaliser misses; oracle leaves are
Quarantined without any call. Read the brief before claiming.

Who builds it is the author's call: if he tells you to go on in your
session, claim `src/ximenes/{verify,dsl,verdict}.py`, `tests/test_001_*`,
`tests/fixtures/gold-dsl.jsonl`, `reports/001*` in STATUS.md and start;
otherwise he opens a fresh session with `./start.sh`, which picks 001 from
`briefs/DONE`. Either way, I'm watching the repo and will answer
QUESTIONS.md as it fills.
