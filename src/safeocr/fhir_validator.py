from __future__ import annotations

import hashlib
import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

OFFICIAL_VALIDATOR_VERSION = "6.10.4"
OFFICIAL_VALIDATOR_SHA256 = "1106b9d58f9e363e47bea7c4fc065841e5fc91fe9d062775c3bfdd212bd653cc"
OFFICIAL_FHIR_VERSION = "4.0.1"

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_SUMMARY_RE = re.compile(
    r"(\d+)\s+errors?,\s+(\d+)\s+warnings?,\s+(\d+)\s+notes?",
    flags=re.IGNORECASE,
)
_VERSION_RE = re.compile(r"FHIR Validation tool Version\s+([^\s]+)")


class FhirValidationError(RuntimeError):
    """Raised when the pinned FHIR validator cannot prove a bundle error-free."""


@dataclass(frozen=True, slots=True)
class FhirValidatorConfig:
    """Pinned local validator configuration."""

    java_executable: str
    validator_jar: Path
    expected_jar_sha256: str
    fhir_version: str = "4.0.1"
    timeout_seconds: float = 120.0

    def __post_init__(self) -> None:
        if not self.java_executable.strip():
            raise ValueError("java_executable must be non-empty")
        if not _SHA256_RE.fullmatch(self.expected_jar_sha256):
            raise ValueError("expected_jar_sha256 must be 64 hexadecimal characters")
        if self.fhir_version != "4.0.1":
            raise ValueError("SafeOCR v0.1 validator supports FHIR R4 4.0.1 only")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        object.__setattr__(
            self,
            "expected_jar_sha256",
            self.expected_jar_sha256.lower(),
        )


@dataclass(frozen=True, slots=True)
class FhirValidationResult:
    """Evidence returned by a successful official-validator run."""

    validator_version: str
    fhir_version: str
    jar_sha256: str
    error_count: int
    warning_count: int
    note_count: int
    stdout: str
    stderr: str


class _CompletedLike(Protocol):
    returncode: int
    stdout: str
    stderr: str


class _Runner(Protocol):
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
    ) -> _CompletedLike: ...


def _subprocess_runner(
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
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        stdout=stdout,
        stderr=stderr,
        timeout=timeout,
        check=check,
        shell=shell,
        text=text,
        encoding=encoding,
        errors=errors,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_summary(output: str) -> tuple[int, int, int]:
    matches = _SUMMARY_RE.findall(output)
    if not matches:
        raise FhirValidationError(
            "FHIR validator output did not contain an errors/warnings/notes summary"
        )
    errors, warnings, notes = matches[-1]
    return int(errors), int(warnings), int(notes)


def _parse_validator_version(output: str) -> str:
    match = _VERSION_RE.search(output)
    if match is None:
        raise FhirValidationError("FHIR validator output did not identify its version")
    return match.group(1)


def validate_fhir_r4_file(
    bundle_path: Path,
    config: FhirValidatorConfig,
    *,
    runner: _Runner = _subprocess_runner,
) -> FhirValidationResult:
    """Validate one bundle with the pinned HL7-maintained R4 CLI."""

    if not bundle_path.is_file():
        raise FhirValidationError(f"FHIR bundle does not exist: {bundle_path}")
    if not config.validator_jar.is_file():
        raise FhirValidationError(
            f"FHIR validator JAR does not exist: {config.validator_jar}"
        )

    actual_jar_sha256 = _sha256_file(config.validator_jar)
    if actual_jar_sha256 != config.expected_jar_sha256:
        raise FhirValidationError(
            "FHIR validator JAR checksum mismatch; refusing Java execution"
        )

    args = [
        config.java_executable,
        "-Dfile.encoding=UTF-8",
        "-jar",
        str(config.validator_jar),
        str(bundle_path),
        "-version",
        config.fhir_version,
        "-tx",
        "n/a",
    ]
    try:
        completed = runner(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=config.timeout_seconds,
            check=False,
            shell=False,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        raise FhirValidationError("FHIR validator execution failed") from exc

    combined_output = "\n".join(
        part for part in (completed.stdout, completed.stderr) if part
    )
    error_count, warning_count, note_count = _parse_summary(combined_output)
    validator_version = _parse_validator_version(combined_output)

    if completed.returncode != 0:
        raise FhirValidationError(
            "FHIR validator returned non-zero exit status "
            f"{completed.returncode}: {error_count} errors"
        )
    if error_count != 0:
        raise FhirValidationError(
            f"FHIR validator reported {error_count} error(s); export is blocked"
        )

    return FhirValidationResult(
        validator_version=validator_version,
        fhir_version=config.fhir_version,
        jar_sha256=actual_jar_sha256,
        error_count=error_count,
        warning_count=warning_count,
        note_count=note_count,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
