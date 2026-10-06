# OpenAlex Search Audit

Search date: 2026-10-06
Coverage window: 2015-01-01 through 2026-10-06
API: OpenAlex Works search
Results requested per query: 100

This is a reproducibility record for broad prior-art discovery. It is not presented as a formal systematic review or PRISMA-complete search.

## Query 1 — clinical OCR / laboratory reports

Search string:

`clinical OCR medical document laboratory report`

OpenAlex reported 2,843 matching works.

High-relevance records screened into the manuscript or literature matrix included:
- Xue et al. — *Text Detection and Recognition for Images of Medical Laboratory Reports With a Deep Learning Approach* — DOI 10.1109/ACCESS.2019.2961964.
- Ma et al. — *Extracting laboratory test information from paper-based reports* — DOI 10.1186/s12911-023-02346-6.
- Li et al. — *Improving tabular data extraction in scanned laboratory reports using deep learning models* — DOI 10.1016/j.jbi.2024.104735.
- Hsu et al. — *ClinOCR-Bench* — arXiv:2607.03650.
- Worragin et al. — *Towards Intelligent Virtual Clerks: AI-Driven Automation for Clinical Data Entry in Dialysis Care* — DOI 10.3390/technologies13110530; retained as context, not a central claim source.
- DEXTER — arXiv:2207.06823; screened as table-extraction context.

## Query 2 — selective prediction / clinical extraction

Search string:

`selective prediction abstention clinical information extraction`

OpenAlex reported 420 matching works.

High-relevance records:
- Swaminathan et al. — DOI 10.1093/jamia/ocad182.
- contemporary healthcare abstention work was screened for context.
- generic or diagnosis-only abstention work was excluded when it did not materially inform document extraction.

## Query 3 — OCR verification / abstention / risk-coverage

Search string:

`document OCR verification abstention risk coverage`

OpenAlex reported 104 matching works.

High-relevance records:
- Ben Hmida et al. — DOI 10.1109/INISTA68122.2025.11249647.
- Gong et al. — *Geometric Risk Control for Vision-Language Model OCR* — arXiv:2603.19790.
- additional document-verification works were screened and retained only where they changed the novelty or evaluation framing.

## Query 4 — FHIR / provenance / clinical extraction

Search string:

`FHIR provenance clinical information extraction`

OpenAlex reported 611 matching works.

High-relevance records:
- Çinar-Koraş et al. — arXiv:2606.19602.
- FHIR implementation/provenance papers were screened against the manuscript's narrower claim about traceable downstream structured data.
- The normative FHIR R4 specification remains the authority for SafeOCR's conformance target.

## Additional targeted searches

Academic-search queries were also run for:
- clinical OCR verification + source evidence + FHIR;
- medical document OCR abstention / field-level verification;
- source-pixel grounding and provenance;
- document-extraction confidence calibration;
- public lab-report OCR datasets;
- external clinical OCR benchmarks.

These targeted searches identified:
- Girda & Groza 2026 — source-grounded integrity gates for laboratory data;
- Curcio et al. 2026 — field-level FPR-constrained document validation;
- Roy et al. 2026 — ConfBench confidence-calibration benchmark;
- MedRepBench 2026;
- MedStruct-S 2026;
- ACIE 2026.

## Screening principle

A work is retained when it changes at least one of:
1. the novelty statement;
2. the evaluation design;
3. the safety/abstention framing;
4. the external-validation plan;
5. the provenance/FHIR interpretation boundary.

Low-quality, off-topic, duplicate, non-primary, and generic commentary sources are not used to support substantive claims when a primary paper or standard is available.

## Search-update gate

Immediately before submission:
- rerun all four OpenAlex queries;
- rerun targeted searches for publications from 2026-10-07 through the submission date;
- check all arXiv references for peer-reviewed versions;
- update the novelty map before finalizing title, abstract, and cover letter.
