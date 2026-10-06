# SafeOCR State

## In flight

F4 Evidence Verification is closed locally. F5 FHIR R4 export gate is next.

## Canonical local foundation

- architecture commit: 6f11ccb
- F1 foundation commit: 1d05ba4
- F2 LabGold commit: a2c626a
- F3 OCR adapters commit: 3aba8f6
- active branch: feat/f4-evidence-verification
- remote repository is currently read-only from the connected credentials

## F4 runtime

- PaddleOCR 3.7.0
- ONNX Runtime 1.23.2 CPU
- Tesseract 5.4.0.20240606
- ucumvert 0.3.2
- runtime evidence: docs/evidence/F4_RUNTIME_SMOKE.json
- review evidence: docs/reviews/F4_REVIEW.md

## Current objective

Specify F5 as a narrow FHIR R4 export gate that exports only VERIFIED_AUTO evidence, preserves source-document provenance, and blocks export on validation failure. F5 must not weaken F4 verification or invent missing clinical content.
