# SafeOCR JAMIA Figure and Table Plan

## Main tables

### Table 1 — SafeOCR verification contract
Purpose: define the safety contract without forcing readers to infer it from prose.

Columns:
- gate;
- input evidence;
- pass criterion;
- failure state;
- downstream effect.

Rows:
- source-region grounding;
- analyte/value/unit association;
- independent OCR-family reread;
- perturbation stability;
- numeric parsing;
- unit validation;
- patient/document linkage;
- runtime health.

### Table 2 — Frozen SafeOCR-LabGold final evaluation
Purpose: report the primary preregistered benchmark transparently, including the negative result.

Rows:
- primary OCR;
- Tesseract crop;
- naive agreement;
- SafeOCR.

Columns:
- accepted;
- review;
- abstain;
- verified coverage;
- unsafe accepts;
- unsafe-accept rate;
- 95% interval.

Mandatory footnote:
The primary OCR baseline observed zero errors at 100% coverage; therefore LabGold does not establish SafeOCR superiority over that baseline.

### Table 3 — ClinOCR-Bench external OCR generalization
Purpose: separate transcription generalization from field-level safety.

Rows:
- frozen PaddleOCR runtime;
- frozen local Tesseract runtime.

Columns:
- N;
- mean WER;
- 95% CI;
- median WER;
- Q1-Q3;
- normal;
- handwriting;
- poor quality;
- rotation;
- tables;
- mixed artifacts.

Mandatory footnote:
Document-level WER is not converted into SafeOCR unsafe-accept, verified-coverage, patient-linkage, or FHIR claims.

### Table 4 — Ma2023 oracle-localised external verifier component
Purpose: provide real laboratory-report field-level evidence while preserving the component-only estimand.

Rows:
- all eligible fields;
- scan stratum;
- illumination/photo stratum.

Frozen result columns:
- eligible fields: 1,850 overall; 926 scan; 924 illumination;
- value-region localisation: 1,850/1,850 overall;
- exact primary numeric value: 1,850/1,850 overall;
- independent agreement: 654/1,850 overall;
- perturbation stability: 449/1,850 overall;
- unit-valid gate: 1,347/1,850 overall;
- component accepted: 375/1,850 (20.27%); 192/926 scan; 183/924 illumination;
- incorrect numeric values among component passes: 0/375;
- numeric accepted-error rate: 0% observed;
- 95% Wilson interval: 0-1.014%.

Mandatory footnotes:
Gold annotations localise the evaluation field after OCR and are never inputs to OCR inference.
This is not end-to-end extraction accuracy and does not estimate full VERIFIED_AUTO coverage.
Ambiguous public annotations are excluded fail-closed and reported explicitly.

## Main figures

### Figure 1 — SafeOCR system architecture
Flow:
immutable document -> primary OCR -> evidence-bound candidate -> independent crop reread -> deterministic verification gates -> VERIFIED_AUTO / REVIEW_REQUIRED / ABSTAINED -> FHIR export only from VERIFIED_AUTO.

Visual requirement:
show the source-pixel/provenance path separately from the decision path.

### Figure 2 — Evidence-bound field and verification gate
A single laboratory row example showing:
- analyte bounding region;
- value bounding region;
- unit bounding region;
- primary OCR;
- independent reread;
- perturbation rereads;
- gate outcomes;
- final decision;
- provenance link.

Use synthetic/PHI-free example only.

### Figure 3 — LabGold automation-risk operating points
Axes:
- x: verified coverage;
- y: unsafe-accept rate.

Plot the four frozen operating points with 95% intervals where defined.
Do not draw a continuous SafeOCR risk-coverage curve because only one SafeOCR operating point was preregistered.

### Figure 4 — External validation
Panel A:
ClinOCR-Bench mean/median WER by artifact subset for PaddleOCR and local Tesseract.

Panel B:
Ma2023 verifier-component accepted-error versus component coverage, split into scan and illumination strata, only after the frozen artifact completes.

## Supplementary material

- full ClinOCR per-subset WER components (substitution/deletion/insertion);
- per-document ClinOCR metrics;
- Ma2023 annotation-integrity exclusions;
- exact engine/model/runtime fingerprints;
- FHIR validator output;
- evidence-report example;
- claims ledger;
- novelty map;
- literature search strategy;
- MI-CLAIM cross-check;
- reproducibility commands and hashes.

## Design rule

A result appears in exactly one main table/figure unless repetition is needed for orientation. Narrative text should state the finding and interpretation, not duplicate every numeric cell.
