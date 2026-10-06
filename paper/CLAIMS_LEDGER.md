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
| Visual grounding of extracted clinical fields to source-image regions has prior art | supported | RAPTOR+ 2026 | Do not claim pixel/bounding-box grounding itself as novel |
| Source-grounded trust promotion for laboratory data has prior art | supported | Girda & Groza 2026 | Do not claim evidence gating itself as novel |
| Clinical text-to-FHIR and printed-form-to-FHIR have prior art | supported | SMART Text2FHIR; Werlitz et al. 2025 | Do not claim FHIR conversion itself as novel |
| Local frozen Tesseract on ClinOCR-Bench test had mean WER 0.5589 and median WER 0.5647 | supported | PAPER_CLINOCR_TESSERACT_WER.json | Call this a local frozen-runtime result, not an exact reproduction of the authors' environment |
| SafeOCR invented visual grounding for clinical document extraction | NOT SUPPORTED | RAPTOR+ evaluates source-image bounding-box grounding | Prohibited |
| SafeOCR invented evidence-gated trust promotion for laboratory extraction | NOT SUPPORTED | Girda & Groza 2026 | Prohibited |
| SafeOCR invented extraction-to-FHIR | NOT SUPPORTED | SMART Text2FHIR and printed-form-to-FHIR prior art | Prohibited |
| SafeOCR is the first system with this exact combination | INSUFFICIENT FOR ABSOLUTE FIRST CLAIM | broad multi-tool literature screen found no exact match but cannot prove universal absence | Describe a distinct integration/evaluation design; avoid "first" |
