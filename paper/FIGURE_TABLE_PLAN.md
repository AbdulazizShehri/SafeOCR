# SafeOCR JAMIA Figure and Table Plan

## Main tables

### Table 1 — Frozen SafeOCR-LabGold final evaluation

Rows:
- primary OCR;
- Tesseract crop;
- naive agreement;
- SafeOCR.

Mandatory interpretation:
- primary OCR observed 0/288 errors at 100% coverage (95% Wilson upper bound 1.316%);
- SafeOCR observed 0/209 errors at 72.57% coverage (upper bound 1.805%);
- all 79 SafeOCR reviews were correct fields under benchmark truth;
- therefore this endpoint measures feasibility/review cost and does not establish a safety gain.

### Table 2 — ClinOCR-Bench official versus local Tesseract reproduction

Rows:
- normal;
- handwriting;
- poor quality;
- rotation;
- tables;
- mixed.

Columns:
- official Tesseract median WER;
- local frozen Tesseract median WER.

Mandatory interpretation:
The local run is not an exact reproduction of the official environment; the rotation discrepancy is material and is reported rather than normalized away.

### Table 3 — Public laboratory-report cohort flow

Rows:
- candidate laboratory rows;
- unsupported gold value;
- missing unit;
- ambiguous duplicate critical cell;
- missing value;
- missing analyte;
- eligible rows.

Mandatory notes:
- 2,219 candidate rows -> 1,850 eligible;
- eligible rows come from 180/238 images;
- 58 images contribute no eligible row under the frozen table/eligibility rules;
- the unit requirement is disclosed as a protocol/code deviation in the post-outcome addendum.

### Table 4 — Frozen verifier-component gate funnel

Rows:
- eligible;
- second-engine numeric agreement;
- agreement + perturbation stability;
- + valid unit syntax;
- + structural association / component pass.

Mandatory interpretation:
- primary numeric readings were already exact in 1,850/1,850 eligible rows;
- 0/375 numeric errors among component passes cannot demonstrate numeric-error reduction;
- the exploratory 38/375 analyte-or-unit mismatch result is reported separately and prominently.

## Main figures

### Figure 1 — SafeOCR system architecture

Flow:
immutable document -> primary OCR -> evidence-bound candidate -> second-engine crop reread -> deterministic verification gates -> VERIFIED_AUTO / REVIEW_REQUIRED / ABSTAINED -> FHIR export only from VERIFIED_AUTO.

The source-pixel/provenance path should remain visually distinct from the decision path.

### Figure 2 — Frozen LabGold coverage versus accepted error

Plot:
- primary OCR;
- Tesseract crop;
- naive agreement;
- SafeOCR.

Do not draw a continuous SafeOCR risk-coverage curve because only one SafeOCR operating point was prespecified. The caption must say that the primary baseline had no endpoint errors, so the zero-event SafeOCR result does not demonstrate a safety gain.

## Supplementary candidates

- full ClinOCR per-subset mean/median WER and substitution/deletion/insertion components;
- PaddleOCR failure distribution, including 33/56 rotated and 24/48 mixed failures;
- Ma2023 scan versus illumination strata;
- Ma2023 annotation-integrity exclusions;
- Ma2023 gate-overlap and exploratory tuple mismatch categories;
- exact engine/model/runtime fingerprints;
- FHIR validator output;
- evidence-report example;
- claims ledger;
- novelty map;
- literature search strategy;
- MI-CLAIM cross-check;
- reproducibility commands and hashes.

## Design rule

A result appears in exactly one main table/figure unless repetition is needed for orientation. Narrative text states the finding and interpretation rather than duplicating every numeric cell.
