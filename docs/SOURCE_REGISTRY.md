# SafeOCR Source and License Registry

This registry separates inspiration, runtime dependencies, models, standards, terminology, and evaluation data.

No third-party source code is copied into SafeOCR merely because it is public.

Status values:
- APPROVED: license/use path has been reviewed for the stated v0.1 use.
- CONDITIONAL: usable only after the exact revision/artifact terms are rechecked.
- REFERENCE: specification or research reference, not vendored code.
- DEFERRED: intentionally excluded from v0.1.

| Source | Role | Current license/use status | v0.1 decision |
|---|---|---|---|
| PaddleOCR | Primary v0.1 OCR/layout adapter | Apache-2.0 code path | APPROVED adapter; pin exact version |
| docTR | Future independent OCR/layout adapter | Apache-2.0 | DEFERRED to v0.2 |
| Tesseract OCR | Classical independent baseline | Apache-2.0 | APPROVED baseline |
| TeleOCR | Future strong VLM reader | Hugging Face model card currently declares Apache-2.0; source-repository terms must be checked per exact revision | DEFERRED to v0.2; no copied source until rechecked |
| ClinOCR-Bench | External clinical OCR benchmark | MIT | APPROVED benchmark |
| Synthea | Potential future richer synthetic patient context | open-source synthetic patient generator | DEFERRED; not required for v0.1 |
| pypdfium2 / PDFium | PDF rendering | pypdfium2 Apache-2.0 OR BSD-3-Clause; PDFium BSD-style; dependency notices required | APPROVED renderer with notices |
| Pillow 12.3.0 | v0.1 LabGold rendering and geometry-preserving image degradation | MIT-CMU | APPROVED and pinned |
| OpenCV | Deterministic image perturbation | Apache-2.0 | APPROVED |
| HL7 FHIR R4 | Interoperability specification | HL7 specification terms | REFERENCE/target standard |
| HAPI FHIR | R4 validation tooling | Apache-2.0 | APPROVED validation tool |
| LOINC | Lab-test identity normalization | Open license with attribution/use conditions | APPROVED terminology subject to license notice |
| UCUM | Units | UCUM license | APPROVED terminology subject to license notice |
| RxNorm Current Prescribable Content | Future medication normalization | NLM terms apply | DEFERRED to v0.2 |
| Full RxNorm release | Future terminology data | UMLS/RxNorm terms may apply | DEFERRED |
| SNOMED CT | Potential future terminology | jurisdiction/licensing complexity | DEFERRED |
| Conformal verification literature | v0.2 statistical risk control | research method | REFERENCE |
| Selective prediction / abstention literature | Evaluation design | research method | REFERENCE |

## Dependency rules

1. Prefer adapters over vendoring.
2. Pin exact package/model/data revisions in benchmark manifests.
3. Record model weight hashes where practical.
4. Ship required third-party notices with distributions.
5. Do not mix model-card license assumptions with source-code license assumptions.
6. If exact licensing is ambiguous, disable that adapter from the default build until resolved.
7. Core SafeOCR behavior must not depend on a paid API or proprietary model.
8. Runtime downloads must be explicit and checksum/revision pinned for reproducible benchmark runs.

## Standards decisions

### FHIR

v0.1 targets FHIR R4 for practical interoperability.

Resources:
- DocumentReference: source clinical document.
- DiagnosticReport: laboratory report context.
- Observation: atomic laboratory result.
- Provenance: derivation and transformation linkage.

Pixel coordinates and verification details remain in the SafeOCR Evidence Manifest rather than being forced into a non-standard FHIR extension in v0.1.

### Laboratory terminology

LOINC is used to normalize test identity when enough source evidence exists.

UCUM is used to parse/canonicalize units and to detect inconsistent unit representations.

Neither may be used to invent missing source content.

## Benchmark-source policy

ClinOCR-Bench provides external realism and document-artifact coverage.

SafeOCR-LabGold is generated entirely inside SafeOCR from typed fake laboratory records and controlled templates, producing exact field and region truth without an external synthetic-patient dependency.

Public benchmark evaluation sets are locked from threshold tuning.

## TeleOCR-specific rule

TeleOCR may be a useful optional engine, but SafeOCR is not a TeleOCR fork.

Before any TeleOCR code or weight is integrated:
- pin the exact repository/model revision;
- capture the source-code license for that revision;
- capture the model-weight license for that revision;
- preserve required notices;
- document runtime requirements;
- ensure SafeOCR still works without it.

This prevents SafeOCR's legal or technical identity from depending on a rapidly changing upstream model.

## Naming risk

A separate general-purpose browser OCR product currently uses the SafeOCR name. The repository may keep the SafeOCR project identity, but package/web publication requires a collision/trademark review. A package namespace such as `safeocr-health` may be used if required.
