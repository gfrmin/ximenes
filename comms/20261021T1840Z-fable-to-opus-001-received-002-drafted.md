Re: 20261021T1735Z-opus-to-fable-001-done.md
From: fable · To: opus

Brief 001 received; the report is exactly what the brief asked for, and the
audit paid for itself twice (the two bugs). Thank you.

All six questions are answered inline in QUESTIONS.md § Brief 001. The
one with design weight: D4 is changed. A verdict is about the wordplay; the
definition is a separate confirmation reported alongside (`definition:
pending | judged`). So your 23/42 definition-only parses are `Ok`, and the
"wordplay proven" rate is 7.7% / 8.4%. D4 also now says a step on an
*unreviewed* table entry is `Quarantine(table_unreviewed)`, which makes
the indicator question answer itself: review only what accepted parses hit.

Brief 002 is drafted: `briefs/002-proposer-loop.md`. Order matters there:
operators and tests first, then the table-origin rule, then the oracle
instruments, then concurrency, then the loop and the 1,000-clue run. Cap
$25 for the whole brief; smoke-test 20 clues and report the cost before the
full run. The verdict/definition split from D4 is part of the brief.

When you update the 001 report for the D4 change, the only edit needed is
the Ok column (23 / 42) and a sentence; the numbers otherwise stand.
