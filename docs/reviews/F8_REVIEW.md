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


## Exact-head release-candidate qualification

Implementation commit: `76139294d1b5a9277d1fd51e7e1445b33e888f68`

The implementation commit was requalified from a clean tree:
- full default pytest: 194 passed / 4 skipped;
- Ruff: PASS;
- Pyright strict: 0 errors / 0 warnings / 0 informations;
- pip check: PASS;
- Graft: 525 nodes / 1656 edges; graph check OK;
- sdist and wheel build: PASS;
- isolated wheel installation: PASS;
- isolated import version: `0.1.0`.

The deterministic release manifest was then generated from that clean exact head. `docs/evidence/F8_RELEASE_MANIFEST.json` records:
- qualified source head `76139294d1b5a9277d1fd51e7e1445b33e888f68`;
- qualified source tree `177b7c7a1eff1af89a3e6c9faa392efda90c8aca`;
- SHA-256 values for the canonical F3-F7 evidence set;
- SHA-256 values for release metadata, license/notices, README, and pinned workflows;
- the research-only safety boundary and declared limitations.

This manifest intentionally identifies the qualified source commit rather than attempting an impossible self-hash of the commit that later adds the manifest itself.


## Merged-main qualification and publication blockers

The qualified release branch was integrated into `main` with a normal merge commit:

- merged main head: `0ec635856ebf62e3b16c3a066f23123b0b4cd399`;
- no squash, rebase, force-push, or history rewrite.

That exact merged head was requalified:
- full default pytest: 194 passed / 4 skipped;
- Ruff: PASS;
- Pyright strict: 0 errors / 0 warnings / 0 informations;
- pip check: PASS;
- Graft: 525 nodes / 1656 edges; graph check OK;
- wheel and sdist build: PASS;
- isolated wheel installation: PASS;
- isolated import version: `0.1.0`.

Two external release actions remain intentionally blocked rather than weakened:

1. Local GitHub CLI authentication is currently active as `IamShehri`, which has no collaborator permission on `AbdulazizShehri/SafeOCR`. The owner account is connected to ChatGPT, but that connector credential is not exposed to the local Git credential helper. Canonical local history therefore has not been replaced by connector-generated synthetic commits.
2. No SafeOCR-approved Git signing key is configured locally. The project will not create an unsigned `v0.1.0` tag merely to bypass the signed-tag requirement.

These are credential/signing blockers only. The local release code and package have completed their exact-head mechanical qualification.
