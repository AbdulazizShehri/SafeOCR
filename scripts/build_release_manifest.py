from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]

_REQUIRED_EVIDENCE = (
    "docs/evidence/F3_RUNTIME_SMOKE.json",
    "docs/evidence/F4_RUNTIME_SMOKE.json",
    "docs/evidence/F5_RUNTIME_SMOKE.json",
    "docs/evidence/F6_FINAL_ATTEMPT_1_FAILURE.json",
    "docs/evidence/F6_FINAL_EVALUATION.json",
    "docs/evidence/F6_CLINOCR_METADATA.json",
    "docs/evidence/F6_CLOSEOUT.json",
    "docs/evidence/F6_RISK_COVERAGE.csv",
    "docs/evidence/F7_EVIDENCE_REPORT.json",
    "docs/evidence/F7_EVIDENCE_REPORT.html",
)

_RELEASE_INPUTS = (
    "LICENSE",
    "NOTICE",
    "CHANGELOG.md",
    "CITATION.cff",
    "README.md",
    "pyproject.toml",
    "docs/RELEASE_NOTES_v0.1.0.md",
    ".github/workflows/ci.yml",
    ".github/workflows/codeql.yml",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    return completed.stdout.strip()


def _clean_head() -> tuple[str, str]:
    status = _git("status", "--porcelain")
    if status:
        raise RuntimeError("release manifest requires a clean exact-head working tree")
    return _git("rev-parse", "HEAD"), _git("rev-parse", "HEAD^{tree}")


def _hash_set(paths: tuple[str, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in paths:
        path = _ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        result[relative] = _sha256(path)
    return result


def build_manifest(*, include_git: bool = True) -> dict[str, Any]:
    head: str | None = None
    tree: str | None = None
    if include_git:
        head, tree = _clean_head()

    return {
        "schema_version": 1,
        "release": "v0.1.0",
        "package": "safeocr-health",
        "version": "0.1.0",
        "license": "Apache-2.0",
        "qualified_source_head": head,
        "qualified_source_tree": tree,
        "evidence_sha256": _hash_set(_REQUIRED_EVIDENCE),
        "release_input_sha256": _hash_set(_RELEASE_INPUTS),
        "safety_boundary": {
            "research_only": True,
            "medical_device": False,
            "diagnosis_or_treatment_use_allowed": False,
        },
        "known_limitations": [
            "LabGold does not establish SafeOCR superiority over raw primary OCR.",
            "Zero observed unsafe accepts is not proof of zero risk.",
            (
                "ClinOCR-Bench v1.0 integration is metadata-locked and no-tuning; "
                "unsupported structured critical-field claims are withheld."
            ),
            "FHIR mapping error rate is not estimable from the frozen F6 final artifact.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the SafeOCR v0.1 release manifest")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/evidence/F8_RELEASE_MANIFEST.json"),
    )
    args = parser.parse_args()

    payload = build_manifest(include_git=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    output = args.output if args.output.is_absolute() else _ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")


if __name__ == "__main__":
    main()
