# SafeOCR Reporting and Reproducibility Checklist

## Study identity

- [x] Clearly label the work as a methods/evaluation study.
- [x] State that SafeOCR v0.1 is research software, not a medical device.
- [x] Separate transcription performance, field-verification safety, FHIR conformance, and clinical correctness.
- [x] Define the primary research question before reporting results.
- [x] Define the engineering traceability question.

## Data

- [x] Describe SafeOCR-LabGold as synthetic and PHI-free.
- [x] Freeze calibration and final-evaluation roles.
- [x] Report final split hash.
- [x] Report all final cases in denominators.
- [x] Pin ClinOCR-Bench version/commit and release-asset hash.
- [x] Prevent external evaluation data from entering tuning paths.
- [ ] Document final external OCR run hashes/results after completion.
- [ ] Add a future real clinical field-level annotation protocol; do not imply that ClinOCR transcript truth supplies it.

## Model / engine identity

- [x] Report PaddleOCR version and frozen model names.
- [x] Report Tesseract version.
- [x] Report local CPU/ONNX backend where relevant.
- [x] Report memory-safe recognition batch size.
- [x] State that no OCR model was trained on final data.

## SafeOCR policy

- [x] Define VERIFIED_AUTO, REVIEW_REQUIRED, and ABSTAINED.
- [x] Define criticality.
- [x] Define visual grounding.
- [x] Define structural association.
- [x] Define independent reread.
- [x] Define perturbation stability.
- [x] Define numeric parsing and unit validation.
- [x] Define patient/document linkage.
- [x] Define fail-closed runtime behavior.
- [x] State that engine confidence is not treated as a calibrated probability.

## Evaluation

- [x] Define CFEA.
- [x] Define unsafe accept rate and denominator.
- [x] Define verified coverage and denominator.
- [x] Define review and abstention rates.
- [x] Use Wilson intervals for accepted-error proportions.
- [x] State explicitly that zero observed errors is not zero risk.
- [x] Report the perfect raw-primary-OCR LabGold result rather than hiding it.
- [x] Withhold unsupported FHIR mapping-error claims.
- [x] Withhold unsupported ClinOCR field-level safety claims.
- [ ] Report external document-level WER only after frozen OCR outputs are complete.
- [ ] Compare Tesseract reproduction with official ClinOCR baseline reporting.

## Reproducibility

- [x] Public-source repository prepared.
- [x] Apache-2.0 license.
- [x] Frozen evidence artifacts.
- [x] Deterministic evaluation contracts and tests.
- [x] Static evidence report.
- [x] FHIR validator artifact and invalid-control test.
- [x] External validation protocol committed before outcomes.
- [x] External runner cannot access ground truth.
- [x] External scorer checks no-tuning/no-ground-truth OCR-run attestations.
- [ ] Freeze external result JSON and per-subset table.
- [ ] Freeze manuscript figure-generation scripts.

## Literature / novelty

- [x] Clinical laboratory OCR literature screened.
- [x] Scanned-EHR OCR/NLP literature screened.
- [x] Selective prediction literature screened.
- [x] Risk-control / conformal verification literature screened.
- [x] FHIR/provenance literature screened.
- [x] Closest 2025–2026 prior/parallel work identified.
- [x] Absolute 'first' claim prohibited.
- [ ] Repeat literature search immediately before submission.

## Manuscript integrity

- [x] Claims ledger exists.
- [x] Novelty map exists.
- [x] Negative result is explicit.
- [x] Limitations distinguish evidence gaps from engineering gaps.
- [ ] Main text <=4,000 words for JAMIA.
- [ ] Structured abstract <=250 words.
- [ ] <=4 main tables.
- [ ] <=6 main figures.
- [ ] Figure alt text prepared.
- [ ] Data availability statement finalized.
- [ ] Code availability statement finalized.
- [ ] Funding statement finalized.
- [ ] Competing interests finalized.
- [ ] CRediT statement finalized.
- [ ] AI-assisted writing disclosure aligned with target-journal policy.
- [ ] Cover letter finalized.

## Reporting-guideline boundary

SafeOCR v0.1 is not a diagnostic-accuracy study, prediction-model study, randomized trial, or live early-stage clinical workflow evaluation. Therefore STARD-AI, TRIPOD+AI, CONSORT-AI, SPIRIT-AI, and DECIDE-AI should not be claimed as if they directly govern this study.

DECIDE-AI is explicitly aimed at early-stage live clinical evaluations in which AI-supported decisions affect real patient care. That is not the present study. Its human-factors and implementation principles may inform future prospective work, but the manuscript must not claim DECIDE-AI compliance.

MI-CLAIM is a more appropriate transparency aid for the present preclinical technical evaluation. Use it as a minimum-information cross-check for data provenance, cohort definition, model/engine identity, training/tuning separation, evaluation design, reproducibility, and code availability without implying that the checklist itself establishes methodological quality.

Use all reporting frameworks as reporting aids rather than evidence of validity. Label the present work accurately as a preclinical informatics methods/evaluation study with independent benchmark validation.
