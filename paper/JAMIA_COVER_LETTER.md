Dear Editors of the Journal of the American Medical Informatics Association,

Please consider our manuscript, “SafeOCR: Evidence-Grounded Selective Verification for Clinical OCR with Provenance-Preserving FHIR Export,” for publication as a Research and Applications article.

SafeOCR addresses a health-informatics problem that arises after optical character recognition: deciding when an extracted clinical field is sufficiently supported for automated downstream use. Rather than proposing a new OCR recognizer, SafeOCR treats OCR output as an untrusted proposal. Critical laboratory fields are bound to source regions and evaluated through deterministic gates that include structural association, a second-engine OCR-family reread, perturbation stability, numeric and unit checks, patient/document linkage, and runtime health. Fields that do not satisfy the frozen policy are routed to review or abstention; only verified fields may enter the FHIR R4 export path.

The manuscript reports the negative results explicitly. On the frozen synthetic SafeOCR-LabGold final set, primary OCR made 0/288 errors (95% Wilson upper bound 1.316%), while SafeOCR accepted 209/288 fields with 0/209 errors (upper bound 1.805%) and routed 79 correct fields to review. This endpoint therefore did not demonstrate a safety gain. On all 328 ClinOCR-Bench evaluation documents, PaddleOCR mean WER was 0.4769 versus 0.5589 for local Tesseract, but PaddleOCR incurred 57 runtime failures retained as empty predictions. In a separate oracle-localised public laboratory-report component study, all 1,850 eligible primary numeric readings were exact; 375 passed the component gates with 0/375 numeric errors, so again the frozen numeric endpoint contained no errors for the gate to intercept. A separately labelled post-outcome diagnostic found analyte or unit mismatches in 38/375 component passes, motivating verification beyond numeric values.

We believe the work may fit JAMIA as an informatics verification specification and transparent evaluation methodology at the boundary between document AI and structured clinical data, rather than as a demonstrated risk-reduction or model-superiority claim. The study separates OCR accuracy, selective verification, provenance, FHIR conformance, and clinical correctness so that evidence for one is not relabeled as evidence for another.

The software, protocols, evaluation code, evidence artifacts, and exact runtime fingerprints are prepared for public reproducibility. The manuscript also identifies closely related prior work—including source-grounded trust promotion, visually grounded clinical extraction, selective prediction, and OCR-to-FHIR systems—and deliberately avoids absolute “first” claims.

Generative AI tools were used during software development and manuscript preparation for drafting assistance, code generation/review, literature-discovery support, and language editing. All scientific claims, citations, analyses, code changes, and manuscript text were reviewed and verified by the human author(s). The tools are not authors and did not determine authorship or final scientific conclusions.

[Add verified corresponding-author details, funding, competing-interests statement, and any related/preprint manuscripts before submission.]

Sincerely,

[Corresponding author]
