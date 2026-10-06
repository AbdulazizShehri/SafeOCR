# SafeOCR JAMIA Submission Metadata

## Manuscript type

Research and Applications

## Working title

SafeOCR: Evidence-Grounded Selective Verification for Clinical OCR with Provenance-Preserving FHIR Export

## Short title

SafeOCR for Selective Clinical OCR Verification

## Data availability

The primary SafeOCR-LabGold evaluation uses PHI-free synthetic data generated under the repository's frozen benchmark specification. ClinOCR-Bench is a publicly available PHI-free external OCR benchmark and is cited at its upstream release. The Ma et al. 2023 laboratory-report dataset is used as an external research dataset without redistribution by SafeOCR; users should obtain it from the original authors' public repository/source subject to the upstream terms. SafeOCR publishes only derived evaluation artifacts, hashes, protocols, and code required to reproduce the analyses where redistribution rights permit.

Final wording must be reconciled with the exact public release state at submission.

## Code availability

SafeOCR source code, frozen evaluation protocols, deterministic scoring code, evidence artifacts, and reproducibility instructions will be available from the public SafeOCR repository associated with the manuscript. The release must identify the exact commit/tag used for the paper and retain dependency/runtime fingerprints.

Submission requirement:
- insert canonical public repository URL;
- insert paper release/tag;
- insert archival DOI if Zenodo or another archive is created before submission.

## Ethics statement

The public v0.1 study does not require real protected health information in the SafeOCR-LabGold or ClinOCR-Bench analyses. The external Ma et al. dataset is described by its source publication as de-identified and is used only for research evaluation. SafeOCR does not redistribute those source images.

Before submission, confirm whether the target journal requires an explicit institutional determination/exemption statement for secondary analysis of the external public dataset. Do not infer or fabricate an IRB determination.

## Clinical safety statement

SafeOCR v0.1 is research software. It is not a medical device, diagnostic system, or treatment recommendation system and has not been prospectively validated for unsupervised clinical use. REVIEW_REQUIRED and ABSTAINED outputs are intentionally blocked from automated FHIR export.

## Funding

[TBD — insert only verified funding/sponsorship relevant to this research.]

Do not infer that an educational scholarship or unrelated sponsorship funded the study unless it actually supported this work.

## Competing interests

[TBD — author must confirm.]

If none:
"The author(s) declare no competing interests."

Use only after explicit author confirmation.

## Author contributions / CRediT

Populate only after the final author list is known.

Potential roles to assign explicitly:
- Conceptualization
- Methodology
- Software
- Validation
- Formal analysis
- Investigation
- Data curation
- Writing — original draft
- Writing — review & editing
- Visualization
- Supervision
- Project administration
- Funding acquisition, if applicable

Do not assign roles to any person without confirmation.

## AI-assisted work disclosure

Draft disclosure, subject to the exact JAMIA policy in force on the submission date:

"Generative AI tools were used during software development and manuscript preparation for drafting assistance, code generation/review, literature-discovery support, and language editing. All scientific claims, citations, code changes, analyses, and manuscript text were reviewed and verified by the human author(s). AI systems were not listed as authors and did not determine authorship, research accountability, or final scientific conclusions."

Before submission:
- verify the current journal wording and location for disclosure;
- name tools/models only if required by the journal;
- distinguish literature discovery from evidence sources;
- ensure no citation is included solely because an AI tool suggested it;
- ensure every quantitative result is traceable to a frozen SafeOCR artifact.

## Acknowledgements

[TBD.]

Do not acknowledge tools as authors.

## Reproducibility statement

The manuscript should identify:
- SafeOCR paper release/tag;
- exact Git commit;
- Python version;
- PaddleOCR version/models/backend;
- Tesseract version;
- HL7 validator version;
- ClinOCR-Bench release and hash;
- Ma2023 annotation SHA-256;
- final evidence-artifact hashes;
- platform/hardware used for the reference run where relevant.

## Suggested keywords

- optical character recognition
- clinical informatics
- laboratory reports
- selective prediction
- abstention
- provenance
- FHIR
- patient safety
- document AI
- information extraction

## Cover-letter core message

SafeOCR should be presented as a health-informatics safety and evaluation contribution, not a new OCR model.

The cover letter should emphasize:
1. a fail-closed verification contract between OCR and structured clinical data;
2. explicit accepted-error versus automation-coverage evaluation;
3. source-level provenance and independent verification;
4. verification-gated FHIR interoperability;
5. transparent negative results and no superiority overclaim;
6. independent public external OCR evaluation;
7. real de-identified laboratory-report verifier-component evaluation, if the frozen Ma2023 experiment completes successfully;
8. public reproducibility artifacts.
