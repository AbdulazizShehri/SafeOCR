# SafeOCR Manuscript Claims Ledger

| Claim | Status | Evidence / citation | Allowed wording |
|---|---|---|---|
| OCR can digitize paper/scanned clinical reports | supported | Ma 2023; Laique 2021 | Strong background claim |
| Laboratory reports contain heterogeneous layouts and mixed text/numeric/unit structure | supported | Ma 2023 | Strong background claim |
| Selective prediction can improve clinical data abstraction when abstention is allowed | supported | Swaminathan et al. | Strong related-work claim |
| Risk/coverage is a standard selective-prediction framing | supported | Geifman & El-Yaniv | Strong methods framing |
| Formal risk-control methods exist without model refitting | supported | Angelopoulos et al. | Strong related-work claim; do not attribute a formal guarantee to SafeOCR |
| Conformal verification has been applied to clinical EHR extraction | supported | Kim et al. | Strong related-work claim |
| FHIR can represent provenance/source relationships | supported | HL7 R4; Daumke 2019; Margheri 2020 | Strong interoperability claim |
| SafeOCR accepted 209/288 critical fields | supported | F6_FINAL_EVALUATION.json | Exact quantitative claim |
| SafeOCR verified coverage was 72.57% | supported | F6_FINAL_EVALUATION.json | Exact quantitative claim |
| SafeOCR observed zero unsafe accepts | supported | F6_FINAL_EVALUATION.json | Must say "observed" |
| SafeOCR UAR 95% Wilson upper bound was 1.805% | supported | F6_FINAL_EVALUATION.json | Exact quantitative claim |
| Raw primary OCR observed zero errors at full coverage on LabGold | supported | F6_FINAL_EVALUATION.json | Must be prominently reported |
| SafeOCR outperformed primary OCR | NOT SUPPORTED | primary OCR was perfect on frozen synthetic final set | Prohibited |
| SafeOCR has zero risk | NOT SUPPORTED | finite sample; interval non-zero | Prohibited |
| SafeOCR is clinically deployment-ready | NOT SUPPORTED | no prospective/real-world clinical validation | Prohibited |
| FHIR mapping error rate was zero | NOT SUPPORTED | F6 did not estimate field-level FHIR mapping error | Prohibited |
| FHIR validator passed the canonical valid bundle with zero errors | supported | F5_RUNTIME_SMOKE.json | Conformance claim only |
| ClinOCR-Bench supports SafeOCR field-level safety metrics | NOT SUPPORTED | transcript truth lacks required field/patient/FHIR labels | Prohibited in v0.1 |
| SafeOCR is the first system to combine all four design components | INSUFFICIENT FOR ABSOLUTE FIRST CLAIM | current literature screen found no direct match | Phrase as "our review did not identify..." |
