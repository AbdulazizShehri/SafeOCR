# SafeOCR Manuscript Claims Ledger

| Claim | Status | Evidence / citation | Allowed wording |
|---|---|---|---|
| OCR can digitize paper/scanned clinical reports | supported | Ma 2023; Hsu 2022; Li 2024 | Strong background claim |
| Laboratory reports contain heterogeneous layouts and mixed text/numeric/unit structure | supported | Ma 2023 | Strong background claim |
| Selective prediction can improve clinical data abstraction when abstention is allowed | supported | Swaminathan et al. | Strong related-work claim |
| Risk/coverage is a standard selective-prediction framing | supported | Geifman & El-Yaniv | Strong methods framing |
| Formal risk-control methods exist without model refitting | supported | Angelopoulos et al. | Strong related-work claim; do not attribute a formal guarantee to SafeOCR |
| Conformal verification has been applied to clinical EHR extraction | supported | Kim et al. | Strong related-work claim |
| FHIR provides standardized interoperability structures and explicit Provenance resources | supported | HL7 R4; Daumke 2019 | Strong interoperability claim; do not imply provenance establishes OCR correctness |
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


| External component evaluated 1,850 eligible analyte-value-unit rows from 238 public laboratory-report images described as de-identified by Ma et al. | supported | PAPER_MA2023_EXTERNAL_VERIFIER.json; Xue 2020; Ma 2023 | Attribute image source to Xue and de-identification description to Ma; oracle-localised verifier-component claim only |
| Ma2023 component passed 375/1,850 eligible rows (20.27%) | supported | PAPER_MA2023_EXTERNAL_VERIFIER.json | Exact quantitative component-coverage claim |
| No Ma2023 component-passed row had an incorrect numeric value (0/375; 95% Wilson upper bound 1.014%) | supported | PAPER_MA2023_EXTERNAL_VERIFIER.json | Must say numeric value / component pass; not full-field safety |
| Ma2023 primary OCR numeric value was exact in 1,850/1,850 oracle-localised eligible rows | supported | PAPER_MA2023_EXTERNAL_VERIFIER.json | Oracle-localised OCR-value claim only |
| Ma2023 full analyte-value-unit tuple was exact in 1,461/1,850 primary OCR rows | supported | PAPER_MA2023_EXTERNAL_VERIFIER.json | Full-tuple descriptive result before component acceptance |
| Among 375 component passes, 337 full tuples were exact; 38 were inexact (36 analyte, 2 unit mismatches) | exploratory supported | PAPER_MA2023_PASS_DIAGNOSTIC.json | Explicitly label post-outcome exploratory diagnostic |
| Ma2023 proves SafeOCR full-field safety | NOT SUPPORTED | component endpoint checks incorrect numeric values; 38 passed tuples were not exact | Prohibited |
| Ma2023 is end-to-end extraction validation | NOT SUPPORTED | gold geometry is used after OCR for oracle-localised scoring | Prohibited |
| Ma2023 validates patient linkage or FHIR mapping | NOT SUPPORTED | excluded from claim boundary | Prohibited |


## Post-Opus claim-control additions

| Claim | Status | Evidence / citation | Allowed wording |
|---|---|---|---|
| LabGold provides evidence that SafeOCR reduced accepted error relative to primary OCR | NOT SUPPORTED | primary OCR 0/288 errors; SafeOCR 0/209 errors | Prohibited; report review cost and non-discrimination |
| LabGold primary OCR 0/288 has a 95% Wilson upper bound of 1.316% | supported | F6_FINAL_EVALUATION.json | Report beside SafeOCR 1.805% bound |
| All 79 SafeOCR LabGold reviews were correct under benchmark truth | supported | primary OCR exact 288/288; SafeOCR accepted 209/288 | Report as review burden / false-alarm cost on this endpoint |
| Public 238-image laboratory-report collection originated with Xue et al. 2020 | supported | Xue 2020 DOI 10.1109/ACCESS.2019.2961964; Ma 2023 data description | Attribute dataset source to Xue |
| Ma et al. kappa=0.89 describes the public 238-image labels | NOT SUPPORTED | Ma 2023 annotation section concerns PKU1 | Prohibited |
| Public collection label-generation provenance is documented | NOT SUPPORTED | audited public source materials do not describe label-generation procedure | State as undocumented |
| PaddleOCR ClinOCR run had 57/328 runtime failures | supported | PAPER_CLINOCR_PADDLEOCR_WER.json run_metadata.failures | Must be prominent; 33 rotated + 24 mixed |
| ClinOCR-Bench is a real clinical corpus | NOT SUPPORTED | benchmark is synthetic/template-generated and PHI-free | Call synthetic/template-generated clinical-document benchmark |
| Ma2023 numeric component gate reduced numeric error | NOT SUPPORTED | primary value exact 1,850/1,850; component pass 0/375 errors | Prohibited; endpoint had no errors to intercept |
| Ma2023 ungated 0/1,850 numeric errors has 95% Wilson upper bound 0.207% | supported | frozen counts + Wilson calculation | Report beside gated 1.014% bound |
| All 1,475 Ma2023 numeric-endpoint rejections were correct numeric values | supported | 1,850 eligible - 375 passes; primary_value_exact 1,850 | Report as rejection cost on numeric endpoint |
| 38/375 component passes had analyte or unit mismatch | exploratory supported | PAPER_MA2023_PASS_DIAGNOSTIC.json | Lead with 10.13%; label post-outcome exploratory |
| Numeric component endpoint was encoded before outcome generation | supported | commit 47433ae; result frozen later at 6f082d8 | Use to defend prespecification; do not reclassify endpoint |
| SafeOCR evaluation was externally preregistered | NOT SUPPORTED | internal version-controlled protocol commits only | Use "prespecified, commit-timestamped" |


## Dependence and follow-up claim controls

| Claim | Status | Evidence / citation | Allowed wording |
|---|---|---|---|
| Field-level Wilson intervals are cluster-robust population guarantees | NOT SUPPORTED | repeated fields within LabGold documents/record pairs and external images | Prohibited |
| LabGold post-outcome document-level sensitivity is 0/48 error-containing documents (Wilson upper 7.41%) | descriptive supported | frozen F6 result aggregated at document level | Must label post-outcome descriptive dependence sensitivity |
| LabGold post-outcome record-pair sensitivity is 0/24 error-containing records (Wilson upper 13.80%) | descriptive supported | frozen split structure + F6 result | Must label post-outcome descriptive dependence sensitivity |
| Ma2023 component passes arose from 86 images with 0/86 images containing an incorrect accepted numeric value (Wilson upper 4.28%) | descriptive supported | frozen row-level verifier artifact | Must label post-outcome descriptive cluster sensitivity; does not redefine field-level endpoint |
| ClinOCR paired PaddleOCR-minus-Tesseract mean WER difference was -0.0820 with fixed-seed bootstrap interval -0.1204 to -0.0442 | descriptive supported | frozen paired per-document WER artifacts | Descriptive sensitivity only; failures remain scored empty under frozen policy |
| On the 271 ClinOCR documents without a PaddleOCR runtime failure, mean WER was 0.3668 for PaddleOCR vs 0.5358 for Tesseract | descriptive supported | frozen paired per-document WER artifacts | Label non-failed sensitivity; never use to replace the all-document primary result |
| Current v0.1 evidence demonstrates SafeOCR intercepts primary-OCR full-tuple errors | NOT SUPPORTED | frozen safety endpoints contain no baseline events | Prohibited |
| RJUA-MedDQA is already qualified as the JAMIA final dataset | NOT SUPPORTED | metadata qualification only; annotation sufficiency unresolved; no SafeOCR outputs inspected | Prohibited |
| A new JAMIA follow-up study may be run under the current draft protocol without first freezing it | NOT SUPPORTED | protocol status is DRAFT | Prohibited; freeze protocol, qualification, manifest, gold schema and scorer before final-set execution |
