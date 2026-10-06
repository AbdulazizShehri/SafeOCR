# SafeOCR v0.1.0 Release Notes

SafeOCR v0.1.0 is the first research release of a healthcare-only,
evidence-grounded verification layer for laboratory-report OCR.

## What v0.1 does

SafeOCR treats OCR output as an untrusted proposal. A critical laboratory field
can reach automatic FHIR R4 export only when it is tied to source pixels and
passes the frozen verification policy. Otherwise it is routed to review or
abstention.

The reference path is CPU-first and uses:

- PaddleOCR 3.7.0 for full-page OCR/layout proposals;
- Tesseract 5.4.0.20240606 for independent critical-crop rereads;
- UCUM validation as a veto-only unit check;
- HMAC-SHA256 patient-linkage binding;
- HL7 FHIR R4 export with official validator evidence.

## Frozen evaluation result

On the preregistered SafeOCR-LabGold final set (48 documents / 288 fields):

| Method | Verified coverage | Unsafe accept rate |
| --- | ---: | ---: |
| Primary OCR | 100.00% | 0.00% observed |
| Tesseract crop | 99.65% | 15.68% |
| Naive agreement | 84.03% | 0.00% observed |
| SafeOCR | 72.57% | 0.00% observed |

SafeOCR accepted 209 fields with zero observed unsafe accepts. Its 95% Wilson
upper bound for unsafe accept rate is 1.805%.

This result is intentionally interpreted conservatively: because the raw
primary OCR baseline also observed zero accepted errors at full coverage on
this synthetic final set, the benchmark does not establish SafeOCR superiority
over that baseline. Zero observed errors is not zero risk.

## External benchmark integration

ClinOCR-Bench v1.0 metadata is pinned and validated without using its evaluation
outcomes for threshold tuning. SafeOCR does not claim structured critical-field
performance on ClinOCR-Bench because its public v1.0 ground truth is a
full-document transcript rather than SafeOCR field/patient/FHIR annotations.

## Evidence

The release includes canonical evidence for:

- OCR runtime identity and model hashes;
- verification/runtime controls;
- FHIR R4 validator output;
- the governed F6 primary evaluation;
- ClinOCR-Bench metadata integrity;
- deterministic risk/coverage operating points;
- a self-contained static evidence report with source crop provenance.

## Safety boundary

SafeOCR is research software. It is not a medical device and must not be used
for diagnosis, treatment decisions, or unsupervised clinical care. It does not
infer missing facts or clinically correct source text.
