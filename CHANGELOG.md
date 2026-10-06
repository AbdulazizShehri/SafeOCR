# Changelog

All notable SafeOCR changes are documented here.

## 0.1.0 — 2026-10-06

First research release.

### Added

- healthcare-only laboratory-report scope;
- deterministic SafeOCR-LabGold benchmark harness;
- PaddleOCR full-page and Tesseract critical-crop readers;
- fail-closed evidence verification with visual grounding, independent agreement,
  perturbation stability, table association, UCUM veto, runtime health, and
  HMAC-bound patient linkage;
- FHIR R4 DocumentReference, DiagnosticReport, Observation, and Provenance export gate;
- official HL7 FHIR validator evidence;
- frozen LabGold primary evaluation and conservative risk/coverage operating points;
- ClinOCR-Bench v1.0 metadata adapter and no-test-set-tuning Safety Track manifest;
- deterministic JSON + self-contained HTML evidence report with embedded source crop.

### Primary frozen LabGold result

SafeOCR accepted 209/288 fields (72.57% verified coverage), sent 79/288 to
review, and observed 0 unsafe accepts. The 95% Wilson upper bound for unsafe
accept rate was 0.01805.

This synthetic benchmark does **not** establish SafeOCR superiority over the
raw primary OCR baseline, which also observed zero accepted errors at full
coverage. Zero observed errors is not zero risk.

### Limitations

- research software only; not a medical device;
- laboratory reports only in v0.1;
- no medication extraction;
- no diagnosis or treatment recommendation;
- F6 does not estimate a per-field FHIR mapping error rate;
- ClinOCR-Bench v1.0 provides transcript truth, not SafeOCR structured
  field/patient/FHIR annotations, so unsupported external safety claims are withheld.
