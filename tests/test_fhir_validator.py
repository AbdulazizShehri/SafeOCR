from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

from safeocr.fhir_validator import (
    FhirValidationError,
    FhirValidatorConfig,
    validate_fhir_r4_file,
)


@dataclass
class _Completed:
    returncode: int
    stdout: str
    stderr: str


class _Runner:
    def __init__(
        self,
        completed: _Completed | None = None,
        *,
        error: BaseException | None = None,
    ) -> None:
        self.completed = completed
        self.error = error
        self.calls: list[dict[str, object]] = []

    def __call__(
        self,
        args: Sequence[str],
        *,
        stdout: int,
        stderr: int,
        timeout: float,
        check: bool,
        shell: bool,
        text: bool,
        encoding: str,
        errors: str,
    ) -> _Completed:
        self.calls.append(
            {
                "args": list(args),
                "stdout": stdout,
                "stderr": stderr,
                "timeout": timeout,
                "check": check,
                "shell": shell,
                "text": text,
                "encoding": encoding,
                "errors": errors,
            }
        )
        if self.error is not None:
            raise self.error
        assert self.completed is not None
        return self.completed


def _files(case: str) -> tuple[Path, Path, str]:
    workspace = Path(".jev") / "test-fhir-validator" / case
    workspace.mkdir(parents=True, exist_ok=True)
    jar = workspace / "validator_cli.jar"
    jar.write_bytes(b"pinned-validator")
    bundle = workspace / "bundle.json"
    bundle.write_text('{"resourceType":"Bundle","type":"collection"}', encoding="utf-8")
    digest = hashlib.sha256(jar.read_bytes()).hexdigest()
    return jar, bundle, digest


def _config(jar: Path, digest: str) -> FhirValidatorConfig:
    return FhirValidatorConfig(
        java_executable="java",
        validator_jar=jar,
        expected_jar_sha256=digest,
        fhir_version="4.0.1",
        timeout_seconds=30.0,
    )


def test_checksum_mismatch_blocks_before_java_execution() -> None:
    jar, bundle, _ = _files("checksum")
    runner = _Runner(_Completed(0, "", ""))

    with pytest.raises(FhirValidationError):
        validate_fhir_r4_file(
            bundle,
            _config(jar, "0" * 64),
            runner=runner,
        )

    assert runner.calls == []


def test_validator_invocation_is_pinned_and_shell_disabled() -> None:
    jar, bundle, digest = _files("invocation")
    runner = _Runner(
        _Completed(
            0,
            "FHIR Validation tool Version 6.10.4\n"
            "* SUCCESS: 0 errors, 2 warnings, 1 notes\n",
            "",
        )
    )

    result = validate_fhir_r4_file(bundle, _config(jar, digest), runner=runner)

    call = runner.calls[0]
    assert call["args"] == [
        "java",
        "-Dfile.encoding=UTF-8",
        "-jar",
        str(jar),
        str(bundle),
        "-version",
        "4.0.1",
        "-tx",
        "n/a",
    ]
    assert call["shell"] is False
    assert call["check"] is False
    assert call["timeout"] == 30.0
    assert result.error_count == 0
    assert result.warning_count == 2
    assert result.note_count == 1
    assert result.validator_version == "6.10.4"
    assert result.jar_sha256 == digest


def test_validator_errors_block_even_with_zero_return_code() -> None:
    jar, bundle, digest = _files("errors-zero-exit")
    runner = _Runner(
        _Completed(
            0,
            "FHIR Validation tool Version 6.10.4\n"
            "*FAILURE*: 1 errors, 0 warnings, 0 notes\n",
            "",
        )
    )

    with pytest.raises(FhirValidationError):
        validate_fhir_r4_file(bundle, _config(jar, digest), runner=runner)


def test_nonzero_validator_exit_blocks() -> None:
    jar, bundle, digest = _files("nonzero-exit")
    runner = _Runner(
        _Completed(
            1,
            "FHIR Validation tool Version 6.10.4\n"
            "*FAILURE*: 1 errors, 0 warnings, 0 notes\n",
            "failure",
        )
    )

    with pytest.raises(FhirValidationError):
        validate_fhir_r4_file(bundle, _config(jar, digest), runner=runner)


def test_missing_validation_summary_fails_closed() -> None:
    jar, bundle, digest = _files("missing-summary")
    runner = _Runner(_Completed(0, "FHIR Validation tool Version 6.10.4\n", ""))

    with pytest.raises(FhirValidationError):
        validate_fhir_r4_file(bundle, _config(jar, digest), runner=runner)


def test_timeout_is_wrapped_as_validation_failure() -> None:
    jar, bundle, digest = _files("timeout")
    runner = _Runner(
        error=subprocess.TimeoutExpired(cmd=["java"], timeout=30.0)
    )

    with pytest.raises(FhirValidationError):
        validate_fhir_r4_file(bundle, _config(jar, digest), runner=runner)


def test_missing_bundle_or_jar_fails_closed() -> None:
    jar, bundle, digest = _files("missing-files")

    with pytest.raises(FhirValidationError):
        validate_fhir_r4_file(
            bundle.parent / "missing-bundle.json",
            _config(jar, digest),
        )

    with pytest.raises(FhirValidationError):
        validate_fhir_r4_file(
            bundle,
            _config(jar.parent / "missing-validator.jar", digest),
        )
