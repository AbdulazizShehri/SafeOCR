# SafeOCR State

## In flight

F6 Evaluation is active. F6.2d final LabGold evaluation completed successfully on governed attempt 2. The primary final artifact is frozen and must not be rerun or overwritten. F6.3 external ClinOCR-Bench / Safety Track integration is next.

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
- F6.2d final-runner commit: `162a9c03536a82e1e1b346ecfdaeb56124de7940`
- F6.2d memory-recovery commit: `e755e36d0379e11b768b573af0c04bb9559be408`
- active branch: `feat/f6-evaluation`

## F6 split

- canonical split SHA-256: `3aa0af90f3d41d5a0b636ded5d784119da81a193b81a907b7bb69a789cc816a5`
- calibration: 24 document cases
- final evaluation: 48 document cases / 288 field cases
- final role completed once successfully for the primary v0.1 claim on governed attempt 2
- attempt 1 was infrastructure-only and emitted no final metric artifact

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

## F6.2d primary final evidence

- primary artifact: `docs/evidence/F6_FINAL_EVALUATION.json`
- exact execution head: `e755e36d0379e11b768b573af0c04bb9559be408`
- artifact reports `working_tree_dirty=false`
- SafeOCR: CFEA 1.0, UAR 0.0, verified coverage 0.7256944444444444, review rate 0.2743055555555556
- SafeOCR accepted fields: 209 / 288; zero observed unsafe accepts; 95% Wilson upper bound 0.018048451847580686
- naive agreement: UAR 0.0, coverage 0.8402777777777778
- primary OCR: UAR 0.0, coverage 1.0 on this synthetic benchmark
- Tesseract crop: UAR 0.156794425087108, coverage 0.9965277777777778
- OCR-only table association scorer: 288 / 288 evaluable, 0 observed association errors
- truth geometry used for association row parsing: false
- patient-attribution and FHIR-mapping headline rates remain outside this LabGold runner
- attempt 1 failure evidence remains immutable at `docs/evidence/F6_FINAL_ATTEMPT_1_FAILURE.json`

## Interpretation boundary

Because raw primary OCR observed zero accepted errors at full coverage on the frozen synthetic final set, LabGold alone does not support a claim that SafeOCR lowers unsafe accepted error versus the primary OCR baseline. The SafeOCR result is reported as selective coverage with zero observed unsafe accepts and its confidence interval, not as proof of zero risk or superiority.

## Publication state

Local history is canonical. Remote publication is still blocked by local Git credentials authenticating as `TheHalfMoon`, which has read-only permission on `AbdulazizShehri/SafeOCR`. Do not rewrite local history to work around authentication.

## Current objective

Implement F6.3 as an external-evaluation adapter and Safety Track manifest that cannot tune thresholds from external evaluation data. Then complete F6.4 reproducible risk-coverage artifacts and limitations.
