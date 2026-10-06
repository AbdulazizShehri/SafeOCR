# SafeOCR State

## In flight

F8 v0.1 is locally merged and requalified. Release branch merge commit `0ec635856ebf62e3b16c3a066f23123b0b4cd399` passed the full local gate. Only signed-tag creation and GitHub publication remain blocked on local owner-account authentication/signing setup.

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
- active branch: `release/v0.1.0-closeout`
- F8 release merge commit on `main`: `0ec635856ebf62e3b16c3a066f23123b0b4cd399`
- F6 closeout commit: `be9b772`
- F7 static evidence report commit: `f39540e1401d4347dd08bea77c35077933cbd484`
- F8 release-candidate implementation commit: `76139294d1b5a9277d1fd51e7e1445b33e888f68`

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

Local history is canonical. Remote publication is blocked because the local GitHub CLI currently authenticates as `IamShehri`, which is not a collaborator on `AbdulazizShehri/SafeOCR`; the owner account is connected inside ChatGPT but not available to local Git credential helpers. Signed release-tag creation is also blocked because no SafeOCR signing key is configured locally. Do not rewrite local history or create an unsigned release tag to work around either blocker.

## Current objective

Commit this closeout, merge it normally into `main`, requalify the final exact head, then authenticate the local Git client as `AbdulazizShehri` and configure an approved signing key before creating/pushing `v0.1.0`.
