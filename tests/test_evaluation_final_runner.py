from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RUNNER = _REPO_ROOT / "scripts" / "run_labgold_final.py"


def test_final_runner_exposes_no_partial_case_limit_or_calibration_role() -> None:
    source = _RUNNER.read_text(encoding="utf-8")
    assert "--max-cases" not in source
    assert "EvaluationRole.CALIBRATION" not in source
    assert "if item.role is EvaluationRole.EVALUATION" in source
    assert '"run_kind": "primary_v0_1_final_evaluation"' in source


def test_final_runner_help_is_non_executing_and_has_only_runtime_options() -> None:
    completed = subprocess.run(
        [sys.executable, str(_RUNNER), "--help"],
        cwd=_REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        shell=False,
        timeout=10,
    )
    assert completed.returncode == 0
    assert "--max-cases" not in completed.stdout
    assert "--tesseract" in completed.stdout
    assert "--output" in completed.stdout


def test_final_runner_refuses_to_overwrite_existing_primary_evidence() -> None:
    output = _REPO_ROOT / ".jev" / "final-runner-existing.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("{}\n", encoding="utf-8")
    try:
        completed = subprocess.run(
            [sys.executable, str(_RUNNER), "--output", str(output)],
            cwd=_REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            shell=False,
            timeout=10,
        )
    finally:
        output.unlink(missing_ok=True)
    assert completed.returncode != 0
    assert "final evaluation evidence already exists; refusing rerun" in completed.stderr
