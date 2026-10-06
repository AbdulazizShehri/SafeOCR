from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.runtime
def test_f3_real_ocr_runtime_smoke() -> None:
    if os.environ.get("SAFEOCR_RUN_OCR_SMOKE") != "1":
        pytest.skip("set SAFEOCR_RUN_OCR_SMOKE=1 to run installed OCR runtimes")

    output = Path(".jev") / "f3-runtime-pytest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)

    env = os.environ.copy()
    env["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/smoke_ocr_runtime.py",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
        shell=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["packages"]["paddleocr"] == "3.7.0"
    assert payload["packages"]["onnxruntime"] == "1.23.2"
    assert payload["results"]["paddle_normalized_span_count"] > 0
    assert payload["results"]["all_paddle_spans_in_page"] is True
    assert payload["results"]["paddle_truth_value_detected"] is True
    assert payload["results"]["tesseract_truth_value_match"] is True
