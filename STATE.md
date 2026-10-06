# SafeOCR State

## In flight

F6 Evaluation is active. F6.1 deterministic evaluation contracts are qualified; F6.2 frozen LabGold split/baseline execution is next.

## Canonical local foundation

- architecture commit: 6f11ccb
- F1 foundation commit: 1d05ba4
- F2 LabGold commit: 2c626a
- F3 OCR adapters commit: 3aba8f6
- F4 evidence verification commit: 11da0c
- patient-binding prerequisite fix: c711a70
- F5 FHIR R4 gate commit: 448f024
- active branch: eat/f6-evaluation

## F5 closeout

- FHIR R4 4.0.1 only
- HL7 validator CLI 6.10.4
- validator JAR SHA-256: 1106b9d58f9e363e47bea7c4fc065841e5fc91fe9d062775c3bfdd212bd653cc
- canonical evidence: docs/evidence/F5_RUNTIME_SMOKE.json
- valid bundle: 0 errors, 7 documented warnings, 1 note
- deliberately invalid control: rejected with 2 errors
- default pytest at F5 close: 139 passed, 3 skipped
- explicit official-validator runtime pytest: 1 passed
- Jev and Alibaba delegated review: qualified

## F6.1 closeout

- deterministic evaluation metrics and role contracts implemented
- full pytest: 147 passed, 3 skipped
- Ruff / Pyright / pip check / git diff --check: PASS
- Graft: 361 nodes / 1133 edges, graph check OK
- Jev functional score: 3.20 / 4
- Jev leakage/metric safety score: 3.35 / 4
- Alibaba Open Code Review delegate rules applied with no blocking finding

## Publication state

Local history is canonical. Remote publication is pending Git authentication for the repository owner; do not rewrite local history to work around authentication.

## Current objective

Implement F6.2 with a frozen LabGold calibration/evaluation split, no patient overlap, held-out final corruption seeds, and reproducible baseline evaluation.