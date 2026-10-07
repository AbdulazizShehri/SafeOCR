# JAMIA Follow-up Error-Interception Study Protocol

Status: DRAFT — NOT FROZEN — DO NOT RUN FINAL EVALUATION YET

This protocol defines a new, separate study intended to address the central evidentiary limitation identified in the 2026-10-07 adversarial review: the frozen SafeOCR v0.1 evaluations contained no primary-OCR errors on their primary safety endpoints, so they could not demonstrate that the verification gate intercepts genuine errors.

This study is **not** a re-analysis of SafeOCR-LabGold, ClinOCR-Bench, or the Xue/Ma public laboratory-report component study. Their frozen results remain unchanged.

## 1. Research question

On previously uninspected laboratory-report images with a non-trivial baseline full-field OCR error rate, does the frozen SafeOCR verification contract intercept primary-OCR analyte-value-unit tuple errors while retaining useful verified coverage?

The intended contribution is a direct measurement of **error interception versus automation cost**, not a post-hoc threshold comparison.

## 2. Candidate external dataset

Primary candidate: **RJUA-MedDQA**, published at KDD 2024.

Published reference:

Congyun Jin et al. *RJUA-MedDQA: A Multimodal Benchmark for Medical Document Question Answering and Clinical Reasoning*. Proceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining, 2024, pp. 5218–5229. DOI: 10.1145/3637528.3671644.

Public repository metadata describes 2,000 medical-report images spanning screenshots, scanned-PDF images, and patient-captured photos, and the dataset license is CC BY-NC-SA 4.0. The dataset includes laboratory reports among broader medical-document types.

### Dataset suitability gate

Before this protocol can be frozen, a **metadata/annotation-only qualification** must establish all of the following without running SafeOCR or inspecting model outputs on the intended final set:

1. laboratory-report documents can be selected from released metadata without using OCR outcomes;
2. the released annotations or source structure are sufficient to construct analyte-value-unit gold tuples, or a blinded manual annotation protocol can do so without viewing SafeOCR predictions;
3. image redistribution and derivative annotation handling comply with the upstream dataset license;
4. the final-set images have not previously been used to tune SafeOCR;
5. the selected final set is distinct from all current SafeOCR evaluation data.

If any condition fails, do not use RJUA-MedDQA for this study. Select another dataset and revise/freeze the protocol before running OCR.

## 3. Split and outcome-inspection firewall

After dataset suitability is established, create a deterministic manifest using dataset identifiers only.

Proposed split:
- calibration/suitability subset: 10% of eligible laboratory-report documents;
- final evaluation subset: remaining 90%.

The split must be generated from a committed deterministic seed and frozen before any SafeOCR result on the final subset exists.

The calibration subset may be used only to answer the dataset-suitability question and to verify that the chosen document family is sufficiently challenging. It must not be used to tune SafeOCR thresholds, gates, preprocessing, OCR models, language packs, or acceptance policy.

### Predeclared suitability criterion

Proceed to final evaluation only if the calibration subset exhibits a measurable primary-OCR **full analyte-value-unit tuple error rate of at least 2%** among evaluable rows.

If the calibration subset does not meet this criterion:
- stop;
- report the dataset as unsuitable for the intended error-interception study;
- do not inspect SafeOCR results on the final subset;
- choose another dataset under a newly versioned protocol.

This is a dataset-selection rule, not a final-set exclusion rule.

## 4. Frozen system configuration

Unless a new version is explicitly declared before protocol freeze, use the same SafeOCR v0.1 verification policy and the same frozen OCR engines:

- primary OCR: PaddleOCR 3.7.0;
- detection: PP-OCRv6_small_det;
- recognition: PP-OCRv6_small_rec;
- backend: ONNX Runtime CPU;
- second-engine reread: Tesseract 5.4.0.20240606;
- existing crop padding, perturbations, numeric parsing, structural association, unit validation, criticality, and terminal-state logic.

No threshold sweep, model substitution, OCR fine-tuning, language-pack change, or outcome-driven preprocessing change is allowed after the final manifest is frozen.

Any necessary compatibility repair that occurs before final outcomes exist must be recorded with:
- exact failure;
- exact code change;
- qualification evidence;
- confirmation that no final outcome was inspected.

## 5. Gold-standard construction

The primary correctness unit is the complete analyte-value-unit tuple.

For each evaluable laboratory row, gold must contain:
- analyte text/identity;
- numeric or categorical value;
- unit where applicable;
- source document identifier;
- source region or row identity sufficient for post-inference scoring.

Gold creation must be independent of SafeOCR outputs.

If manual annotation is required:
- annotators must not see SafeOCR predictions;
- annotation instructions must be frozen first;
- ambiguous rows must be marked non-evaluable rather than arbitrarily adjudicated;
- the adjudication process and inter-annotator agreement must be reported if more than one annotator is available.

## 6. End-to-end boundary

This study must evaluate **end-to-end field discovery and verification**.

Gold geometry may be used only after inference to score predicted fields against truth.

Gold text or geometry must not:
- define OCR crops during inference;
- locate fields for PaddleOCR or Tesseract;
- select predictions;
- rewrite OCR text;
- choose preprocessing;
- alter SafeOCR acceptance decisions.

A prediction that cannot be matched to a gold field under the frozen scoring rule counts as a miss, not as unevaluable solely because the system failed to find it.

## 7. Primary endpoint

Primary endpoint: **full-tuple error interception rate** among primary-OCR errors.

Let:
- N = number of evaluable gold fields;
- B = number of fields where the primary OCR analyte-value-unit tuple is incorrect;
- U = number of those B incorrect primary fields that SafeOCR still accepts automatically;
- I = B - U = number of primary-OCR tuple errors routed to REVIEW_REQUIRED or ABSTAINED.

Report:

- baseline full-tuple error rate = B / N;
- unsafe accepted full-tuple errors = U;
- error interception rate = I / B, when B > 0;
- verified coverage = accepted fields / N;
- false-review burden = correct primary-OCR fields rejected / correct primary-OCR fields;
- review rate;
- abstention rate.

The study succeeds scientifically even if SafeOCR fails to intercept errors; negative results must be reported unchanged.

## 8. Secondary endpoints

Secondary endpoints:

1. numeric-value error interception;
2. analyte-identity error interception;
3. unit error interception;
4. table/row association error;
5. runtime-failure containment;
6. verified coverage by acquisition mode (scan, screenshot, photo where available);
7. error-interception and coverage by document-quality stratum where metadata supports a frozen definition;
8. patient/document linkage only if the dataset supplies an appropriate governed reference standard;
9. FHIR mapping correctness only if separately annotated and prespecified.

Do not infer patient-linkage or FHIR correctness from document OCR alone.

## 9. Statistical analysis

The final analysis must respect clustering of fields within documents.

Primary reporting:
- exact counts and denominators;
- field-level proportions;
- document-cluster bootstrap 95% intervals for verified coverage, unsafe accepted error, error interception, and false-review burden;
- document-level event rates where interpretable.

Use a deterministic bootstrap seed recorded in the analysis artifact.

Do not use field-independent binomial intervals as the sole uncertainty statement for clustered final data.

No post-hoc operating-point sweep is permitted.

## 10. Failure policy

Runtime failures are outcomes, not deletions.

For primary OCR:
- runtime failure remains in the denominator;
- failed OCR output is represented as empty/no prediction.

For verification:
- runtime failure must fail closed;
- it may not be converted to VERIFIED_AUTO.

Exception classes should be recorded explicitly rather than caught only as an unclassified aggregate wherever feasible.

## 11. Prespecification artifacts required before execution

Before any final-set OCR:

1. commit this protocol with status changed to FROZEN;
2. commit the exact dataset qualification report;
3. commit the deterministic split manifest and its SHA-256;
4. commit the annotation schema/instructions and gold-manifest hash;
5. commit the scoring script and tests;
6. record exact engine/model/runtime fingerprints;
7. run static/code review;
8. run test qualification;
9. verify that the final-run process cannot access gold labels during OCR;
10. record the exact clean git head.

## 12. Claim boundary

If the study produces non-zero baseline tuple errors, SafeOCR may claim only what the frozen results establish.

Potentially supportable claims:
- observed full-tuple error-interception rate;
- observed unsafe accepted-error rate at the frozen coverage;
- review/abstention cost;
- acquisition-mode differences;
- fail-closed runtime containment.

Still prohibited without additional evidence:
- universal clinical safety;
- deployment readiness;
- medical-device validation;
- zero underlying risk;
- cross-institution generalization beyond the evaluated data;
- formal conformal/distribution-free risk guarantees unless a separate calibrated method is implemented and prespecified.

## 13. Relationship to the current paper

The current SafeOCR v0.1 evidence remains a transparent feasibility/negative-result package.

This follow-up study is intended to answer the question that the current data cannot answer: **does the frozen gate actually intercept real primary-OCR full-field errors?**

Do not merge new results into the current arXiv v1 until:
- the protocol is frozen;
- the final study is complete;
- all deviations are documented;
- the manuscript clearly distinguishes original frozen evidence from the new study.
