from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import cast

import safeocr

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
_WORKFLOWS = (
    ".github/workflows/ci.yml",
    ".github/workflows/codeql.yml",
)
_SHA_USES_RE = re.compile(r"^\s*uses:\s*[^@\s]+@([0-9a-f]{40})\s*$", re.MULTILINE)


def _pyproject() -> dict[str, object]:
    return tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_release_version_and_package_name_are_frozen() -> None:
    project_raw = _pyproject()["project"]
    assert isinstance(project_raw, dict)
    project = cast(dict[str, object], project_raw)
    assert project["name"] == "safeocr-health"
    assert project["version"] == "0.1.0"
    assert safeocr.__version__ == "0.1.0"


def test_project_license_is_apache_2() -> None:
    license_text = (_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text
    assert "Version 2.0, January 2004" in license_text

    project_raw = _pyproject()["project"]
    assert isinstance(project_raw, dict)
    project = cast(dict[str, object], project_raw)
    license_raw = project["license"]
    assert isinstance(license_raw, dict)
    license_value = cast(dict[str, object], license_raw)
    assert license_value["file"] == "LICENSE"


def test_release_documents_exist() -> None:
    for relative in ("NOTICE", "CHANGELOG.md", "CITATION.cff", "docs/RELEASE_NOTES_v0.1.0.md"):
        assert (_ROOT / relative).is_file(), relative


def test_required_canonical_evidence_is_present() -> None:
    missing = [relative for relative in _REQUIRED_EVIDENCE if not (_ROOT / relative).is_file()]
    assert missing == []


def test_readme_preserves_research_only_safety_boundary() -> None:
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    assert "not a medical device" in readme
    assert "must not be used to make diagnosis or treatment decisions" in readme
    assert "does not establish SafeOCR superiority" in readme
    assert "Zero observed errors is not proof of zero risk" in readme


def test_release_notes_preserve_conservative_f6_interpretation() -> None:
    notes = (_ROOT / "docs/RELEASE_NOTES_v0.1.0.md").read_text(encoding="utf-8")
    assert "does not establish SafeOCR superiority" in notes
    assert "Zero observed errors is not zero risk" in notes
    assert "not a medical device" in notes


def test_citation_metadata_is_v010_apache2() -> None:
    citation = (_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert 'version: "0.1.0"' in citation
    assert 'license: "Apache-2.0"' in citation
    assert "Abdulaziz" in citation
    assert "Alshehri" in citation


def test_ci_matrix_covers_python_311_and_312() -> None:
    ci = (_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert '"3.11"' in ci
    assert '"3.12"' in ci
    for command in ("ruff check .", "pyright", "python -m pytest -q", "python -m build"):
        assert command in ci


def test_all_github_actions_are_pinned_to_full_commit_shas() -> None:
    for relative in _WORKFLOWS:
        text = (_ROOT / relative).read_text(encoding="utf-8")
        uses_lines = [line for line in text.splitlines() if line.strip().startswith("uses:")]
        assert uses_lines, relative
        for line in uses_lines:
            assert _SHA_USES_RE.match(line), f"mutable or invalid action ref: {line}"


def test_workflows_use_least_privilege_permissions() -> None:
    ci = (_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    codeql = (_ROOT / ".github/workflows/codeql.yml").read_text(encoding="utf-8")
    assert "contents: read" in ci
    assert "contents: read" in codeql
    assert "security-events: write" in codeql
