# Brief 017: harder puzzles — does asking directly hold up?

**Status: open (2026-10-24, drafted by `lead`).** Sources approved by the
author on 2026-10-24 ("yes and yes", QUESTIONS.md § 017). Cap **$15**,
inside the Phase 3 envelope as long as 016 ends near its projection (~$15);
if 016's actual spend would put 017 past the $60 envelope, ask `lead`
before the paid stage. Builder: `opus`, on its own machine (the lead's
clone holds no data). Harvesting is $0 and may start while 016's run is
going.

Headline number: **fully correct grids for Opus asked directly (015's D1,
unchanged) on post-cutoff hard blocked cryptics**, pooled over Times
dailies and Telegraph Toughies, with a Beta(1,1) 90% interval; each
publisher reported separately beside it.

## Why
015's 30/40 is on Guardian, Independent and FT dailies. Darmok's claim is
on Times Championship puzzles, which are harder. Whether the direct rate
holds on harder puzzles decides two things: how the note compares itself
with Darmok, and whether hard puzzles are where the hybrid's machinery
earns its keep.

## Stage 0: harvest ($0, builder's machine)
- **Sources:**
  - Big Dave's Crossword Blog (bigdave44.com): Telegraph **Toughie**
    posts. Its robots.txt allows ordinary crawlers.
  - Times for the Times (timesforthetimes.co.uk): **Times daily cryptic**
    posts (not Quick Cryptic, Jumbo, Sunday or Mephisto). Its robots.txt
    sets `ai-train=no`, blocks AI crawlers by name, reserves rights under
    EU Directive 2019/790, and asks for a 10 s crawl delay. The author
    decided on 2026-10-24 that local evaluation is within his use. So:
    nothing from it is ever used for training, fitting, a lexicon or a
    prompt example (D7 already forbids this for post-cutoff data);
    requests use the project's honest User-Agent, never a browser's or an
    AI crawler's; and the delay is 20 s.
  - The Times's and the Telegraph's own sites stay off limits.
- **Protocol:** 012's, unchanged: WordPress REST API, 20 s between
  requests, posts dated from 2026-08-01 (Opus 5.5's post-cutoff floor
  under 012's rule), local only under `data/postcutoff/`, nothing
  committed, the blind-parser checks of 012's answer before any row is
  read, linked-clue puzzles excluded, blocked grids reconstructed
  uniquely or dropped. Barred puzzles are out.
- **Report:** posts, clues parsed and unique grids per publisher, with
  the reasons for drops, as in 012.

## Stage 1: Opus asked directly (cap $15)
- **Grids:** up to **20 Times and 20 Toughie** unique grids, sampled by
  seed **20261031** from Stage 0's output, fixed in `data/eval.json`
  before any grid is read. Fewer if fewer exist; report n.
- **Arm:** 015's D1 exactly: `direct-grid-v1`, Opus 5.5 at high effort,
  pinned settings, one call per grid. No other arm.
- **Smoke:** one grid per publisher, cost reported before the run.
  Harder puzzles may think longer. If the projection exceeds $15, cut
  each publisher to the same smaller n and say so before the run.
- **Report:** fully correct grids, clues, $ per grid, crossing conflicts,
  ECE of stated confidences, and wrong slots per imperfect grid, each per
  publisher and pooled; 015's 30/40 beside it, labelled as different
  puzzles (not paired).

## Decision rule (written before any data; pooled rate, n ≈ 40)
- **Lower bound ≥ 0.5:** the direct result holds on hard dailies. The
  note claims it for the Times and the Toughie with these numbers.
- **Upper bound < 0.5:** hard puzzles are where direct falls off. The
  next brief runs 016's hybrid (if 016 did not lose) on these grids'
  successors; the note says where the direct result stops.
- **Otherwise:** report; the note states the rate with its interval and
  no claim either way.

**The rule can resolve either way.** At n = 40 the lower bound clears
0.5 from about 26/40 (0.65), and the upper bound falls below 0.5 at
about 14/40 (0.35). At n = 30, the thresholds are 20/30 and 10/30.

## Not in this brief
Barred puzzles (Listener, Azed, Mephisto), Times Championship puzzles
themselves (not blogged as a set), and the hybrid on hard puzzles.
