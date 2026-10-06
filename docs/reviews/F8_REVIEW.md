# F8 Review Evidence

Date: 2026-10-06
Phase: F8 v0.1 Release

## Release-candidate implementation

The release branch freezes SafeOCR as `safeocr-health==0.1.0` under Apache-2.0 while preserving the research-only safety boundary and all declared F6 limitations.

Release surfaces added or updated:
- Apache-2.0 `LICENSE`, `NOTICE`, changelog, citation metadata, and v0.1 release notes;
- package version and metadata in `pyproject.toml` and `safeocr.__version__`;
- Python 3.11/3.12 CI and CodeQL workflows with third-party actions pinned to full commit SHAs;
- release-contract regression tests;
- deterministic release-manifest builder that requires a clean exact-head tree.

## Mechanical qualification

Pre-commit release-candidate gates:
- full default pytest: 194 passed / 4 runtime tests skipped by design;
- release-contract tests: 10 passed;
- Ruff: PASS;
- Pyright strict: 0 errors / 0 warnings / 0 informations;
- pip check: PASS;
- Graft: 518 nodes / 1638 edges; graph check OK;
- git diff --check: PASS;
- sdist build: PASS;
- wheel build: PASS;
- isolated wheel installation: PASS;
- isolated import reports `safeocr.__version__ == "0.1.0"`.

Runtime-heavy OCR/FHIR tests are not silently rerun as part of default release CI. Their canonical evidence remains frozen and hashable.

## Review tools

Jev release-contract advisory score: 2.80 / 4 expected-level score, with low confidence (0.26). It is treated as advisory uncertainty rather than a release certificate.

Alibaba Open Code Review delegate preview/rules were applied to the reviewable F8 Python/YAML/project surfaces. Direct LLM-backed `ocr review` is not claimed because the locally configured Anthropic provider has no API key. No fabricated review result is recorded.

pstack TDD/blast-radius workflow remains the engineering discipline for the repository; the executable release-contract tests were written to freeze the release boundary.

## Safety and claim discipline

The release keeps these statements explicit:
- SafeOCR is research software and not a medical device;
- it must not be used for diagnosis or treatment decisions;
- LabGold does not establish SafeOCR superiority over raw primary OCR;
- zero observed errors is not proof of zero risk;
- ClinOCR-Bench transcript truth is not relabeled as structured clinical-field evidence;
- FHIR validator conformance is not relabeled as an F6 FHIR mapping error-rate estimate.

## Next gate

Commit the F8 implementation, requalify that exact head, generate `docs/evidence/F8_RELEASE_MANIFEST.json` from the clean qualified source head, commit release closeout evidence, then perform a normal merge into `main` and requalify the merged head before tag readiness.
