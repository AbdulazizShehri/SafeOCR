# Reproducibility Statement

SafeOCR v0.1 is designed so that the primary manuscript claims can be traced to immutable machine-readable artifacts.

## Software identity

- Package: `safeocr-health`
- Version: `0.1.0`
- License: Apache-2.0
- Reference OCR engine: PaddleOCR 3.7.0
- Reference detection model: PP-OCRv6_small_det
- Reference recognition model: PP-OCRv6_small_rec
- Reference backend: ONNX Runtime CPU
- Independent critical-crop engine: Tesseract 5.4.0.20240606
- FHIR target: R4 / 4.0.1

## Frozen primary evaluation

The primary LabGold result is stored in:

`docs/evidence/F6_FINAL_EVALUATION.json`

The artifact records:
- exact source git head;
- clean-working-tree state;
- frozen split SHA-256;
- engine versions;
- all primary aggregate metrics;
- uncertainty intervals;
- interpretation limitations.

The final split contains 48 documents and 288 critical-field cases. The evaluation policy has one frozen operating point. The final set was not used for threshold selection.

## Evidence traceability

The static evidence demonstration is available in:
- `docs/evidence/F7_EVIDENCE_REPORT.json`
- `docs/evidence/F7_EVIDENCE_REPORT.html`

A verified field includes:
- source page SHA-256;
- source bounding boxes;
- OCR engine and version;
- verification signals;
- policy version;
- terminal decision;
- failed gates, if any;
- deterministic explanation.

## FHIR evidence

FHIR conformance evidence is stored in:

`docs/evidence/F5_RUNTIME_SMOKE.json`

The canonical valid bundle passed the recorded HL7 validator execution with zero errors. A deliberately invalid control was rejected. This evidence is a conformance test and is not presented as a field-level FHIR mapping-accuracy estimate.

## External generalization

ClinOCR-Bench v1.0 is evaluated under:
- `paper/EXTERNAL_VALIDATION_PROTOCOL.md`
- `scripts/run_clinocr_external.py`

The protocol was committed before evaluation images or ground-truth transcripts were opened. The dataset release SHA-256 and official metric-semantics repository commit are frozen. The experiment uses all 328 official evaluation documents and does not alter model, preprocessing, thresholds, or SafeOCR policy in response to external outcomes.

## Reproduction boundary

Exact numerical reproduction requires:
- the pinned/public benchmark data;
- the released source revision;
- compatible OCR model artifacts;
- Tesseract;
- the recorded Python dependencies;
- sufficient local CPU/RAM.

The manuscript distinguishes exact artifact reproduction from clinical generalizability. Reproducing the software result does not establish clinical deployment safety.
