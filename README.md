# SafeOCR

**Trust pixels, not predictions.**

SafeOCR is healthcare-only verification infrastructure for clinical document extraction. It sits between OCR/document-understanding engines and structured health data, and blocks unverified clinical facts from automatic downstream use.

> If SafeOCR cannot bind a clinical datum to source evidence and pass a risk-appropriate verification gate, it does not export that datum to FHIR.

## Why

A low character-error rate is not a clinical safety guarantee. A one-character error can turn `0.5` into `5`, lose a minus sign, change a laboratory unit, or attach a correct number to the wrong analyte row.

SafeOCR treats those failures as a selective-verification problem, not merely an OCR-accuracy problem.

## v0.1 scope

SafeOCR v0.1 supports one healthcare document family only:

- laboratory reports.

Inputs are printed, scanned, fax-like, or photographed laboratory reports. Handwritten free-text is a stress condition, not a promised capability. Medication documents are explicitly deferred to v0.2.

Core decisions are:

- `VERIFIED_AUTO`
- `REVIEW_REQUIRED`
- `ABSTAINED`

Only `VERIFIED_AUTO` fields may enter automatic FHIR export in v0.1. Human review resolution is deferred to v0.2; v0.1 produces evidence-rich review reports.

## Core invariants

1. No evidence -> no automatic export.
2. Missing is never interpreted as negative.
3. Agreement between OCR engines is evidence, not proof.
4. Clinical plausibility may block an extraction but must never rewrite source pixels.
5. Safety-critical disagreement routes to review or abstention.
6. Every accepted field is reproducible from pinned inputs, model revisions, transforms, and policy versions.
7. No real PHI is required for the public benchmark or demo.

## Architecture

```
Clinical document
       |
       v
Safe ingestion + rendering
       |
       v
OCR / parsing adapters
       |
       v
Evidence-bound clinical fields
       |
       v
Verification signals
       |
       v
Risk-aware decision policy
   /       |        \
verified  review   abstain
   |
   v
FHIR R4 export gate
   |
   +--> Provenance
   +--> Evidence manifest
```

SafeOCR is model-agnostic. OCR engines are replaceable readers; SafeOCR owns the evidence contract, verification logic, decision policy, audit trail, benchmark, and FHIR gate.

## v0.1 engine paths

- PaddleOCR: primary OCR/layout path.
- Tesseract: independent critical-crop re-reader and classical baseline.

docTR and TeleOCR remain planned adapters, but they do not block v0.1.

## Evaluation

Headline metrics:

- Critical Field Exact Accuracy
- Unsafe Accept Rate
- Verified Coverage
- Review Rate
- Abstention Rate
- Patient Attribution Error Rate
- Table Association Error Rate
- FHIR Mapping Error Rate

The primary result is a risk-coverage curve, not a single confidence score.

See [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md), [docs/SAFETY_CONTRACT.md](docs/SAFETY_CONTRACT.md), and [docs/SOURCE_REGISTRY.md](docs/SOURCE_REGISTRY.md).

## Safety

SafeOCR is research software. It is not a medical device and must not be used to make diagnosis or treatment decisions. v0.1 is designed to evaluate whether extracted clinical facts are sufficiently evidenced for structured-data export; it does not infer missing facts, diagnose conditions, or recommend treatment.
