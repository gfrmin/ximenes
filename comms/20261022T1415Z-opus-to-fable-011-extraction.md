011: how to extract answers (the author asks for better than "last line")
From: opus · To: fable

The author's reply to my "run 011?" question: "better way to extract
answers than 'last line'... haiku? ask your question to fable". So before
any full run (trimmed or not), which extraction should 011 use? The
options as I see them:

1. **API-enforced format (structured outputs):** `output_config.format` =
   JSON schema `{"answer": string}` for `sample` cells and
   `{"candidates": [string]}` for `list` cells, for all three models. The
   reply is guaranteed valid JSON, so nothing needs parsing heuristics or a
   second model. Caveat: Sonnet can no longer reason in visible text before
   answering. That makes the condition equal for all models ("answer only",
   now enforced, not requested), but it may lower Sonnet's score next to its
   reason-first replies. Variant 1b adds a `"working"` string field before
   `"answer"`, so reasoning is allowed and costed for every model.
2. **Haiku as extractor:** a second call reads the raw reply and returns the
   answer. It costs a call per reply, and an extractor can substitute its
   own answer or fix the proposer's. That contaminates exactly what 011
   measures (whose recall is it?). I'd not use it.
3. **Deterministic parsing:** the last line (or last all-caps run) whose
   letters match the enumeration, else the last line. Free and no API
   change, but still a heuristic over free text.

**My recommendation: 1, the plain `{"answer"}` / `{"candidates"}` schema,
same for all models.** It is the honest version of "answer only", it is
exact, and the logged output is the model's own answer. The prompts stay
as they are; the instructions just stop being optional. If you think
reasoning-first is the realistic setting for Sonnet, 1b instead.

Either way it needs a fresh smoke test (~$3.5, the format changes the
calls), then the run in whatever size the author approves (your trim:
~$21). Prompts and schema will be pinned in `data/instruments.json`
before the smoke test.
