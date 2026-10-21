"""Instruments: the only door to LLMs and oracles (DESIGN D6).

An `Instrument` maps (instrument name, model, input) to (output, cost).
Backends: `anthropic` and `ollama` (live APIs) and `stub` (replays a JSONL
log and raises if an input is missing). `logged` wraps either one so every call is
appended to `runs/<run-id>.jsonl` as `{ts, instrument, model, input, output,
cost}`; replaying that log with `stub` reproduces the outputs exactly.
"""

from __future__ import annotations

import json
import pathlib
import threading
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Protocol

from .data import DATA
from .prompts import ANSWER_ONLY_V1, FORMALISE_USER, formalise_system

Json = Any
Cost = dict[str, Json]

PROPOSE_ANSWERS = "propose_answers"
SETTINGS: dict[str, Json] = json.loads((DATA / "instruments.json").read_text())

PROMPTS = {"answer-only-v1": ANSWER_ONLY_V1}
FORMALISE_GOLD = "formalise_gold"


class Instrument(Protocol):
    def __call__(self, instrument: str, model: str, inp: Mapping[str, Json]) -> tuple[Json, Cost]:
        ...


class BudgetExceeded(RuntimeError):
    """A run's logged cost reached its max_usd; resume with --log and a higher cap."""


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


def budgeted(backend: Instrument, max_usd: float) -> Instrument:
    """Refuse new calls once the cost spent through `backend` reaches max_usd."""
    lock = threading.Lock()
    spent = [0.0]  # the one mutable cell; guarded by lock

    def call(instrument: str, model: str, inp: Mapping[str, Json]) -> tuple[Json, Cost]:
        with lock:
            if spent[0] >= max_usd:
                raise BudgetExceeded(f"spent ${spent[0]:.2f} of max_usd ${max_usd:.2f}")
        output, cost = backend(instrument, model, inp)
        with lock:
            spent[0] += cost.get("usd") or 0.0
        return output, cost

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


def _input_tokens(m: Any) -> int:
    u = m.usage
    return u.input_tokens + (u.cache_read_input_tokens or 0) + (u.cache_creation_input_tokens or 0)


def _message_usd(model: str, m: Any) -> float:
    """Input at the base price, cache reads and writes at their multipliers."""
    price = SETTINGS["prices_usd"][model]
    mult = SETTINGS["cache_price_multipliers"]
    u = m.usage
    tokens = (u.input_tokens * price["input"]
              + (u.cache_read_input_tokens or 0) * price["input"] * mult["read"]
              + (u.cache_creation_input_tokens or 0) * price["input"] * mult["write"]
              + u.output_tokens * price["output"])
    return tokens / SETTINGS["tokens_per_price_unit"]


def _formalise_user(inp: Mapping[str, Json]) -> str:
    tokens = " ".join(f"[{i}] {t}" for i, t in enumerate(inp["tokens"]))
    previous = "".join(
        f"Your earlier parse:\n{p['src']}\nwas rejected: {p['rule']}. {p['hint']}\n"
        for p in inp["previous"]
    )
    return FORMALISE_USER.format(
        clue=inp["clue"], tokens=tokens, answer=inp["answer"],
        definition=inp["definition"], wordplay=inp["wordplay"],
        previous=previous + ("Write a corrected parse.\n" if previous else ""),
    )


def _expression(message: Any) -> str:
    """The reply's expression: text blocks joined, code fences dropped."""
    text = "".join(b.text for b in message.content if b.type == "text")
    lines = [ln for ln in text.strip().splitlines() if not ln.strip().startswith("```")]
    return "\n".join(lines).strip()


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

    def formalise(model: str, inp: Mapping[str, Json]) -> Any:
        return client.messages.create(
            model=model,
            max_tokens=inp["max_tokens"],
            output_config={"effort": inp["effort"]},
            system=[{"type": "text", "text": formalise_system(),
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": _formalise_user(inp)}],
        )

    def call(instrument: str, model: str, inp: Mapping[str, Json]) -> tuple[Json, Cost]:
        if instrument == PROPOSE_ANSWERS:
            messages = [sample(model, inp) for _ in range(inp["k"])]
            output: Json = [_first_line(m) for m in messages]
        elif instrument == FORMALISE_GOLD:
            messages = [formalise(model, inp)]
            output = _expression(messages[0])
        else:
            raise ValueError(f"anthropic backend has no instrument {instrument!r}")
        tokens_in = sum(_input_tokens(m) for m in messages)
        tokens_out = sum(m.usage.output_tokens for m in messages)
        cost = {
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "cache_read_tokens": sum(m.usage.cache_read_input_tokens or 0 for m in messages),
            "usd": sum(_message_usd(model, m) for m in messages)
            if model in SETTINGS["prices_usd"] else None,
            "refusals": sum(m.stop_reason == "refusal" for m in messages),
        }
        return output, cost

    return call


def _with_retries(f: Any, transient: Any, *args: Any) -> Any:
    """Call f; on an error `transient(e)` accepts, sleep through the table's
    delays and try again. Any other error, or the last try's, is raised."""
    for delay in SETTINGS["ollama"]["retry_delays_seconds"]:
        try:
            return f(*args)
        except Exception as e:
            if not transient(e):
                raise
            time.sleep(delay)
    return f(*args)


def ollama_backend() -> Instrument:
    """Ollama cloud (ollama.com). Needs the `llm` extra and OLLAMA_API_KEY.
    Sends no sampling options, so samples use the model's defaults; `effort`
    has no Ollama equivalent and is not sent."""
    import os

    import httpx
    from ollama import Client, ResponseError  # optional dependency; imported only when used

    retry_status = frozenset(SETTINGS["ollama"]["retry_status"])

    def transient(e: Exception) -> bool:
        if isinstance(e, ResponseError):
            return e.status_code in retry_status
        return isinstance(e, ConnectionError | httpx.TransportError)

    client = Client(
        host=SETTINGS["ollama"]["host"],
        timeout=SETTINGS["ollama"]["timeout_seconds"],
        headers={"Authorization": "Bearer " + os.environ["OLLAMA_API_KEY"]},
    )

    def sample(model: str, inp: Mapping[str, Json]) -> Any:
        prompt = PROMPTS[inp["prompt"]].format(**inp)
        return client.chat(model=model, messages=[{"role": "user", "content": prompt}])

    def call(instrument: str, model: str, inp: Mapping[str, Json]) -> tuple[Json, Cost]:
        if instrument != PROPOSE_ANSWERS:
            raise ValueError(f"ollama backend has no instrument {instrument!r}")
        if inp.get("effort") is not None:
            # The log must not claim a parameter that was not sent (QUESTIONS.md
            # brief 000 item 7): pass effort=None in the input before using Ollama.
            raise ValueError("ollama sends no effort; the logged input must say effort: null")
        responses = [_with_retries(sample, transient, model, inp) for _ in range(inp["k"])]
        tokens_in = sum(r.prompt_eval_count or 0 for r in responses)
        tokens_out = sum(r.eval_count or 0 for r in responses)
        cost = {
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "usd": usd(model, tokens_in, tokens_out),
        }
        lines = ((r.message.content or "").splitlines() for r in responses)
        return [next((ln.strip() for ln in ls if ln.strip()), "") for ls in lines], cost

    return call


def formalise_gold(
    clue: str,
    answer: str,
    definition: str,
    wordplay: str,
    model: str,
    *,
    tokens: tuple[str, ...],
    previous: tuple[dict[str, str], ...] = (),
    backend: Instrument,
) -> str:
    """DSL source for one gold explanation. `previous` holds earlier rejected
    attempts ({src, rule, hint}) so a retry sees the verifier's hint."""
    inp = {
        "clue": clue,
        "tokens": list(tokens),
        "answer": answer,
        "definition": definition,
        "wordplay": wordplay,
        "previous": list(previous),
        **SETTINGS[FORMALISE_GOLD],
    }
    output, _ = backend(FORMALISE_GOLD, model, inp)
    return str(output)


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
