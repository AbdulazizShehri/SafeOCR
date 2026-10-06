# Manuscript Highlights

- SafeOCR treats clinical OCR output as an untrusted proposal rather than an automatically exportable datum.
- Critical laboratory fields require source-pixel grounding, structural checks, an independent OCR-family reread, perturbation stability, valid parsing, patient linkage, and healthy runtime before automatic acceptance.
- The frozen v0.1 policy automatically verified 209 of 288 synthetic critical-field cases (72.57% coverage) with zero observed unsafe accepts; the 95% Wilson upper bound was 1.805%.
- The raw primary OCR baseline also observed zero errors at 100% coverage, so the study does not claim SafeOCR superiority from the synthetic benchmark.
- Verified fields may enter a provenance-preserving FHIR R4 export path; review-required and abstained fields are mechanically blocked from automatic export.
- External ClinOCR-Bench OCR generalization is preregistered and executed zero-shot without tuning the SafeOCR policy.
