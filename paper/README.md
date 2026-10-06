# SafeOCR Manuscript Workspace

Working title: **SafeOCR: Evidence-Grounded Selective Verification for Clinical OCR with Provenance-Preserving FHIR Export**

## Target paper type

Methods / evaluation paper in clinical informatics.

## Core contribution

SafeOCR is not presented as a new OCR recognizer. It is a healthcare-only verification layer that treats OCR output as an untrusted proposal and allows automatic structured export only when a critical field is bound to source evidence and passes deterministic verification gates.

## Non-negotiable claims policy

- Do not claim clinical deployment readiness.
- Do not claim superiority over raw primary OCR from LabGold.
- Do not convert zero observed errors into zero risk.
- Do not claim FHIR mapping error-rate evidence from the F6 benchmark when the frozen artifact did not estimate that quantity.
- Do not claim ClinOCR-Bench structured critical-field performance from transcript-only ground truth.
- Do not use final-evaluation data for threshold tuning.
- Distinguish FHIR conformance evidence from clinical extraction correctness.

## Primary quantitative result

On the frozen SafeOCR-LabGold final set (48 documents / 288 critical-field cases), SafeOCR:
- accepted 209 / 288 fields;
- verified coverage: 72.57%;
- review rate: 27.43%;
- observed unsafe accepts: 0;
- unsafe accept rate: 0.0;
- 95% Wilson upper bound: 1.805%.

The raw primary OCR baseline also observed zero accepted errors at full coverage on this synthetic final set. Therefore the paper must not claim that LabGold establishes superiority over the primary OCR baseline.

## Literature workflow

Sources are screened into:
1. clinical OCR and laboratory-report extraction;
2. public clinical OCR benchmarks;
3. selective prediction / reject-option methods;
4. uncertainty and verification in clinical extraction;
5. interoperability, provenance, and clinical-IE reporting.

Every substantive literature claim in the manuscript must map to LITERATURE_MATRIX.md and references.bib.
