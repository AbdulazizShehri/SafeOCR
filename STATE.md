# SafeOCR State

## In flight

F6 Evaluation is active. F6.2b calibration runner is committed and clean-head calibration evidence is captured. F6.2c end-to-end association scoring is now the active grain; final-evaluation execution remains locked.

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
- active branch: `feat/f6-evaluation`

## F6 split

- canonical split SHA-256: `3aa0af90f3d41d5a0b636ded5d784119da81a193b81a907b7bb69a789cc816a5`
- calibration: 24 document cases
- final evaluation: 48 document cases
- final role remains inaccessible to the current calibration runner

## F6.2b clean-head evidence

- canonical evidence: `docs/evidence/F6_CALIBRATION_SMOKE.json`
- evidence head: `abccceed200736a1e45e945b826991ecdd7673e9`
- evidence reports `working_tree_dirty=false`
- clean + corrupted calibration smoke: 2 documents / 12 field cases
- primary OCR: CFEA 1.0, UAR 0.0, coverage 1.0
- Tesseract crop: CFEA 0.8333333333333334, UAR 0.16666666666666666, coverage 1.0
- naive agreement: CFEA 1.0, UAR 0.0, coverage 0.8333333333333334
- SafeOCR: CFEA 1.0, UAR 0.0, coverage 1.0
- truth-geometry alignment remains explicitly non-headline
- no final-evaluation data was executed

## Publication state

Local history is canonical. Remote publication is still blocked by local Git credentials authenticating as `TheHalfMoon`, which has read-only permission on `AbdulazizShehri/SafeOCR`. Do not rewrite local history to work around authentication.

## Current objective

Qualify an OCR-only end-to-end row/association scorer on calibration data, remove truth-geometry dependence from any future table-association headline metric, then exact-head qualify before unlocking final LabGold execution.
