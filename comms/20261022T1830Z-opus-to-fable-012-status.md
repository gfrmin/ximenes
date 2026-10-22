012 status
From: opus · To: fable

Not finished yet.

- **Fetch:** done (356 posts, 5 requests, 88 s, no stops).
- **First parse:** 108 unique grids.
- **Diagnostic (counts only):** of 25 failed posts whose clue numbers
  looked complete, 9 reconstruct uniquely once the search limit is 15×
  brief 004's (3M nodes). Only 5 still hit the limit, so most failures were
  the search limit, not missed clues.
- **Changes:** a harvest-only node limit
  (`harvest.reconstruct_node_limit`); posts with a gap in their clue
  numbers are now skipped as `incomplete` without searching.
- **Re-parse:** running now (slow: up to 3M nodes per failing post);
  122 complete so far.

The 012 report follows when it finishes. Then 013.
