# SafeOCR Evidence Sources

Verified during architecture planning on 2026-10-06.

## Core implementations

- Pillow: https://pypi.org/project/pillow/12.3.0/

- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- docTR: https://github.com/mindee/doctr
- Tesseract: https://github.com/tesseract-ocr/tesseract
- TeleOCR: https://github.com/caipeng328/TeleOCR
- TeleOCR model: https://huggingface.co/XingChen-AGI/TeleOCR
- pypdfium2: https://github.com/pypdfium2-team/pypdfium2
- HAPI FHIR: https://github.com/hapifhir/hapi-fhir

## Data and benchmark

- ClinOCR-Bench: https://github.com/ClinOCR-Bench/ClinOCR-Bench

## Standards and terminology

- FHIR R4 DocumentReference: https://hl7.org/fhir/R4/documentreference.html
- FHIR R4 DiagnosticReport: https://hl7.org/fhir/R4/diagnosticreport.html
- FHIR R4 Observation: https://hl7.org/fhir/R4/observation.html
- FHIR R4 Provenance: https://hl7.org/fhir/R4/provenance.html
- LOINC license: https://loinc.org/license
- UCUM license: https://ucum.org/license
- RxNorm files/terms: https://www.nlm.nih.gov/research/umls/licensedcontent/rxnormfiles.html

## Research references

- ClinOCR-Bench paper: arXiv:2607.03650
- Conformal Prediction and Verification of Large Language Model Extractions in EHR Data, AAAI Symposium Series, 2025, DOI 10.1609/aaaiss.v7i1.36929

## Evidence hygiene

This file is a planning registry, not a substitute for a lockfile or third-party notices.

Before release, SafeOCR must generate a machine-readable dependency/model/dataset manifest and a third-party notices artifact from exact pinned revisions.
