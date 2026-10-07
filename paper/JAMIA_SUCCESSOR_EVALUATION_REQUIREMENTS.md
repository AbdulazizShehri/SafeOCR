# JAMIA Successor Evaluation Requirements

Status: DESIGN REQUIREMENTS ONLY — NOT A FROZEN PROTOCOL

This document defines what a new study must accomplish before SafeOCR makes a claim that verification reduces accepted field error. It intentionally does not freeze a dataset or analysis until an appropriate previously uninspected dataset is verified.

## Why a successor study is required

The current frozen safety endpoints contain no primary-OCR events to intercept:

- SafeOCR-LabGold primary OCR: 0/288 endpoint errors.
- Public laboratory-report component study: 0/1,850 primary numeric-value errors.

Therefore the current evidence can evaluate implementation, coverage cost, review burden, failure handling, and full-tuple diagnostic weaknesses, but it cannot estimate a reduction in accepted error attributable to the verification gate.

## Dataset requirements

A candidate dataset must be screened for suitability **without inspecting SafeOCR outcome metrics** and must satisfy all of the following before protocol freeze:

1. previously uninspected by the SafeOCR study;
2. lawful research access and clear redistribution/citation terms;
3. clinical document images, preferably laboratory reports;
4. source-region or field-level annotations sufficient for end-to-end scoring;
5. analyte/test identity, value, and unit/reference semantics available or independently adjudicable;
6. enough difficult image conditions to make a non-trivial primary-OCR field error rate plausible;
7. patient/document linkage truth if that endpoint will be claimed;
8. no use of SafeOCR outputs to create the gold standard.

Synthetic-only data may support stress testing but must not be the sole external evidence for a JAMIA risk-reduction claim.

## Primary endpoint candidate

The preferred primary field endpoint for a new study is **full analyte-value-unit tuple correctness among automatically accepted fields**, with an error defined whenever any clinically meaning-changing tuple component or association is incorrect.

Numeric-only correctness may be reported as a secondary endpoint but must not replace full-field correctness.

## Primary comparison

The study must compare, on identical evaluable fields:

- ungated primary OCR/extraction;
- SafeOCR frozen acceptance policy;
- review/rejection burden;
- errors intercepted by the gate;
- errors remaining among accepted fields.

The key quantities are:

- baseline endpoint error count/rate;
- accepted endpoint error count/rate;
- number and fraction of baseline errors intercepted;
- verified coverage;
- review/abstention burden;
- false-review burden.

A gate cannot be described as risk-reducing if the baseline has no endpoint errors.

## Independence and localisation

The preferred study is end-to-end and does not use gold geometry to propose fields.

If an oracle-localised secondary analysis is included, it must be explicitly separated from the end-to-end primary analysis.

## Statistics

Before outcome inspection, freeze:

- unit of analysis;
- clustering unit (document/patient/site);
- paired comparisons;
- confidence-interval method;
- handling of zero-event strata;
- multiplicity/secondary endpoints;
- missing data/runtime failure rules.

Cluster-aware uncertainty should be used when multiple fields arise from the same document or paired acquisition.

## Runtime failures

Runtime failures are first-class outcomes.

The protocol must prespecify whether they:
- count as abstentions;
- count as extraction failures;
- remain in coverage denominators;
- trigger review.

They must never be silently dropped.

## Comparator requirement

At least one contemporary document-AI/VLM comparator should be considered if licensing, compute cost, and reproducibility permit. If omitted, the manuscript must justify the omission in relation to the study question rather than imply that classical OCR is the current performance frontier.

## Governance

Before any target outcome is inspected:

1. freeze the dataset manifest and hashes;
2. freeze eligibility and exclusions;
3. freeze engine/model revisions;
4. freeze preprocessing;
5. freeze the endpoint and matching rules;
6. freeze runtime-failure handling;
7. commit the protocol;
8. qualify runner/scorer leakage boundaries;
9. record exact git head and clean-tree state.

No post-outcome threshold or cohort retuning is permitted.

## Candidate-source screening

Potential sources may be investigated for licensing and annotation suitability, but **do not execute SafeOCR on them until a source is selected and the protocol is frozen**.

The source-selection audit should explicitly record why rejected candidates were unsuitable, preventing outcome-driven dataset selection.
