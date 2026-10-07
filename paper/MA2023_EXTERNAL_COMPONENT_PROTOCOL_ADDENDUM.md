# Ma2023 External Component Protocol Addendum

Status: POST-OUTCOME AUDIT ADDENDUM — DOES NOT AMEND THE FROZEN PROTOCOL

This document records factual provenance corrections, implementation disclosures, and protocol/code deviations identified during pre-submission review. It does **not** alter the frozen cohort, thresholds, OCR outputs, component-pass rule, or primary endpoint.

## Dataset provenance correction

The 238 public laboratory-report images used in the external verifier-component study originate from the public dataset released with:

Xue W, Li Q, Xue Q. *Text Detection and Recognition for Images of Medical Laboratory Reports With a Deep Learning Approach*. IEEE Access. 2020;8:407-416. DOI: 10.1109/ACCESS.2019.2961964.

Ma et al. (2023) subsequently used and described this public collection as 238 de-identified Chinese laboratory-report images derived from 119 paper reports and captured by scanners and smartphones under varied illumination.

The Cohen's kappa value of 0.89 reported by Ma et al. applies to the separate PKU1 annotation exercise. It must not be attributed to the public 238-image collection. The available public source materials do not document whether the public collection's text/cell labels were created manually, OCR-assisted, or by another procedure.

## Frozen endpoint provenance

The numeric component endpoint was encoded before any Ma2023 verifier result existed.

- Prespecification commit: `47433ae8fb429671489ac530dfd05c95a82bfaf4`
- In that commit, `unsafe_component_pass` is defined as `component_pass and not value_exact`.
- Frozen result commit: `6f082d8dad6d576c8add7a5914609c68785ef665`

This endpoint is narrower than the manuscript's general definition of full-field correctness. The post-outcome analyte/value/unit tuple diagnostic remains exploratory and must not replace the frozen primary component endpoint.

## Oracle-localisation mechanics

The scoring implementation:

- evaluates laboratory table `table_no == 2`;
- excludes the header row;
- uses gold geometry only after OCR inference;
- matches OCR spans to a truth cell at a minimum truth-area overlap of 0.25;
- ranks eligible OCR candidates by overlap and then OCR confidence;
- uses gold text only for scoring, never as OCR input.

These mechanics mean the experiment is an oracle-localised verifier-component evaluation, not end-to-end extraction.

## Cohort flow and code/protocol deviation

The frozen scorer evaluated 2,219 candidate laboratory rows:

- 1,850 eligible rows;
- 275 excluded for unsupported gold values;
- 74 excluded for missing units;
- 13 excluded for ambiguous duplicate analyte/value/unit annotations;
- 4 excluded for missing values;
- 3 excluded for missing analytes.

Eligible rows came from 180/238 images; 58 images contributed no eligible row under the frozen table and eligibility rules.

The written frozen protocol states that unit-dependent analysis is restricted to rows with a non-empty unit. The implemented scorer requires a non-empty unit for the entire component estimand and therefore excludes 74 unitless rows before the numeric component analysis. This is a protocol/code deviation and is reported transparently; it is not corrected post hoc.

## Gate-overlap funnel

Descriptive overlap from the frozen row-level artifact:

- second-engine numeric agreement: 654/1,850;
- agreement + perturbation stability: 442/1,850;
- agreement + stability + valid unit syntax: 377/1,850;
- agreement + stability + unit-valid + structural association: 375/1,850;
- final component pass: 375/1,850.

This funnel is descriptive only and does not redefine any gate or endpoint.

## Pre-outcome runtime/integrity repairs

Three repairs occurred before a Ma2023 verifier outcome artifact existed:

1. JPEG source images were decoded and losslessly re-encoded as PNG solely to satisfy the existing crop contract.
2. OCR span page identity was rebound to the normalized PNG page hash without changing coordinates, text, confidence, engine identity, or fingerprint.
3. Thirteen rows with duplicate annotations in estimand-relevant cells were classified as reference non-evaluable fail-closed.

The chronology and qualification evidence remain recorded in `docs/evidence/MA2023_DELEGATED_OCR_REVIEW.md`.

## Interpretation boundary

The frozen result contains no primary-OCR numeric errors to intercept: primary numeric value exactness was 1,850/1,850. Therefore 0/375 incorrect numeric values among component passes cannot be interpreted as evidence that the gate reduced numeric error.

The post-outcome exploratory tuple diagnostic found 38/375 component passes with an analyte or unit mismatch. This result is useful for identifying the missing verification boundary but does not alter the frozen numeric endpoint.
