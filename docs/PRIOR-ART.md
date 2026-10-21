# Prior art (condensed; full report in the project doc "Cryptic crosswords as a decision-theoretic parsing game")

## What exists
- **Darmok** (Chatterjee, UT Austin, 2025–26). Ensemble of Gemini 3.1 Pro + Claude Fable 5 (GPT-5 / GPT-6 Astra as backups). Beat the human winner of the 2026 Times Championship final by ~3 min; got SNARF (a *visual* deletion clue) that 3 of 5 finalists missed. No paper, no code. One disclosed process change: attempt all clues before entering any.
  https://www.theguardian.com/puzzles/crossword-blog/2026/oct/20/could-this-be-a-deep-blue-moment-for-the-cryptic-crossword
- **Andrews & Witteveen, ICML 2025**, "A Reasoning-Based Approach to Cryptic Crossword Clue Solving". Gemma2-9B generates 20 candidates → 10 wordplay hypotheses each → formaliser writes Python `assert` proofs → verifier walks the AST. 32.5% top-1 on 200 Cryptonite test clues (±3.3). Code Apache-2: https://github.com/mdda/cryptic-crossword-reasoning-verifier. arXiv 2506.04824.
  - Verifier holes they name: comment-only proofs; `if` routing; `assert X == False`; disconnected steps. On *Quick* clues the formaliser (46.7%) loses to plain majority vote (55.3%) because of false verifications. Synonyms/definitions fall back to an LLM vote.
- **Deits** (2013–2022). PCFG clue solver; 8.6% on Cryptonite; indicator/abbreviation lists reused by A&W. https://github.com/rdeits/CrypticCrosswords.jl
- **Cryptonite** (Efrat et al., EMNLP 2021): 523k Times/Telegraph clues, answer-disjoint splits. arXiv 2103.01242. Contamination: overlaps Rozner's Guardian "Init" train split, which was re-released; frontier models have likely seen test answers.
- **Wordplay dataset** (Andrews 2024): scraped Fifteensquared / Times for the Times explanations with `{definition}` spans. Nearest thing to a parse treebank, but notation is per-blogger. https://github.com/mdda/cryptic-wordplay
- **Grid solvers** (American): Proverb (1999, probabilistic CSP, probabilities as interchange format), Dr.Fill (JAIR 2011, confidence-gap slot ordering), Berkeley Crossword Solver (ACL 2022, loopy BP maximising expected letter overlap; arXiv 2205.09665), SweepClip (NAACL 2025, arXiv 2406.09043).
- **Metareasoning**: Russell & Wefald 1991; Hay, Russell, Tolpin, Shimony UAI 2012 (arXiv 1207.5879); Sezener & Dayan UAI 2020 (arXiv 2002.04335); Callaway et al. UAI 2018. No crossword solver has treated "which clue next" as a metalevel MDP.
- **Semiring parsing** (Goodman 1999): same parser, swap semiring → recognition / Viterbi / n-best / derivation forests. The bridge to a provenance-semiring kernel. Provenance semirings: Green, Karvounarakis, Tannen PODS 2007.

## What does not exist (as of 2026-10-21; re-check arXiv cs.CL "cryptic" before claiming)
1. A cryptic verifier that is sound by grammar (no execution, token-coverage law).
2. Calibrated per-clue posteriors with abstention / set-valued answers, risk–coverage curves.
3. Grid BP using *verified wordplay* as likelihood and set answers as slot domains.
4. A value-of-computation policy for clue ordering under a time/token price.

## Why the SNARF clue matters
"Wolf trap missing its lowest crosspiece? (5)": SNARE with the bottom stroke of E removed → F. Glyph-level, outside any string algebra. The DSL will never make it `Ok`; it can only arrive as a `Quarantine(cryptic_def)` with a residual. That is the honest answer, and the decision layer prices it.
