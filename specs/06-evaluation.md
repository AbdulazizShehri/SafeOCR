# F6 � Evaluation

Status: IN PROGRESS
Depends on: F5 FHIR R4 export gate (448f024)

## Objective

Measure SafeOCR as a selective clinical-OCR verification system without tuning on held-out evaluation data.

## Frozen evaluation rules

1. Calibration and final evaluation are separate roles.
2. Patient identities must not cross roles.
3. LabGold final-evaluation corruption seeds are frozen before any final result is inspected.
4. Final-evaluation outcomes may be measured but never passed to a tuning API.
5. External ClinOCR-Bench evaluation data never selects SafeOCR thresholds.
6. Zero observed unsafe accepts is reported as zero observed errors with an interval, never as zero risk.

## Headline metrics

- Critical Field Exact Accuracy (CFEA)
- Unsafe Accept Rate (UAR)
- Verified Coverage (VC)
- Review Rate
- Abstention Rate
- Patient Attribution Error Rate
- Table Association Error Rate
- FHIR Mapping Error Rate
- 95% Wilson confidence interval for accepted-error proportions
- risk/coverage points by method

## Baselines

- raw primary OCR
- raw Tesseract critical-crop read
- naive exact-agreement gate
- SafeOCR verification policy

## Grain F6.1 � deterministic evaluation contracts

Deliver:
- typed truth/prediction/outcome contracts;
- deterministic exact-field comparison;
- aggregate headline metrics;
- Wilson interval implementation with explicit zero-denominator behavior;
- risk/coverage point generation;
- role-aware leakage guard;
- tests proving final-evaluation records cannot be used as calibration inputs.

Exit:
- pytest/Ruff/Pyright/Graft/Jev/OCR review pass.

## Remaining F6 grains

F6.2a — CLOSED:
- frozen LabGold split manifest and corruption schedule;
- preregistered manifest SHA-256;
- baseline prediction semantics for primary OCR, Tesseract crop, and naive agreement.

F6.2b — QUALIFIED CALIBRATION RUNNER:
- calibration-only LabGold runtime runner;
- explicit runtime smoke covering clean + corrupted calibration cases;
- truth-geometry scoring limitation is machine-readable and documented;
- final-evaluation execution remains locked until the runner commit is canonical.

F6.2c — CLOSED:
- [x] run the committed calibration runner from a clean tree;
- [x] capture canonical calibration evidence at `docs/evidence/F6_CALIBRATION_SMOKE.json`;
- [x] design and qualify an OCR-only end-to-end association scorer before any headline table-association claim;
- [x] exact-head qualify commit `c6abed545b531834a46784f06997ac7fcbb8291b` before unlocking final LabGold execution.

F6.2d — INFRASTRUCTURE RECOVERY:
- [x] implement a final-evaluation-only runner over the frozen split;
- [x] expose no partial-case, threshold-tuning, or calibration path;
- [x] record the exact split SHA-256 and clean git head at run start;
- [x] refuse overwrite/rerun when primary evidence already exists;
- [x] exact-head qualify runner commit `162a9c03536a82e1e1b346ecfdaeb56124de7940`;
- [x] preserve failed attempt 1 as infrastructure-only evidence with no final metrics emitted;
- [x] constrain PaddleOCR text-recognition batch size without changing model/policy/split;
- [ ] requalify the recovery runner on calibration data and exact head;
- [ ] execute the recovery final run and report it explicitly as attempt 2.

F6.3:
- ClinOCR-Bench adapter + Safety Track manifest without test-set tuning.

F6.4:
- reproducible benchmark run, risk-coverage artifacts, limitations and closeout evidence.