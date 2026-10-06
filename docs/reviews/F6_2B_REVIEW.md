# F6.2b Calibration Runtime Review

Date: 2026-10-06
Phase: F6.2b calibration-only LabGold runtime runner

## Runtime scope

The runner is intentionally calibration-only. It selects only `EvaluationRole.CALIBRATION` cases from the preregistered split. There is no CLI option that unlocks final-evaluation cases.

The runner executes:
- PaddleOCR 3.7.0 / PP-OCRv6 small detector + recognizer on CPU;
- Tesseract 5.4 crop reads;
- raw primary OCR baseline;
- oracle truth-crop Tesseract baseline;
- naive exact-agreement baseline;
- SafeOCR verification policy with perturbation and UCUM checks.

## Calibration smoke

Two preregistered calibration document cases were exercised: one clean and its frozen corrupted variant, producing 12 laboratory-field cases.

Observed calibration-only diagnostics:
- primary OCR: 12/12 exact field reads, 12/12 accepted;
- Tesseract truth-crop baseline: 10/12 exact value reads, 12/12 accepted;
- naive agreement: 10/12 accepted, 2/12 review-required;
- SafeOCR: 12/12 accepted in this bounded smoke.

These are calibration diagnostics only. They are not final benchmark claims.

## Evaluation-boundary limitation

Current calibration plumbing uses truth geometry to align OCR spans to benchmark fields for scoring. Therefore:
- it is not an end-to-end row parser;
- patient-attribution and table-association rates from this runner are diagnostic only;
- the Tesseract crop baseline inherits benchmark field identity and measures crop-read correctness;
- no headline table-association claim may be made until an end-to-end association scorer is qualified.

These limitations are emitted in the machine-readable runtime payload.

## Mechanical gates

- default pytest: 157 passed, 4 runtime tests skipped by design
- explicit F6 runtime smoke: 1 passed using clean + corrupted calibration cases
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings
- Graft: 402 nodes / 1285 edges, graph check OK
- git diff --check: PASS
- split SHA remains `3aa0af90f3d41d5a0b636ded5d784119da81a193b81a907b7bb69a789cc816a5`

## Jev

- initial runner correctness expected-level score: 2.87 / 4
- benchmark/leakage safety score: 3.30 / 4
- after making the oracle-scoring boundary explicit, bounded-runner score: 3.10 / 4

The initial lower score was treated as a signal to narrow the claim surface rather than as a reason to tune benchmark outcomes.

## Alibaba Open Code Review

Delegate preview/rules were applied to the runner, evaluation module, and runtime test. No blocking correctness or security finding remains.

## Gate

Final-evaluation execution remains locked. The runner must first be committed, then rerun from a clean exact head to produce canonical calibration evidence.
