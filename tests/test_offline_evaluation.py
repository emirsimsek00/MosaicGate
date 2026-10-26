"""The frozen suites run end to end through the real local MCP boundary."""

import json
from pathlib import Path

import pytest

from mosaicgate.evaluation import Split, aggregate, evaluate, load_cases
from mosaicgate.reporting import create_report


@pytest.mark.parametrize("split", ["dev", "holdout"])
async def test_frozen_suite_and_saved_report_are_reproducible(split: Split, tmp_path: Path) -> None:
    assert len(load_cases(split)) == 24
    trace_path = tmp_path / "runs.jsonl"
    first = await evaluate(split, "scripted", trace_path, max_sessions=2)
    assert first["new_sessions"] == 2
    assert first["missing_sessions"] == 70
    partial = aggregate(split, trace_path)
    partial_modes = partial["modes"]
    assert isinstance(partial_modes, dict)
    assert sum(partial_modes[mode]["missing_sessions"] for mode in partial_modes) == 70
    partial_dir = tmp_path / "partial-report"
    assert create_report(trace_path, partial_dir)["completed_sessions"] == 2
    assert (partial_dir / "index.html").read_text().count("Missing completed run") == 70
    resumed = await evaluate(split, "scripted", trace_path)
    assert resumed["new_sessions"] == 70
    assert resumed["completed_sessions"] == 72
    assert resumed["api_requests_total"] == 0
    assert (await evaluate(split, "scripted", trace_path))["new_sessions"] == 0

    summary = aggregate(split, trace_path)
    modes = summary["modes"]
    assert isinstance(modes, dict)
    for mode in ("baseline", "inspect", "full"):
        assert modes[mode]["completed_sessions"] == 24
        assert modes[mode]["missing_sessions"] == 0
        assert modes[mode]["benign_task_completion"]["denominator"] == 12
    assert modes["full"]["unauthorized_simulated_completions"]["numerator"] == 0
    assert modes["full"]["ocr_extraction_success"]["denominator"] == 12

    output = tmp_path / "report"
    result = create_report(trace_path, output)
    assert result["completed_sessions"] == 72
    first_html = (output / "index.html").read_bytes()
    assert b"Every frozen case" in first_html
    assert b"<script>" not in first_html
    assert len(json.loads((output / "cases.json").read_text())) == 24
    assert create_report(trace_path, output) == result
    assert (output / "index.html").read_bytes() == first_html
