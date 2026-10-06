Dear Editors of the Journal of the American Medical Informatics Association,

Please consider our manuscript, “SafeOCR: Evidence-Grounded Selective Verification for Clinical OCR with Provenance-Preserving FHIR Export,” for publication as a Research and Applications article.

SafeOCR addresses a health-informatics problem that arises after optical character recognition: deciding when an extracted clinical field is sufficiently supported for automated downstream use. Rather than proposing a new OCR recognizer, SafeOCR treats OCR output as an untrusted proposal. Critical laboratory fields are bound to source regions and evaluated through deterministic gates that include structural association, an independent OCR-family reread, perturbation stability, numeric and unit checks, patient/document linkage, and runtime health. Fields that do not satisfy the frozen policy are routed to review or abstention; only verified fields may enter the FHIR R4 export path.

The manuscript emphasizes accepted-error risk together with automation coverage and reports negative evidence explicitly. On the frozen synthetic SafeOCR-LabGold final set, SafeOCR verified 209 of 288 critical fields (72.57% coverage) with no observed unsafe accepts (95% Wilson upper bound 1.805%). However, the raw primary OCR baseline also observed zero errors at full coverage; accordingly, we do not claim that this benchmark establishes SafeOCR superiority. We further evaluate transcription generalization without tuning on all 328 ClinOCR-Bench evaluation documents. In a separate oracle-localised verifier-component evaluation of 1,850 eligible fields from 238 public de-identified laboratory-report images, 375 fields passed all component gates (20.27%); none contained an incorrect numeric value (95% Wilson upper bound 1.014%). A separately labelled post-outcome diagnostic found that 337/375 passed fields had an exact analyte-value-unit tuple, underscoring that value verification alone does not establish complete field correctness.

We believe the work fits JAMIA because its contribution is an informatics safety contract and reproducible evaluation methodology at the boundary between document AI and structured clinical data, rather than a model-performance claim alone. The study separates OCR accuracy, selective verification, provenance, FHIR conformance, and clinical correctness so that evidence for one is not relabeled as evidence for another.

The software, protocols, evaluation code, evidence artifacts, and exact runtime fingerprints are prepared for public reproducibility. The manuscript also identifies closely related prior work—including source-grounded trust promotion, visually grounded clinical extraction, selective prediction, and OCR-to-FHIR systems—and deliberately avoids absolute “first” claims.

Generative AI tools were used during software development and manuscript preparation for drafting assistance, code generation/review, literature-discovery support, and language editing. All scientific claims, citations, analyses, code changes, and manuscript text were reviewed and verified by the human author(s). The tools are not authors and did not determine authorship or final scientific conclusions.

[Add verified corresponding-author details, funding, competing-interests statement, and any related/preprint manuscripts before submission.]

Sincerely,

[Corresponding author]
