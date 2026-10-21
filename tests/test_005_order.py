"""Brief 005 (D7): the slot prior and the gain model were committed before
the first evaluation run; VOC refuses its own fit grids; score-at-budget in the
report replays from the log (local)."""

import json
import pathlib
import subprocess
from datetime import UTC, datetime

import pytest

from ximenes.voc import GAIN_MODEL, OTHER_PRIOR

REPORT = pathlib.Path("reports/005/policies.json")


def _first_commit(path: pathlib.Path) -> datetime | None:
    out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%cI", "--", str(path)],
                         capture_output=True, text=True, check=False).stdout.split()
    return datetime.fromisoformat(out[-1]).astimezone(UTC) if out else None


def _run_time(run_id: str) -> datetime:
    return datetime.strptime(run_id.split("-")[0], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)


@pytest.mark.skipif(not REPORT.exists(), reason="brief 005 report not written yet")
def test_tables_committed_before_first_evaluation_run() -> None:
    runs = json.loads(REPORT.read_text())["evaluation_runs"].values()
    first_eval = min(_run_time(r) for r in runs)
    for table in (OTHER_PRIOR, GAIN_MODEL):
        committed = _first_commit(table)
        assert committed is not None and committed < first_eval, table


def test_gain_model_names_its_fit_seed_not_the_evaluation_seed() -> None:
    from ximenes.voc import VOC

    if not GAIN_MODEL.exists():
        pytest.skip("gain model not fitted yet")
    m = json.loads(GAIN_MODEL.read_text())
    assert m["fit_seed"] == VOC["fit_seed"] != VOC["eval_seed"]
