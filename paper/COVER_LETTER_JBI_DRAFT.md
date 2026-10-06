# Draft Cover Letter — Journal of Biomedical Informatics

Dear Editor,

Please consider our manuscript, **“SafeOCR: Evidence-Grounded Selective Verification for Clinical OCR with Provenance-Preserving FHIR Export,”** for publication as an Original Research article in the *Journal of Biomedical Informatics*.

Clinical OCR pipelines are commonly evaluated by transcription or extraction accuracy, but these metrics do not directly answer a downstream informatics question: when is an OCR-derived clinical field sufficiently supported to be automatically converted into structured health data? SafeOCR addresses this problem as a selective-verification and provenance problem rather than as a new OCR recognizer.

The manuscript makes a methodological contribution by defining and evaluating a fail-closed field-level verification contract for laboratory-report OCR. Critical fields retain source-pixel provenance and must pass structural association, independent OCR-family rereading, perturbation-stability, parsing, unit, patient-linkage, and runtime gates before automatic acceptance. Only verified fields can cross the FHIR R4 export boundary; review-required and abstained fields remain source-linked but are blocked from automatic export.

We emphasize a result that limits, rather than inflates, our claim. On the frozen synthetic final benchmark, SafeOCR automatically verified 209/288 critical fields with zero observed unsafe accepts (95% Wilson upper bound 1.805%), but the primary OCR baseline also observed zero errors at 100% coverage. We therefore do **not** claim that the synthetic benchmark demonstrates superiority over the primary OCR engine. Instead, the paper evaluates the verification contract, auditability, and governed risk/coverage methodology, and supplements this with a preregistered zero-shot external OCR-generalization study on ClinOCR-Bench.

We believe the manuscript fits JBI because its focus is a generalizable biomedical-informatics methodology for controlling the transition from uncertain document extraction to structured interoperable data. The work separates OCR correctness, selective acceptance, provenance, and FHIR conformance as distinct evidentiary claims and provides machine-readable artifacts for each.

The software and reproducibility artifacts are prepared for public release under Apache-2.0. The public evaluation uses synthetic or public PHI-free data. The study does not involve diagnosis, treatment recommendations, or live clinical decision support, and we make no medical-device or deployment-safety claim.

[Insert author names, affiliations, corresponding-author details, funding disclosure, competing-interest declaration, and any required statement regarding preprints or related submissions.]

Thank you for your consideration.

Sincerely,

[Corresponding author]
[Affiliation]
[Email]
