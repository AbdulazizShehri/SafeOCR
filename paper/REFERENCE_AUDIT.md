# SafeOCR Reference Audit

Audit date: 2026-10-07

Bibliographic metadata and claim fit were checked against publisher pages, PubMed/PMC, PMLR, Springer proceedings, IEEE metadata where available, arXiv/official benchmark releases, and the normative HL7 FHIR R4 specification. Discovery-engine output is not treated as bibliographic authority.

## Submission-critical corrections

| Key | Status | Submission note |
|---|---|---|
| xue2020labocr | verified published | Original published source associated with the public laboratory-report image collection; mandatory provenance citation. DOI 10.1109/ACCESS.2019.2961964. |
| ma2023labocr | verified published | BMC MIDM 2023. May describe the public collection as de-identified, but its reported kappa=0.89 must be attributed only to the separate PKU1 annotation exercise. |
| hsu2026clinocr | verified arXiv/release | Synthetic/template-generated PHI-free benchmark. For JAMIA, cite the official dataset/repository as an electronic dataset/resource if no published/in-press paper exists at submission. |
| abioye2025raptor | verified published | MICCAI 2025, LNCS 15966, pp. 495-505, DOI 10.1007/978-3-032-04981-0_47. Published anchor for contemporary clinical document AI. |
| abioye2026raptorplus | verified preprint | Internal novelty surveillance only unless publication status changes; do not rely on it as a formal JAMIA reference while arXiv-only. |
| girda2026review | verified preprint | Close conceptual prior art; retain for novelty surveillance, but JAMIA formal-reference eligibility must be confirmed before submission. |

## Published / normative references

| Key | Identifier / venue | Audit status |
|---|---|---|
| laique2021ocrnlp | DOI 10.1016/j.gie.2020.08.038 | verified published |
| swaminathan2024selective | DOI 10.1093/jamia/ocad182 | verified published |
| geifman2019selectivenet | PMLR 97:2151-2159 | verified published |
| angelopoulos2025learntest | DOI 10.1214/24-AOAS1998 | verified published; do not imply SafeOCR has this guarantee |
| kim2025conformalEHR | DOI 10.1609/aaaiss.v7i1.36929 | verified published; text-note/LLM extraction rather than OCR |
| daumke2019fhir | DOI 10.3233/SHTI190188 | verified published; author accent normalized to Martínez-Costa |
| margheri2020provenance | DOI 10.1016/j.ijmedinf.2020.104197 | verified published; healthcare provenance broadly, not specific proof of FHIR Provenance |
| li2026medstructs | DOI 10.1007/978-981-92-2864-5_12 | verified published online for KSEM 2026; LNCS 16636, pp. 131-141. Springer volume also carries 2027 copyright metadata, so year should be rechecked at final export |
| shang2026medrepbench | DOI 10.1007/978-3-032-37029-7_17 | verified published, ECCV 2026, LNCS 17074, pp. 282-298 |
| hsu2022scanned | DOI 10.1093/jamiaopen/ooac045 | verified published |
| benhmida2025ontology | DOI 10.1109/INISTA68122.2025.11249647 | verified conference paper, pp. 1-5; non-clinical OCR context |
| ren2025serialization | DOI 10.1177/20552076251334431 | verified published, DIGITAL HEALTH 11, article 20552076251334431; 330 image-based lab reports |
| li2024tabular | DOI 10.1016/j.jbi.2024.104735 | verified published |
| wang2026keycoverage | PMLR 340:2109-2130 | verified published |
| miller2023smarttext2fhir | PMID 38222416 / PMCID PMC10785871 | verified published; no DOI required |
| werlitz2025printedfhir | DOI 10.3233/SHTI251392 | verified published, Stud Health Technol Inform 331:162-169 |
| schafer2025transfusion | DOI 10.1109/EMBC58623.2025.11254237 | verified published, pp. 1-7; author diacritics normalized where supported |
| norgeot2020miclaim | DOI 10.1038/s41591-020-1041-y | verified published, Nat Med 26(9):1320-1324 |
| vasey2022decideai | DOI 10.1038/s41591-022-01772-9 | verified published, Nat Med 28(5):924-933; not a direct governing guideline for this preclinical systems study |
| hl7fhirr4 | HL7 FHIR R4 v4.0.1 | normative standard |

## Preprints / non-final publication status

| Key | Status | Handling |
|---|---|---|
| hsu2026clinocr | arXiv 2607.03650 + official benchmark release | arXiv paper may remain in the preprint bibliography; JAMIA should use the dataset/repository citation if policy requires published/in-press papers only |
| girda2026review | arXiv 2608.29965 | novelty surveillance; verify proceedings/publication status immediately before journal submission |
| abioye2026raptorplus | arXiv 2605.25956 | novelty surveillance; use published RAPTOR as formal peer-reviewed anchor |
| ajayi2025uncertainty | arXiv 2507.02009 | currently not needed for a core manuscript claim; drop from final journal bibliography unless cited and publication status is eligible |

## Claim-fit corrections

- Xue 2020, not Ma 2023, is the original source citation for the public lab-image collection.
- Ma 2023 must not be cited as evidence that the public collection had dual-human annotation with kappa=0.89.
- Margheri 2020 supports healthcare provenance broadly; it should not be described as direct evidence for the FHIR Provenance resource.
- Ben Hmida 2025 is adjacent OCR/abstention prior art, not a clinical OCR study.
- Kim 2025 is clinical EHR text extraction, not OCR.
- ClinOCR-Bench is synthetic/template-generated and should not be called a real-world clinical corpus.
- RAPTOR MICCAI 2025 is a stronger formal peer-reviewed clinical document-AI reference than relying only on RAPTOR+.

## JAMIA policy boundary

The current JAMIA author instructions state that the formal reference list should contain papers that are published or in press, while public datasets should be fully referenced with identifiers. Therefore:

1. replace arXiv citations with versions of record whenever one exists;
2. cite ClinOCR-Bench as a dataset/electronic resource if no eligible paper version exists at submission;
3. keep arXiv-only novelty-surveillance works out of the formal journal list unless editorial policy permits them or their publication status changes;
4. rerun this audit immediately before submission.

## Remaining metadata gates

Before the final journal bibliography is frozen:

- confirm the final bibliographic year exported by Springer for MedStruct-S (online 2026; proceedings copyright metadata also shows 2027);
- confirm any updated published/in-press version of ClinOCR-Bench, Girda & Groza, RAPTOR+, and Ajayi;
- confirm full author lists if required by final journal style;
- run a final DOI-resolution and duplicate-key check.
