"""Brief 001: hand-written gold parses in tests/fixtures/gold-dsl.jsonl verify
with their expected status. Val entries name clue tokens by position (#i) so
no dataset text is committed; they are filled in from local data."""

import json
import pathlib
import re

import pytest

from ximenes.clue import Clue, split_clue
from ximenes.data import WORDPLAY
from ximenes.prompts import FORMALISE_EXAMPLES
from ximenes.verdict import Reject
from ximenes.verify import verify

ROWS = [json.loads(line) for line in
        (pathlib.Path(__file__).parent / "fixtures" / "gold-dsl.jsonl").read_text().splitlines()]
VAL = [r for r in ROWS if r["split"] == "val"]
HAVE_DATA = (WORDPLAY / "sample_teacow_val.jsonl").exists()


def status(v: object) -> str:
    if isinstance(v, Reject):
        return f"Reject:{v.first_broken_rule}"
    return f"{type(v).__name__}:{','.join(r.value for r in getattr(v, 'reasons', ()))}"


def test_fixture_examples_are_the_prompt_examples() -> None:
    examples = [(r["clue"], r["answer"], r["src"]) for r in ROWS if r["split"] == "example"]
    assert examples == list(FORMALISE_EXAMPLES)


def test_audit_has_thirty_classified_parses() -> None:
    assert len(VAL) == 30
    assert {r["audit"] for r in VAL} <= {"dsl_limit", "formaliser_miss", "verifier_bug"}
    args = [a for r in VAL for inner in re.findall(r"tok\(([^)]*)\)", r["src"])
            for a in re.findall(r"'([^']*)'", inner)]
    assert args and all(re.fullmatch(r"#\d+", a) for a in args)  # no clue words


@pytest.mark.skipif(not HAVE_DATA, reason="wordplay sample not downloaded (./setup.sh)")
@pytest.mark.parametrize("row", VAL, ids=[str(r["index"]) for r in VAL])
def test_gold_parse_has_expected_status(row: dict) -> None:
    from ximenes.data import load_wordplay
    from ximenes.eval import wordplay_clue

    ex = load_wordplay("val")[row["index"]]
    assert ex.answer == row["answer"]
    clue = wordplay_clue(ex)
    src = re.sub(r"'#(\d+)'", lambda m: repr(clue.tokens[int(m.group(1))].text), row["src"])
    assert status(verify(clue, ex.answer, src)) == row["expected"]
    # (Superseded by brief 002: with the new operators, a 001 "dsl_limit" entry
    # may now verify, so its expected status no longer has to name an unknown
    # operator. The 001 audit class is kept as recorded.)
    if row["audit"] != "dsl_limit":
        assert not row["expected"].startswith("Reject")


@pytest.mark.parametrize("raw,answer,src", FORMALISE_EXAMPLES)
def test_examples_accept(raw: str, answer: str, src: str) -> None:
    text, enum = split_clue(raw.replace("{", "").replace("}", ""))
    assert not isinstance(verify(Clue(text, enum), answer, src), Reject)
