"""Corpus integrity and pre-render split leakage checks."""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN_HOLDOUT_MANIFEST_SHA256 = "73da91e336c5f5523f64de65fa6e399a89d743d85948e1473fb05239f0bcf7c8"


def test_preassigned_split_and_frozen_holdout_sources() -> None:
    plan = json.loads((ROOT / "fixtures" / "case_plan.json").read_text())
    assert plan["split_assigned_before_rendering"] is True
    assert len(plan["cases"]) == 48
    assert len({case["family"] for case in plan["cases"]}) == 48
    assert len({case["id"] for case in plan["cases"]}) == 48
    counts = Counter((case["split"], case["modality"], case["label"]) for case in plan["cases"])
    assert len(counts) == 8 and set(counts.values()) == {6}
    assert {case["image_template"] for case in plan["cases"] if case["split"] == "dev"} == {
        "memo_card"
    }
    assert {case["image_template"] for case in plan["cases"] if case["split"] == "holdout"} == {
        "grid_sheet"
    }

    holdout = ROOT / "fixtures" / "holdout_manifest.json"
    assert hashlib.sha256(holdout.read_bytes()).hexdigest() == FROZEN_HOLDOUT_MANIFEST_SHA256
    for split in ("dev", "holdout"):
        manifest = json.loads((ROOT / "fixtures" / f"{split}_manifest.json").read_text())
        assert len(manifest["cases"]) == 24
        for case in manifest["cases"]:
            path = ROOT / case["source_file"]
            assert path.is_file()
            assert path.resolve().is_relative_to((ROOT / "fixtures" / split).resolve())
            assert hashlib.sha256(path.read_bytes()).hexdigest() == case["source_file_sha256"]
            assert case["legitimate_user_goal"] == plan["shared_goal"]
            if case["modality"] == "image":
                assert path.suffix == ".png"
                assert case["expected_ocr_text"]
            else:
                assert path.suffix == ".txt"
                assert case["expected_ocr_text"] is None
            text = path.read_text() if path.suffix == ".txt" else str(case["expected_ocr_text"])
            for address in re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]+", text):
                assert address.endswith(".test")
