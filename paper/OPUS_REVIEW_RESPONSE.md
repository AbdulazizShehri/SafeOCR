# Response to 2026-10-07 Opus Pre-Submission Adversarial Review

Review basis: `paper/safeocr-manuscript @ b616f8224ff5ddcf483ec50ed210b3a39188cb76`

Status: ACTIVE REVISION LOG

This document records the disposition of the adversarial review. It is not peer-review evidence and does not override frozen scientific artifacts. Review suggestions were accepted only when supported by repository evidence or independently verified sources.

## Executive disposition

The review correctly identified that the current frozen safety endpoints contain no primary-OCR errors to intercept. The manuscript has therefore been reframed from safety-gain evidence to a transparent feasibility, auditability, review-cost, and failure-analysis study.

No frozen threshold, cohort, preprocessing rule, OCR result, eligibility rule, operating point, or primary endpoint has been changed.

The current arXiv revision is intended to be publishable as an honest negative/feasibility systems preprint after identity confirmation and final PDF inspection.

JAMIA remains a separate decision. A new end-to-end error-interception study is being designed under a new protocol and has not been run.

## F1 — no evaluation shows gate interception on the primary endpoint

**Disposition: ACCEPTED.**

Actions:
- report primary OCR 0/288 beside SafeOCR 0/209;
- report ungated Wilson upper bound 1.316% beside gated 1.805%;
- state that all 79 LabGold reviews were correct on the evaluated endpoint;
- report primary numeric OCR 1,850/1,850 beside component-pass 0/375;
- report ungated numeric Wilson upper bound 0.207% beside gated 1.014%;
- state that all 1,475 component rejections were numerically correct under the frozen reference labels;
- conclusion now explicitly states that current evidence does not demonstrate a reduction in accepted error.

A separate draft follow-up protocol now defines an end-to-end full-tuple error-interception study. It is not frozen or executed.

## F2 — public laboratory-report provenance and kappa attribution

**Disposition: ACCEPTED AND CORRECTED.**

Actions:
- cite Xue et al. 2020 as the source of the public image collection;
- retain Ma et al. 2023 as a later user/descriptor of the collection;
- explicitly state that Ma et al.'s kappa=0.89 belongs to PKU1, not the public collection;
- state that the public label-generation/adjudication process is undocumented in the audited source materials;
- add a post-outcome protocol addendum without modifying the frozen protocol.

## M1 — numeric endpoint narrower than full-field correctness

**Disposition: ACCEPTED.**

Actions:
- explicitly state that the frozen numeric endpoint is narrower than the manuscript's general full-field correctness definition;
- cite commit `47433ae8fb429671489ac530dfd05c95a82bfaf4` as the pre-outcome code definition and `6f082d8...` as the later result-freeze commit;
- give the exploratory 38/375 analyte-or-unit mismatch finding equal prominence;
- retain it as post-outcome exploratory analysis; do not reclassify the frozen endpoint.

## M2 — 57/328 PaddleOCR runtime failures

**Disposition: ACCEPTED.**

Actions:
- abstract and Results report 57/328 failures (17.4%);
- report concentration in rotated (33/56) and mixed (24/48) subsets;
- retain failures in the denominator and score them as empty under the frozen policy;
- add descriptive paired comparison and non-failed sensitivity from frozen per-document artifacts.

No failures were rescored.

## M3 — prespecified official-vs-local Tesseract comparison

**Disposition: ACCEPTED.**

Actions:
- add the official-versus-local subset median table;
- explicitly state that the local run is not an exact reproduction;
- flag the rotation discrepancy as likely environment/orientation/page-segmentation sensitivity rather than conceal it.

## M4 — ClinOCR-Bench description

**Disposition: ACCEPTED.**

Actions:
- remove "realism benchmark";
- describe ClinOCR-Bench as a synthetic, template-generated, PHI-free clinical-document OCR benchmark;
- keep it scoped to transcription-level external benchmark evidence only.

## M5 — LabGold truth-geometry alignment

**Disposition: ACCEPTED.**

Actions:
- Methods disclose `alignment_mode = truth_geometry_scoring` for legacy per-field scoring;
- state that these are not end-to-end field-discovery metrics;
- state that the Tesseract-crop baseline measures crop-read correctness;
- preserve the separate OCR-geometry-only association scorer.

## M6 — LabGold design/dependence

**Disposition: SUBSTANTIALLY ACCEPTED.**

Actions:
- disclose 24 synthetic records represented as 48 clean/corrupt documents across three templates, six fields per document;
- state that ABSTAINED was not exercised;
- add post-outcome descriptive document- and record-level zero-event bounds;
- do not present field-level Wilson intervals as cluster-robust.

The requested per-gate distribution for the 79 reviews is not added unless it can be reconstructed directly from frozen artifacts without invention.

## M7 — Ma2023 cohort flow and protocol/code deviation

**Disposition: ACCEPTED.**

Actions:
- report 2,219 candidate rows and all exclusion counts;
- report that eligible rows come from 180/238 images;
- disclose that 58 images contribute no eligible row under frozen rules;
- disclose the unit-rule protocol/code deviation;
- disclose the three pre-outcome compatibility/integrity repairs;
- preserve all frozen counts without post-hoc correction.

## M8 — second-engine and perturbation dependence

**Disposition: ACCEPTED.**

Actions:
- replace "independent reread" with "second-engine reread";
- explicitly state shared primary-defined crop dependence;
- state perturbation stability is related to second-engine agreement rather than an independent signal;
- add the frozen descriptive gate-overlap funnel;
- identify missing analyte semantic verification as the key design gap.

## M9 — "preregistered" wording

**Disposition: ACCEPTED.**

Actions:
- manuscript and arXiv source use "prespecified, version-controlled/commit-timestamped";
- explicitly state there was no external preregistration service.

## M10 — JAMIA reference status

**Disposition: ACCEPTED FOR SUBMISSION PREPARATION.**

Actions:
- replace several preprint citations with published proceedings versions where available;
- add published Xue 2020 and RAPTOR 2025 anchors;
- maintain arXiv-only work as internal novelty surveillance when necessary;
- final JAMIA bibliography remains subject to a last publication-status audit immediately before submission.

## M11 — novelty narrower than claimed

**Disposition: ACCEPTED.**

Actions:
- novelty claim is now specification/integration/evaluation methodology;
- no universal "first" claim;
- manuscript states that marginal accepted-error reduction from the added gates is not demonstrated in v0.1.

## M12 — reproducibility gaps

**Disposition: PARTIALLY CLOSED.**

Closed:
- Xue/Ma provenance and redistribution boundary documented;
- dataset manifest and OCR run-state hashes documented;
- scorer head documented;
- explicit Tesseract path is supported by the current scorer/runner interfaces;
- ClinOCR frozen release hash/commit documented.

Still open before archival release:
- record the full labels-file SHA-256 in the release manifest;
- create a paper release/tag after final identity/PDF review;
- archive release/DOI if chosen;
- retain only claims supported by committed artifacts.

## M13 — arXiv package

**Disposition: SUBSTANTIALLY CLOSED; TWO MANUAL GATES REMAIN.**

Closed:
- duplicate Markdown title/draft front matter removed;
- section structure repaired;
- four tables present;
- two figures present;
- Xue/FHIR citations synchronized;
- malformed LaTeX tables repaired;
- static citation/package audit passes: 23 cited keys, 23 bibliography entries, zero missing/uncited entries.

Open:
1. confirm one canonical scholarly author name and affiliation;
2. complete a clean LaTeX compile and visual PDF inspection.

## M14 — internal strategy / AI review material

**Disposition: CONTROLLED.**

The arXiv upload package contains only submission source files, not strategy documents or review logs. AI-generated quality scores are not treated as scientific validation or independent peer review. The manuscript disclosure names AI-assisted roles and assigns accountability to the author.

## Moderate/minor findings incorporated

The revision also:
- adds possible OCR training-distribution contamination as a limitation;
- removes unsupported real-world patient-linkage performance implications;
- scopes FHIR evidence to a single-bundle conformance smoke test;
- cites FHIR R4 explicitly;
- states terminology validation is not a clinical correctness endpoint;
- removes unused bibliography entries;
- strengthens data-rights wording for the Xue repository;
- records post-outcome cluster-sensitivity bounds as descriptive only.

## Remaining arXiv blockers

1. canonical scholarly name/affiliation confirmation;
2. successful LaTeX compilation and visual inspection;
3. deliberate arXiv manuscript-license choice.

No new scientific experiment is required to post an honestly reframed arXiv v1.

## Remaining JAMIA blocker

The key substantive blocker remains the absence of non-zero baseline full-tuple errors on a prespecified end-to-end safety endpoint.

A separate draft protocol now exists at:
`paper/JAMIA_FOLLOWUP_ERROR_STUDY_PROTOCOL.md`

RJUA-MedDQA is only a candidate dataset and remains unqualified until its released annotations are shown to support prediction-blind laboratory full-tuple gold construction.

## Frozen-science decision

The frozen v0.1 scientific protocol remains unchanged.

Outcome-driven threshold tuning, endpoint replacement, duplicate re-adjudication, failure rescoring, or cohort repair after outcome inspection would damage the strongest methodological property of the project: transparent prespecification followed by honest reporting of negative results.
