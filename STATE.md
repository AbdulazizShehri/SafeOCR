# SafeOCR State

## In flight

F6 Evaluation is active. F6.2c OCR-only association scoring is exact-head qualified. The F6.2d final-only runner is implemented, but final LabGold execution is locked until that runner is committed and exact-head qualified. No final-evaluation case has been executed yet.

## Canonical local foundation

- architecture commit: `6f11ccb`
- F1 foundation commit: `1d05ba4`
- F2 LabGold commit: `a2c626a`
- F3 OCR adapters commit: `3aba8f6`
- F4 evidence verification commit: `b11da0c`
- patient-binding prerequisite fix: `c711a70`
- F5 FHIR R4 gate commit: `448f024`
- F6.1 evaluation contracts commit: `f3810a8`
- F6.2a split freeze commit: `5b328de`
- F6.2b calibration runtime commit: `abccceed200736a1e45e945b826991ecdd7673e9`
- F6.2c association scorer implementation: `c6abed545b531834a46784f06997ac7fcbb8291b`
- active branch: `feat/f6-evaluation`

## F6 split

- canonical split SHA-256: `3aa0af90f3d41d5a0b636ded5d784119da81a193b81a907b7bb69a789cc816a5`
- calibration: 24 document cases
- final evaluation: 48 document cases
- no final-evaluation case has been inspected or executed to date

## F6.2c exact-head qualification

- canonical evidence: `docs/evidence/F6_CALIBRATION_SMOKE.json`
- evidence head: `c6abed545b531834a46784f06997ac7fcbb8291b`
- evidence reports `working_tree_dirty=false`
- clean + corrupted calibration smoke: 2 documents / 12 field cases
- OCR-only association scorer: 12/12 association-evaluable, 0 observed association errors
- truth geometry used for association row parsing: false
- full default suite: 162 passed, 4 skipped
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings, 0 informations
- Graft: 420 nodes / 1342 edges, graph check OK
- Jev truth-independence advisory: 0.86
- Jev conservative association-isolation advisory: 0.58
- Alibaba Open Code Review delegate review was applied before commit; no blocking host-agent finding remained

## Publication state

Local history is canonical. Remote publication is still blocked by local Git credentials authenticating as `TheHalfMoon`, which has read-only permission on `AbdulazizShehri/SafeOCR`. Do not rewrite local history to work around authentication.

## Current objective

Commit and exact-head qualify the F6.2d final-only runner. Only after that gate passes may it execute all 48 frozen final-role document cases once and write `docs/evidence/F6_FINAL_EVALUATION.json`.
