# SafeOCR Novelty Map

The goal of this document is to prevent an overbroad novelty claim.

| Capability | Ma 2023 | Hsu 2022 | Ren 2025 | Swaminathan 2024 | Kim 2025 | Girda & Groza 2026 | SafeOCR v0.1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Scanned clinical-document OCR | yes | yes | yes | no | no | source documents | yes |
| Laboratory-report focus | yes | no | yes | no | no | yes | yes |
| Structured field extraction | yes | yes | yes | yes | yes | yes | yes |
| Explicit reject/review state | no central gate | no | no central gate | yes | yes | yes | yes |
| Source-grounded admission gate | no | no | no | no | verification of narrative extraction | yes | yes |
| Pixel-region binding per accepted field | partial OCR boxes | layout-aware | layout boxes | no | no | quotation/source support | yes |
| Independent OCR-family reread | no | no | no | no | no | no | yes |
| Perturbation-stability gate | preprocessing experiments | preprocessing experiments | no | no | no | no | yes |
| Structural row association as mandatory gate | IE pipeline | layout features | layout analysis | no | no | yes | yes |
| Patient/document linkage gate | not central | not central | privacy filtering | no | no | provenance context | yes |
| Explicit clinical criticality policy | no | no | no | cost-sensitive labels | no | no | yes |
| Risk/coverage reporting | no | no | no | yes | accepted-risk control | admission coverage | yes |
| Held-out no-tuning final contract | standard evaluation | standard evaluation | standard evaluation | train/test | conformal calibration | replay/conformance | yes |
| Provenance attached to downstream record | no | no | no | no | no | yes | yes |
| FHIR export blocked unless field verified | no | no | no | no | no | downstream PHR trust promotion | yes |
| Official FHIR validator evidence | no | no | no | no | no | not central | yes |

## Positioning

The strongest novelty claim is **not** "the first evidence-gated medical OCR system."

The literature now contains close prior/parallel work, especially Girda and Groza (2026), which also treats laboratory extraction as a trust-promotion problem with deterministic source verification, same-row evidence, provenance, and review retention.

A defensible contribution statement is:

> SafeOCR contributes a healthcare OCR verification contract that combines pixel-bound field evidence, independent OCR-family rereading, perturbation stability, structural and patient-linkage gates, explicit criticality, selective automation states, governed risk/coverage evaluation, and verification-gated FHIR R4 export in one reproducible pipeline.

This is an **integration + evaluation + safety-contract contribution**.

## What makes the paper interesting despite close prior work

1. The trust decision is tied to the exact source pixel region rather than only a supporting quotation.
2. Verification uses a second OCR family on the bounded critical crop.
3. Non-destructive perturbation stability is part of acceptance.
4. Patient/document linkage and row association are explicit safety gates.
5. Criticality changes verification strictness without rewriting source text.
6. The paper reports unsafe accepted error jointly with verified coverage.
7. Calibration/final evaluation roles are mechanically separated.
8. FHIR R4 export is downstream of the trust decision and is mechanically blocked for non-verified fields.
9. FHIR validator conformance evidence and extraction correctness are intentionally reported as different claims.
10. The manuscript publishes negative evidence: the primary OCR baseline was perfect on LabGold, so superiority is not claimed.
