"""Brief 010 item 1: Wikipedia's entries in their own CC BY-SA file, merged at
load time; the merged table equals brief 009's single table."""

import json
import subprocess

import pytest

from ximenes.data import LEXICON, abbreviation_origins


def test_share_alike_stays_in_one_file() -> None:
    main = json.loads((LEXICON / "abbreviations.json").read_text())
    wiki = json.loads((LEXICON / "abbreviations.wikipedia.json").read_text())
    assert "CC BY-SA 4.0" in wiki["license"]
    assert not any("wikipedia" in o for d in main["_origin"].values() for o in d.values())
    assert all("wikipedia" in o for d in wiki["_origin"].values() for o in d.values())


def test_merged_table_equals_brief_009s() -> None:
    old = subprocess.run(["git", "show", "b1e76e3:data/lexicon/abbreviations.json"],
                         capture_output=True, text=True, check=False)
    if old.returncode:
        pytest.skip("git history not available")
    assert abbreviation_origins() == json.loads(old.stdout)["_origin"]
