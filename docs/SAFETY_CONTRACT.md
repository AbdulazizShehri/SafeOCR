# SafeOCR Safety Contract

This document defines non-negotiable invariants for SafeOCR v0.1.

## Core principle

SafeOCR is a selective verification gateway. It may reduce automation to preserve evidence quality. It must never fabricate certainty to increase throughput.

## Invariants

### S-01 No evidence, no automatic export

Every automatically exported structured clinical field must map to source pixels through an immutable evidence record.

### S-02 Missing is not negative

A missing, unreadable, unsupported, or unresolvable field is never converted to a negative finding, zero value, normal value, or absent condition.

### S-03 Plausibility cannot rewrite pixels

Clinical knowledge and terminology may veto, flag, or route an extraction to review. They may not silently substitute a value that looks clinically more plausible.

### S-04 Agreement is not proof

Multi-engine agreement is one verification signal. It is insufficient by itself because engines may share training data, architecture, preprocessing, or correlated failure modes.

### S-05 Critical disagreement blocks automation

For critical fields, unresolved disagreement, instability, uncertain table association, or uncertain patient linkage prevents automatic FHIR export.

### S-06 Engine output is untrusted

OCR/VLM output is treated as untrusted data. Document text cannot override SafeOCR policy, invoke tools, grant network access, or alter verification thresholds.

### S-07 Patient attribution is critical

SafeOCR must not attach extracted clinical data to a patient when document identity is ambiguous or conflicting.

### S-08 Association correctness is part of correctness

A correctly read number attached to the wrong analyte, patient, date, unit, or table column is incorrect.

### S-09 Review output is evidence-preserving

v0.1 does not resolve human review. REVIEW_REQUIRED artifacts preserve the original candidate, source evidence, failed gates, and machine uncertainty for a future audited review workflow.

### S-10 Verified fields only

REVIEW_REQUIRED and ABSTAINED fields do not enter automatic clinical FHIR output.

### S-11 Reproducible acceptance

Every VERIFIED_AUTO decision records the exact source hash, engine/model versions, transforms, policy version, and evidence needed to reproduce it.

### S-12 No hidden inference

SafeOCR may normalize representations but may not infer absent dose, unit, result, date, diagnosis, or treatment intent.

### S-13 No unsupported FHIR semantics

SafeOCR v0.1 exports laboratory semantics only. Unsupported document families or uncertain report semantics must not be coerced into a FHIR resource type.

### S-14 No clinical-use claim from synthetic evidence

Synthetic/public benchmark performance is evidence of system behavior under those conditions, not evidence of clinical effectiveness or regulatory fitness.

### S-15 Observed zero is not guaranteed zero

If evaluation observes no unsafe accepted errors, reporting must state the sample size and confidence interval and must not claim zero real-world risk.

## Threat model

SafeOCR v0.1 explicitly considers:

- visually unsupported OCR/VLM generation;
- decimal, sign, exponent, and unit errors;
- row/column drift;
- cross-page table association errors;
- patient misattribution;
- conflicting duplicate values;
- overwritten or struck-through values;
- low-resolution/fax/compression artifacts;
- correlated OCR-engine failures;
- prompt injection embedded in document text;
- malicious/oversized PDFs and resource exhaustion;
- dependency/model drift;
- accidental PHI leakage through logs or telemetry;
- FHIR resource-type semantic mistakes.

## Fail-safe behavior

When evidence is insufficient, the correct SafeOCR behavior is REVIEW_REQUIRED or ABSTAINED.

Abstention is an intended output, not an exception path.

## Change control

Any change to:
- criticality rules;
- verification hard gates;
- automatic-export conditions;
- FHIR mapping semantics;
- benchmark labels;
- metric definitions

requires:
1. an explicit version change;
2. regression evaluation;
3. rationale in repository history;
4. no retroactive rewriting of prior benchmark evidence.

### S-16 Fail closed

Any unhandled verification error, missing mandatory verifier, invalid evidence manifest, or failed FHIR validation blocks automatic export.

### S-17 Benchmark separation

Final evaluation examples, templates, and corruption seeds must not be used to tune automatic-acceptance policy.

### S-18 Confidence is not probability

Engine-native OCR confidence must not be described as calibrated clinical correctness probability unless separately calibrated and validated.
