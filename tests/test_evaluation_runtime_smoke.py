from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.runtime
def test_f6_calibration_runtime_smoke() -> None:
    if os.environ.get("SAFEOCR_RUN_EVAL_SMOKE") != "1":
        pytest.skip("set SAFEOCR_RUN_EVAL_SMOKE=1 to run the F6 calibration smoke")

    output = Path(".jev") / "f6-calibration-pytest.json"
    output.unlink(missing_ok=True)
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_labgold_calibration.py",
            "--max-cases",
            "2",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=240,
        shell=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["role"] == "calibration"
    assert payload["document_cases"] == 2
    assert payload["field_cases"] == 12
    assert payload["alignment_mode"] == "truth_geometry_scoring"
    assert payload["split_sha256"] == (
        "3aa0af90f3d41d5a0b636ded5d784119da81a193b81a907b7bb69a789cc816a5"
    )
    assert set(payload["methods"]) == {
        "primary_ocr",
        "tesseract_crop",
        "naive_agreement",
        "safeocr",
    }
