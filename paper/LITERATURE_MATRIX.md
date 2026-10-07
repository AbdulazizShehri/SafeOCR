# SafeOCR Literature Matrix

This matrix is the manuscript's claim-control layer. It separates what prior work establishes from what SafeOCR may claim.

| Source | Domain / task | What it establishes | Relevance to SafeOCR | Limitation relative to SafeOCR |
|---|---|---|---|---|
| Xue et al., 2020, IEEE Access, DOI 10.1109/ACCESS.2019.2961964 | OCR for medical laboratory-report images | Original published source associated with the public laboratory-report image collection used in the external component study | Mandatory provenance citation for the external public image collection | Does not establish the SafeOCR verification contract or the provenance of every public text/cell label |
| Ma et al., 2023, BMC Medical Informatics and Decision Making, DOI 10.1186/s12911-023-02346-6 | OCR + information extraction from paper laboratory reports | Evaluates laboratory-report OCR/IE and describes the 238-image public collection as de-identified; separately reports a PKU1 clinical validation set | Closest direct laboratory-report predecessor and a secondary description of the public collection | Its reported Cohen's kappa of 0.89 belongs to the separate PKU1 annotation exercise and must not be attributed to the public 238-image labels |
| Laique et al., 2021, Gastrointestinal Endoscopy, DOI 10.1016/j.gie.2020.08.038 | OCR + NLP on scanned clinical reports | OCR/NLP can recover clinical quality variables from scanned records at scale | Supports the practical need for OCR before downstream NLP in legacy documents | Different document family; no field-level verification gate |
| Hsu et al., 2022, JAMIA Open, DOI 10.1093/jamiaopen/ooac045 | OCR + NLP on scanned EHR documents | Demonstrates pipeline sensitivity to preprocessing, OCR, layout and downstream NLP | Strong scanned-document systems comparator | Optimizes extraction performance rather than trust promotion/export gating |
| ClinOCR-Bench, 2026, arXiv:2607.03650 + official release | Synthetic/template-generated PHI-free clinical-document OCR benchmark | Provides 384 documents across normal, handwriting, poor-quality, rotation, table and mixed-artifact subsets | External transcription stress test for the two frozen OCR engines | Synthetic, mostly not laboratory reports, transcript truth only; does not exercise SafeOCR field-level gates |
| Li et al., 2024, Journal of Biomedical Informatics, DOI 10.1016/j.jbi.2024.104735 | Deep-learning table extraction from scanned laboratory reports | Shows table structure is a first-class laboratory-report extraction problem | Motivates explicit structural association | No selective trust states or verified-only export |
| Ren et al., 2025, DIGITAL HEALTH, DOI 10.1177/20552076251334431 | Digitization of image-based medical laboratory reports | Uses 330 image-based lab reports with layout analysis, text detection/recognition and serialized output | Direct lab-report digitization prior art | Focus is digitization/layout reconstruction rather than accepted-error verification |
| Wang et al., 2026, MLHC/PMLR 340 | Semi-structured extraction of OCR clinical reports | Large-scale extraction performance depends strongly on key coverage and OCR corruption | Strong modern heterogeneous-report comparator | Does not evaluate SafeOCR-style trust promotion or FHIR gating |
| Li et al., 2026, KSEM/Springer, DOI 10.1007/978-981-92-2864-5_12 | Semi-structured extraction from OCR clinical reports | Benchmarks key discovery, QA and extraction under OCR noise | Supports the heterogeneous-schema problem setting | Extraction capability rather than evidence-bound acceptance |
| Shang et al., 2026, ECCV/Springer, DOI 10.1007/978-3-032-37029-7_17 | Structured understanding of medical report images | Benchmarks report-image structured interpretation | Relevant to structure-aware document understanding | Not a selective-verification/provenance system |
| Abioye et al., RAPTOR, MICCAI 2025, DOI 10.1007/978-3-032-04981-0_47 | Clinical referral document extraction | Peer-reviewed clinical document-AI predecessor using generative AI and review/uncertainty concepts | Published anchor for contemporary clinical document AI | Different task and evidence contract; does not demonstrate SafeOCR's exact integration |
| Swaminathan et al., 2024, JAMIA, DOI 10.1093/jamia/ocad182 | Selective prediction for clinical abstraction | Shows value of abstention under asymmetric clinical abstraction costs | Direct conceptual support for review/abstention | Clinical-note setting rather than OCR evidence binding |
| Geifman & El-Yaniv, 2019, ICML/PMLR | Selective prediction / reject option | Formalizes risk-coverage trade-offs with rejection | Provides selective-prediction vocabulary | SafeOCR uses deterministic gates, not SelectiveNet |
| Angelopoulos et al., 2025, Annals of Applied Statistics, DOI 10.1214/24-AOAS1998 | Risk control | Formal finite-sample risk-control framework | Motivates calibration/evaluation discipline | SafeOCR v0.1 does not claim such a guarantee |
| Kim et al., 2025, AAAI Symposium Series, DOI 10.1609/aaaiss.v7i1.36929 | Conformal verification of EHR extraction | Verification of accepted structured extractions from text notes | Contemporary clinical verification precedent | Text-note/LLM extraction, not OCR |
| Daumke et al., 2019, MEDINFO, DOI 10.3233/SHTI190188 | Clinical text mining on FHIR | Connects text mining and FHIR interoperability, including provenance-related constructs | Supports downstream FHIR boundary | Not OCR verification |
| Miller et al., 2023, SMART Text2FHIR | Clinical NLP-to-FHIR | Demonstrates extraction-to-FHIR pipeline | Establishes extraction-to-FHIR as prior art | Starts from text rather than source pixels |
| Werlitz et al., 2025, Stud Health Technol Inform, DOI 10.3233/SHTI251392 | Printed forms to FHIR | Demonstrates transformation of printed care-transition records to FHIR | Directly narrows any document-to-FHIR novelty claim | Does not evaluate SafeOCR's selective verifier |
| Margheri et al., 2020, International Journal of Medical Informatics, DOI 10.1016/j.ijmedinf.2020.104197 | Healthcare provenance | Healthcare provenance infrastructure using blockchain/W3C-PROV concepts | Supports the need for traceability broadly | Must not be cited as proof specifically of FHIR Provenance |
| Ben Hmida et al., 2025, INISTA, DOI 10.1109/INISTA68122.2025.11249647 | Ontology-constrained OCR with abstention | Shows OCR validation can integrate semantic constraints and abstention | Adjacent verification/abstention precedent | Financial/administrative rather than clinical |
| HL7 FHIR R4 | Interoperability standard | Defines FHIR R4 resources and Provenance | Normative basis for SafeOCR export representation | Conformance does not establish extraction correctness |

## Internal novelty surveillance — not automatically JAMIA references

The following preprints remain useful for conservative novelty surveillance but should not automatically appear in a JAMIA reference list while they remain neither published nor in press:

- Girda & Groza, 2026, *Review Before Trust* (arXiv:2608.29965): close conceptual overlap in source-grounded laboratory-data trust promotion, same-row evidence, provenance and review retention.
- RAPTOR+, 2026 (arXiv:2605.25956): visually grounded clinical extraction with value-plus-source-box safety metrics.
- ClinOCR-Bench manuscript (arXiv:2607.03650): use the official dataset/release citation for JAMIA if no eligible publication exists at submission.

These works still constrain what SafeOCR may call novel even when journal reference-policy rules require a different formal citation strategy.

## Synthesis

Four mature lines intersect:

1. clinical document OCR and structured extraction;
2. selective prediction and abstention;
3. extraction verification and risk control;
4. FHIR/interoperability and provenance.

SafeOCR should be positioned as a **specification, integration and evaluation-methodology contribution**, not as proof that any individual component is new and not as a demonstrated reduction in accepted error.

## Defensible novelty statement

SafeOCR specifies and evaluates a healthcare OCR verification contract combining source-region binding, a second OCR engine on the bounded critical crop, perturbation-consistency checks, structural and patient/document linkage gates, explicit clinical criticality, selective decision states, governed accepted-error/coverage reporting, and FHIR export blocked for non-verified fields.

The current v0.1 evidence does **not** demonstrate the marginal risk-reduction benefit of these additions because both frozen primary safety endpoints contained zero primary-OCR errors.

## Claims that must remain withheld

- SafeOCR reduced accepted error relative to the primary OCR baseline in v0.1.
- Zero observed unsafe accepts implies zero underlying risk.
- ClinOCR-Bench provides field-level SafeOCR safety validation.
- The public 238-image collection has a documented dual-human label standard with kappa 0.89.
- FHIR validator conformance equals measured FHIR mapping correctness.
- SafeOCR is clinically deployment-ready or medically validated.
- Any universal "first" claim.
