# F7 — Static Evidence Report

Status: CLOSED
Depends on: F6 Evaluation closeout (`be9b772a0709131d5bd9630d0f9c6e0b97cf787b`)

## Objective

Produce a deterministic, local-only evidence report for SafeOCR critical fields without an interactive application framework or cloud service.

## Contract

1. Every displayed critical field must resolve to exact source evidence.
2. Every displayed field must include a source crop embedded in the static HTML.
3. The source page hash must match the bytes used to derive the crop.
4. The machine-readable report must retain the complete EvidenceRecord, source box, crop hash, policy version, decision state, failed gates, and explanation.
5. OCR text is untrusted display content and must be HTML-escaped.
6. The report must not display raw patient identifiers; linkage evidence remains HMAC-bound.
7. VERIFIED_AUTO, REVIEW_REQUIRED, and ABSTAINED explanations are deterministic and state-specific.
8. No JavaScript, remote asset, paid API, or network request is required to open the report.

## Deliverables

- `src/safeocr/report.py`: deterministic report/crop/HTML builder.
- `scripts/build_f7_report.py`: canonical local CLI builder.
- `tests/test_report.py`: report safety and determinism tests.
- `docs/evidence/F7_EVIDENCE_REPORT.json`: machine-readable canonical report.
- `docs/evidence/F7_EVIDENCE_REPORT.html`: self-contained static HTML report.

## Canonical v0.1 report source

The canonical F7 report is built from the already-qualified F4 runtime trace and a deterministic regeneration of its SafeOCR-LabGold source page.

The script must:
- read `docs/evidence/F4_RUNTIME_SMOKE.json`;
- regenerate only the named LabGold source from the frozen seed/template;
- require regenerated page SHA-256 equality with the F4 evidence;
- derive the displayed crop from the exact evidence span union;
- write deterministic JSON and HTML artifacts.

This does not rerun OCR, change policy, or reinterpret F6 results.

## Exit criteria

- focused report tests pass;
- full pytest suite passes;
- Ruff passes;
- Pyright strict passes;
- Graft graph check passes;
- Jev review evidence recorded;
- Alibaba Open Code Review delegated rules applied;
- canonical JSON report retains complete EvidenceRecord provenance;
- canonical HTML contains an embedded source crop and no remote resources;
- repeated canonical builds are byte-for-byte deterministic.
