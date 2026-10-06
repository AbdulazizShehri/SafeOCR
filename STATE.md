# SafeOCR State

## In flight

F6 Evaluation is active. F6.1 and F6.2a are qualified. F6.2b calibration-only runtime runner is next.

## Canonical local foundation

- architecture commit: `6f11ccb`
- F1 foundation commit: `1d05ba4`
- F2 LabGold commit: `a2c626a`
- F3 OCR adapters commit: `3aba8f6`
- F4 evidence verification commit: `b11da0c`
- patient-binding prerequisite fix: `c711a70`
- F5 FHIR R4 gate commit: `448f024`
- F6.1 evaluation contracts commit: `f3810a8`
- active branch: `feat/f6-evaluation`

## F6.2a split freeze

- canonical split: `docs/evidence/F6_LABGOLD_SPLIT.json`
- split SHA-256: `3aa0af90f3d41d5a0b636ded5d784119da81a193b81a907b7bb69a789cc816a5`
- calibration: 24 document cases
- final evaluation: 48 document cases
- clean + corrupted variants for every record seed
- patient identities disjoint across calibration/evaluation roles
- unique frozen corruption seeds
- primary OCR, Tesseract crop, and naive agreement baseline semantics frozen
- full pytest: 156 passed, 3 skipped
- Graft: 381 nodes / 1190 edges, graph check OK
- Jev correctness: 3.23 / 4
- Jev leakage/preregistration safety: 3.67 / 4
- Alibaba delegated review: no blocking finding

## Publication state

Local history is canonical. Remote publication is pending Git authentication for the repository owner; do not rewrite local history to work around authentication.

## Current objective

Build F6.2b using calibration-role data only. Freeze and qualify the runner before the first final-evaluation OCR execution.
