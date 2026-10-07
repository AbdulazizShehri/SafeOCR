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
- Second-engine critical-crop engine: Tesseract 5.4.0.20240606
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


## Public laboratory-report verifier-component study

The external laboratory-report study uses the public image collection released with Xue et al. (IEEE Access 2020; DOI 10.1109/ACCESS.2019.2961964) and later used/described by Ma et al. (BMC Medical Informatics and Decision Making 2023).

SafeOCR does not redistribute the source images or source annotations. The upstream repository does not expose a dataset-wide license file in the audited state, so absence of a stated license must not be described as permissive redistribution terms.

Frozen identity recorded in the result artifact:

- OCR source head: `47433ae8fb429671489ac530dfd05c95a82bfaf4`
- dataset-manifest SHA-256: `e55fbe53fe886f54bd3b9cb5d7a98253577bc283125bbcb9f454a67bf000a74b`
- OCR run-state SHA-256: `c934dccb631d322b20a9fe7280e77a6c00e287d14017de79b65103e78eac377f`
- scorer head: `fc4a1543f79869d36c21f2e7ce615e80ed3f5ce5`
- scorer working tree: clean
- PaddleOCR: 3.7.0
- models: PP-OCRv6_small_det + PP-OCRv6_small_rec
- backend: ONNX Runtime CPU
- Tesseract: 5.4.0.20240606
- evaluation images: 238
- OCR runtime failures: 0
- annotation source opened by OCR runner: false
- tuning performed: false

The labels-file SHA-256 must be recorded explicitly in the final release manifest before archival publication; the current aggregate result artifact does not carry that value.

See `paper/MA2023_EXTERNAL_COMPONENT_PROTOCOL_ADDENDUM.md` for the provenance correction, oracle-localisation mechanics, cohort-flow disclosure, and protocol/code deviation.

## ClinOCR-Bench external OCR run

Frozen ClinOCR-Bench identity:

- release asset SHA-256: `ce1d231138050abf7f458ba5e6bd75c6ee2f3832b72f22296843da4c5ba45457`
- repository commit: `3b720a951bb7eec4a4f4fb34a636e7335a19981e`
- evaluation documents: 328
- PaddleOCR failures retained and scored as empty: 57/328
- failed rotated documents: 33/56
- failed mixed-artifact documents: 24/48

The local Tesseract run is a frozen local-runtime result, not an exact reproduction of the official authors' Tesseract environment.

## Portability note

The Ma2023 scorer originally resolves Tesseract from standard Windows installation paths. This is a reproducibility portability limitation, not a scientific parameter. The paper revision should expose the executable path as an explicit CLI/configuration input while retaining the recorded Windows path for the frozen result.
