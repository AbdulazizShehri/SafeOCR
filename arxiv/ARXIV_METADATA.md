# SafeOCR arXiv Submission Metadata

Checked: 2026-10-07

## Title

SafeOCR: Evidence-Grounded Selective Verification for Clinical OCR with Provenance-Preserving FHIR Export

## Author display

Current source provisionally uses **Abdulaziz M. Shehri** with **Independent researcher** as the affiliation.

**Hard pre-submission identity gate:** confirm the exact scholarly display name against the author's intended ORCID/journal identity. The repository metadata currently also contains "Abdulaziz Alshehri"; do not post arXiv v1 until one canonical scholarly name is chosen and synchronized.

## Abstract

Use the structured abstract in `main.tex` / `paper/manuscript.md`. The current manuscript abstract remains below the JAMIA 250-word limit.

## Suggested arXiv classification

- Primary candidate: `cs.CV`
- Potential cross-list: `cs.AI`

Rationale: the central technical object is OCR/document-image verification with an AI safety and health-informatics application layer. The work is not primarily a language-model paper.

## Comments field

Suggested concise wording:

`Preprint. SafeOCR v0.1 methods and evaluation study. The frozen safety endpoints contained no primary-OCR errors for the verification gate to intercept; the paper therefore reports feasibility, review/rejection cost, failure handling, and exploratory full-field mismatch evidence rather than a demonstrated risk reduction. Code and frozen evidence artifacts are available in the public repository.`

## License

Choose an arXiv license deliberately at submission. The repository code is Apache-2.0, but the manuscript/preprint license is a separate publication choice and must not be inferred automatically.

## Public repository

https://github.com/AbdulazizShehri/SafeOCR

## Scientific freeze

The arXiv version must preserve the frozen protocol:
- no threshold changes;
- no cohort changes;
- no preprocessing changes;
- no post-outcome retuning;
- Ma2023 post-outcome tuple analysis remains explicitly exploratory.

## Preprint-to-JAMIA linkage

JAMIA currently permits manuscripts that have appeared as preprints. After journal publication, update the preprint record with the published DOI/link in accordance with the journal policy then in force.

## Submission hygiene

Do not upload:
- raw Ma2023 source images;
- credentials;
- local caches;
- review-agent scratch files;
- private notes;
- unrelated evidence artifacts not needed to compile the manuscript.


## Adversarial-review gates before arXiv v1

The 2026-10-07 pre-submission review identified factual/presentational blockers. The source package has been revised to:

- correct the public laboratory-report dataset provenance to Xue et al. 2020;
- remove the incorrect public-dataset kappa attribution;
- report ungated baseline bounds beside gated zero-event bounds;
- state explicitly that the frozen safety endpoints had no primary-OCR errors to intercept;
- report 57/328 ClinOCR PaddleOCR runtime failures in the abstract;
- give the post-outcome 38/375 analyte-or-unit mismatch result explicit prominence;
- disclose LabGold truth-geometry score alignment;
- replace internal "preregistered" wording with "prespecified, commit-timestamped";
- add the official-versus-local Tesseract reproducibility comparison;
- add cohort-flow and gate-funnel tables.

Current static preflight:
- abstract: 220 words;
- JAMIA main text (excluding table cells): approximately 3,440 words;
- citations: 23/23 bibliography entries cited;
- main tables: 4;
- figures: 2;
- no missing or uncited bibliography keys;
- no raw Markdown table/heading leakage;
- no stale "preregistered" wording;
- no stale "independent verification" wording.

Remaining before posting:
1. confirm one canonical scholarly author name and affiliation;
2. complete a clean LaTeX compile and visual PDF inspection;
3. deliberately choose the arXiv manuscript license.

Internal strategy/review files are not part of the arXiv upload package.
