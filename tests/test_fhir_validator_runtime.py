from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.runtime
def test_f5_official_fhir_validator_runtime_smoke() -> None:
    if os.environ.get("SAFEOCR_RUN_FHIR_SMOKE") != "1":
        pytest.skip("set SAFEOCR_RUN_FHIR_SMOKE=1 to run the official FHIR validator")

    output = Path(".jev") / "f5-fhir-runtime-pytest.json"
    output.unlink(missing_ok=True)
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/smoke_fhir_runtime.py",
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
    assert payload["fhir_version"] == "4.0.1"
    assert payload["validator"]["errors"] == 0
    assert payload["valid_bundle"]["passed"] is True
    assert payload["invalid_control"]["rejected"] is True
