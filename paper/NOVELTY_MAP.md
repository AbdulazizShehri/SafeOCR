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

The strongest novelty claim is **not** "the first evidence-gated medical OCR system," "the first visually grounded clinical extraction system," or "the first OCR-to-FHIR system."

The literature contains close prior/parallel work. Girda and Groza (2026) treat laboratory extraction as deterministic trust promotion with source support, same-row evidence, provenance, and review retention. RAPTOR+ (2026) links extracted clinical fields to source-image bounding boxes and evaluates joint value correctness plus evidence localisation. Ben Hmida et al. (2025) combine OCR verification with abstention. SMART Text2FHIR and printed-form-to-FHIR studies establish prior art for mapping extracted clinical information into FHIR.

A defensible contribution statement is:

> SafeOCR contributes a reproducible healthcare OCR safety contract that combines source-region binding with independent OCR-family rereading, perturbation stability, structural and patient-linkage gates, explicit clinical criticality, selective automation states, governed accepted-error/coverage evaluation, and FHIR R4 export mechanically blocked for non-verified fields.

This is an **integration + evaluation + safety-contract contribution**.

## What still differentiates SafeOCR

1. The accepting verifier uses a second OCR family on the bounded critical crop rather than relying solely on the extracting model's own grounding.
2. Non-destructive perturbation stability is a mandatory acceptance signal.
3. Patient/document linkage and row association are explicit fail-closed safety gates.
4. Criticality changes verification strictness without rewriting source text.
5. The paper reports unsafe accepted error jointly with verified coverage.
6. Calibration/final evaluation roles are mechanically separated and final outcomes cannot be routed back into tuning.
7. FHIR R4 export is downstream of the trust decision and mechanically blocked for non-verified fields.
8. FHIR validator conformance evidence and extraction correctness are intentionally reported as separate claims.
9. The manuscript publishes negative evidence: the primary OCR baseline was perfect on LabGold, so superiority is not claimed.
10. External OCR generalization is evaluated under a frozen no-tuning protocol separately from SafeOCR's field-level safety claims.

## Prohibited novelty shortcuts

- Do not claim pixel-level visual grounding is new.
- Do not claim source-grounded admission is new.
- Do not claim abstention/review is new.
- Do not claim provenance is new.
- Do not claim FHIR conversion is new.
- Do not claim that lower WER is equivalent to lower clinical risk.
- Avoid absolute "first" claims; the paper does not need one.
