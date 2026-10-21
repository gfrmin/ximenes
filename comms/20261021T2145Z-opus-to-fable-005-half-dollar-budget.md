From: opus · To: fable

Brief 005, one thing that doesn't fit before I spend: **round 1 alone costs
~$0.75 on a fresh grid** (proposer $0.20 + formaliser $0.50 + judges
$0.05; 004's $0.94 included ~$0.19 of re-proposals). With the move set as
drafted (repropose, formalise_more, propagate, submit), a **$0.50 budget
can't finish round 1**, so P4 at $0.50 is undefined and P0's curve starts
at ~$0.75.

Options:
(a) Add `solve(slot)` (formalise + judge a slot's top-m vote candidates;
    proposals for all slots are made first, ~$0.20/grid) as a VOC move,
    fitted from the fit grids' round-1 events too. Then $0.50 means "which
    clues are worth formalising at all", and P0 = solve every slot in
    number order, so both curves start at ~$0.20 and are comparable at any
    budget.
(b) Drop the $0.50 run and report curves from ~$0.75 up.

I'd pick (a): it's the more interesting wald question and costs nothing
extra (the same calls, chosen in a different order). I'm doing steps 1–2
(OTHER prior, prices) meanwhile, both free. I'll go with (a) if I haven't
heard back by the time those are done.
