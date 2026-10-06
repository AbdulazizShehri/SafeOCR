# SafeOCR State

## In flight

F6 Evaluation is next. F5 FHIR R4 export gate is closed and qualified.

## Canonical local foundation

- architecture commit: `6f11ccb`
- F1 foundation commit: `1d05ba4`
- F2 LabGold commit: `a2c626a`
- F3 OCR adapters commit: `3aba8f6`
- F4 evidence verification commit: `b11da0c`
- patient-binding prerequisite fix: `c711a70`
- active branch: `feat/f5-fhir-export`
- GitHub connector now has admin/push access to `AbdulazizShehri/SafeOCR`

## F5 closeout

- FHIR R4 4.0.1 only
- HL7 validator CLI 6.10.4
- validator JAR SHA-256: `1106b9d58f9e363e47bea7c4fc065841e5fc91fe9d062775c3bfdd212bd653cc`
- canonical evidence: `docs/evidence/F5_RUNTIME_SMOKE.json`
- valid bundle: 0 errors, 7 documented warnings, 1 note
- deliberately invalid control: rejected with 2 errors
- default pytest: 139 passed, 3 skipped
- explicit official-validator runtime pytest: 1 passed in 72.51s
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings
- pip check: PASS
- Graft: 333 nodes / 1063 edges, graph check OK
- git diff --check: PASS
- Jev functional acceptance: 3.21 / 4 expected-level score
- Jev fail-closed safety/interoperability: 3.55 / 4 expected-level score
- Alibaba Open Code Review delegate rules applied to the final reviewable code surface; no blocking finding remains

## Current objective

Begin F6 Evaluation from the closed F5 export gate. Do not tune thresholds on held-out evaluation data.