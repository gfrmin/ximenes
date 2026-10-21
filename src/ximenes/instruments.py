"""Instruments: the only door to LLMs and oracles (DESIGN D6).

An `Instrument` maps (instrument name, model, input) to (output, cost). Two
backends exist: `anthropic` (live API) and `stub` (replays a JSONL log and
raises if an input is missing). `logged` wraps either one so every call is
appended to `runs/<run-id>.jsonl` as `{ts, instrument, model, input, output,
cost}`; replaying that log with `stub` reproduces the outputs exactly.
"""

from __future__ import annotations

import json
import pathlib
import threading
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Protocol

from .data import DATA

Json = Any
Cost = dict[str, Json]

PROPOSE_ANSWERS = "propose_answers"
SETTINGS: dict[str, Json] = json.loads((DATA / "instruments.json").read_text())

PROMPTS = {
    "answer-only-v1": (
        "Solve this cryptic crossword clue. The numbers in brackets give the "
        "answer's word lengths. Reply with the answer only, in capital letters, "
        "and nothing else.\n\n{clue_text} ({enumeration})"
    ),
}


class Instrument(Protocol):
    def __call__(self, instrument: str, model: str, inp: Mapping[str, Json]) -> tuple[Json, Cost]:
        ...


class MissingFromLog(KeyError):
    """The stub backend was asked for an input its log does not contain."""


def call_key(instrument: str, model: str, inp: Mapping[str, Json]) -> str:
    return json.dumps([instrument, model, inp], sort_keys=True, ensure_ascii=False)


def read_log(path: pathlib.Path) -> tuple[dict[str, Json], ...]:
    with open(path, encoding="utf-8") as f:
        return tuple(json.loads(line) for line in f if line.strip())


def stub_backend(log: pathlib.Path) -> Instrument:
    """Replay outputs from a log. Raises MissingFromLog for unseen inputs and
    ValueError if the log holds two different outputs for one input."""
    table: dict[str, tuple[Json, Cost]] = {}
    for r in read_log(log):
        k = call_key(r["instrument"], r["model"], r["input"])
        if k in table and table[k][0] != r["output"]:
            raise ValueError(f"{log}: conflicting outputs for {k}")
        table[k] = (r["output"], r["cost"])

    def call(instrument: str, model: str, inp: Mapping[str, Json]) -> tuple[Json, Cost]:
        k = call_key(instrument, model, inp)
        if k not in table:
            raise MissingFromLog(f"{log}: no record for {k}")
        return table[k]

    return call


def replay_then(log: pathlib.Path, live: Instrument) -> Instrument:
    """Replay calls found in `log`; send only the rest to `live` (resume a run)."""
    replay = stub_backend(log)

    def call(instrument: str, model: str, inp: Mapping[str, Json]) -> tuple[Json, Cost]:
        try:
            return replay(instrument, model, inp)
        except MissingFromLog:
            return live(instrument, model, inp)

    return call


def logged(backend: Instrument, path: pathlib.Path) -> Instrument:
    """Append every call through `backend` to `path` as one JSON line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()

    def call(instrument: str, model: str, inp: Mapping[str, Json]) -> tuple[Json, Cost]:
        output, cost = backend(instrument, model, inp)
        record = {
            "ts": datetime.now(UTC).isoformat(),
            "instrument": instrument,
            "model": model,
            "input": dict(inp),
            "output": output,
            "cost": cost,
        }
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with lock, open(path, "a", encoding="utf-8") as f:
            f.write(line)
        return output, cost

    return call


def usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    price = SETTINGS["prices_usd"].get(model)
    if price is None:
        return None
    per = SETTINGS["tokens_per_price_unit"]
    return (input_tokens * price["input"] + output_tokens * price["output"]) / per


def _first_line(message: Any) -> str:
    text = "".join(b.text for b in message.content if b.type == "text")
    return next((ln.strip() for ln in text.splitlines() if ln.strip()), "")


def anthropic_backend() -> Instrument:
    """Live backend. Needs the `llm` extra and ANTHROPIC_API_KEY (or another
    credential the SDK resolves). No sampling parameters are sent: current
    models reject non-default temperature, so samples use the API default."""
    import anthropic  # optional dependency; imported only when used

    client = anthropic.Anthropic(max_retries=SETTINGS["anthropic"]["max_retries"])

    def sample(model: str, inp: Mapping[str, Json]) -> Any:
        prompt = PROMPTS[inp["prompt"]].format(**inp)
        return client.messages.create(
            model=model,
            max_tokens=inp["max_tokens"],
            output_config={"effort": inp["effort"]},
            messages=[{"role": "user", "content": prompt}],
        )

    def call(instrument: str, model: str, inp: Mapping[str, Json]) -> tuple[Json, Cost]:
        if instrument != PROPOSE_ANSWERS:
            raise ValueError(f"anthropic backend has no instrument {instrument!r}")
        messages = [sample(model, inp) for _ in range(inp["k"])]
        tokens_in = sum(m.usage.input_tokens for m in messages)
        tokens_out = sum(m.usage.output_tokens for m in messages)
        cost = {
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "usd": usd(model, tokens_in, tokens_out),
            "refusals": sum(m.stop_reason == "refusal" for m in messages),
        }
        return [_first_line(m) for m in messages], cost

    return call


def propose_answers(
    clue_text: str, enumeration: str, k: int, model: str, *, backend: Instrument
) -> list[str]:
    """k independent answer samples for one clue. `enumeration` as in '4,3-2'."""
    inp = {
        "clue_text": clue_text,
        "enumeration": enumeration,
        "k": k,
        **SETTINGS[PROPOSE_ANSWERS],
    }
    output, _ = backend(PROPOSE_ANSWERS, model, inp)
    return list(output)
