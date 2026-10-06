# F7 Review Evidence

Date: 2026-10-06
Phase: F7 Static Evidence Report

## Deliverables

- `src/safeocr/report.py`
- `scripts/build_f7_report.py`
- `tests/test_report.py`
- `docs/evidence/F7_EVIDENCE_REPORT.json`
- `docs/evidence/F7_EVIDENCE_REPORT.html`

## Canonical evidence identity

The canonical report is regenerated from the already-qualified F4 runtime trace and the frozen SafeOCR-LabGold seed/template.

- report JSON SHA-256: `2e6933440e9b9e066dfd970ae8e9341ab3831ebc59e471b464b9c5c1d89e21f0`
- report HTML SHA-256: `8e52f47e28da7dd1c0bc60a41e996628a00386f5bec9fdb90c0bcc66e7a843c1`
- repeated canonical builds produced the same hashes
- source page SHA-256: `f6acec4c54e4fb4ce6bcd4a0c7ee76b9fa748015bd7c21621d13684b54110d16`

The report builder refuses source-page bytes whose SHA-256 does not match the evidence trace.

## Safety and provenance

- OCR text is HTML-escaped before rendering.
- Source crops are embedded as local base64 PNG data URIs.
- The generated HTML has no http/https remote resource reference.
- The JSON report retains the complete EvidenceRecord, failed gates, source box, page hash, crop hash, decision state, policy version, and deterministic explanation.
- Raw patient identifiers are not rendered.
- Patient linkage remains represented through the qualified evidence record/HMAC binding rather than plaintext identity.

## State explanations

- VERIFIED_AUTO: all required gates passed.
- REVIEW_REQUIRED: failed review gates are enumerated.
- ABSTAINED: failed abstention gates are enumerated.

Tests cover all three explanation states even though the canonical runtime artifact displays the qualified verified control.

## Mechanical qualification

- focused F7 tests: 9 passed
- full suite: 184 passed, 4 runtime tests skipped by default
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings, 0 informations
- pip check: PASS
- git diff --check: PASS
- Graft: 506 nodes / 1620 edges, graph check OK

## Review tools

Jev report-quality score: 3.42 / 4, with 48% excellent and 47% strong probability.

Alibaba Open Code Review delegated correctness/security rules were applied to the report implementation, canonical builder, tests, specification, and JSON evidence surface. No blocking host-agent finding remained. A direct LLM-backed OCR review is not claimed because the configured Anthropic OCR provider has no API key.

## Exit

F7 is ready for commit and exact-head qualification.
