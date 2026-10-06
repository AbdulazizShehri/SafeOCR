from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.runtime
def test_f4_real_verification_runtime_smoke() -> None:
    if os.environ.get("SAFEOCR_RUN_VERIFY_SMOKE") != "1":
        pytest.skip("set SAFEOCR_RUN_VERIFY_SMOKE=1 to run the F4 runtime smoke")

    output = Path(".jev") / "f4-runtime-pytest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)

    env = os.environ.copy()
    env["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/smoke_verification_runtime.py",
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
    assert payload["clean"]["decision"] == "VERIFIED_AUTO"
    assert payload["clean"]["signals"]["runtime_healthy"] is True
    assert payload["clean"]["signals"]["unit_valid"] is True
    assert payload["disagreement_control"]["decision"] != "VERIFIED_AUTO"
    assert "independent_agreement" in payload["disagreement_control"]["failed_gates"]
