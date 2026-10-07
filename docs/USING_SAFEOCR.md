# Using SafeOCR v0.1

SafeOCR v0.1 is a verification core for laboratory-report OCR. It is intended to sit between OCR/extraction and automated structured export.

The terminal states are:

- `VERIFIED_AUTO`
- `REVIEW_REQUIRED`
- `ABSTAINED`

Only `VERIFIED_AUTO` evidence may enter the automated FHIR R4 export path.

## Install

Follow the package installation instructions in the repository root README. The reference OCR path uses PaddleOCR for primary full-page OCR and Tesseract for second-engine critical-crop rereading.

## Minimal policy example

```python
from safeocr import Criticality, VerificationSignals, decide

signals = VerificationSignals(
    candidate_present=True,
    visual_grounded=True,
    independent_agreement=True,
    perturbation_stable=True,
    structural_association=True,
    numeric_parse_unambiguous=True,
    unit_valid=True,
    patient_linkage_unambiguous=True,
    runtime_healthy=True,
)

decision = decide(signals, criticality=Criticality.CRITICAL)
print(decision.state)
print(decision.failed_gates)
```

All required gates passing yields `VERIFIED_AUTO`. A failed review gate yields `REVIEW_REQUIRED`. Missing candidate evidence, missing visual grounding, or an unhealthy runtime yields `ABSTAINED`.

## Pipeline placement

```text
Clinical document
  -> OCR and layout proposal
  -> evidence-bound laboratory field candidate
  -> SafeOCR verification
  -> VERIFIED_AUTO / REVIEW_REQUIRED / ABSTAINED
  -> FHIR R4 export only for VERIFIED_AUTO
```

## Public demonstration

The official Hugging Face Space is a synthetic, PHI-free interactive policy explorer:

https://huggingface.co/spaces/MedScaleAI/SafeOCR

The frozen synthetic benchmark is published at:

https://huggingface.co/datasets/MedScaleAI/SafeOCR-LabGold

## Important boundary

The v0.1 paper does not establish end-to-end clinical deployment safety. The public Space intentionally does not accept real patient reports. End-to-end raw-document extraction remains a separate validation target.

SafeOCR is research software and must not be used for diagnosis, treatment decisions, or unsupervised clinical use.
