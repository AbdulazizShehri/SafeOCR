# F3 — OCR Adapters and Critical-Crop Re-reader

Status: in progress
Complexity: medium
Depends on: F2 SafeOCR-LabGold harness

## Goal

Add a narrow, model-agnostic OCR boundary:

- PaddleOCR performs the primary full-page read.
- Tesseract independently re-reads only bounded critical crops.
- Both paths normalize into SafeOCR contracts without making verification decisions.

F3 establishes engine I/O and provenance. F4 owns agreement, perturbation, association, and VERIFIED/REVIEW/ABSTAIN policy.

## Frozen runtime direction

Primary reference runtime:
- PaddleOCR 3.7.x
- ONNX Runtime CPU
- PP-OCRv6_small_det
- PP-OCRv6_small_rec
- document orientation, unwarping, and text-line orientation disabled

Independent crop reader:
- Tesseract 5.4.0.20240606 on the reference Windows host
- English traineddata
- stdin -> stdout
- page segmentation mode 7 for single-line critical crops
- no content-specific whitelist or clinically informed correction

## Scope

1. Engine fingerprint contract.
2. PaddleOCR current-result normalization into CandidateSpan.
3. Exact page-byte integrity checks before cropping.
4. Deterministic critical-crop extraction with bounded pixel padding.
5. Tesseract CLI adapter with safe subprocess invocation.
6. Runtime availability probe.
7. One local smoke path per installed engine before F3 closeout.

## Explicit non-goals

- deciding VERIFIED/REVIEW/ABSTAIN;
- LOINC/UCUM semantics;
- table association;
- perturbation voting;
- FHIR;
- PDF ingestion;
- downloading or vendoring OCR source code;
- training/fine-tuning;
- medical plausibility correction.

## Paddle normalization contract

SafeOCR consumes the current PaddleOCR pipeline result fields:
- rec_texts
- rec_scores
- rec_boxes

The normalizer:
- requires equal lengths;
- drops blank recognized strings while preserving aligned box/score indexing;
- treats engine confidence only as metadata;
- converts [xmin, ymin, xmax, ymax] pixel boxes into SafeOCR half-open BoundingBox values;
- rejects malformed, negative, inverted, or out-of-page boxes;
- binds every CandidateSpan to the exact PageAsset;
- binds engine/model/backend identity through EngineFingerprint.

## Critical-crop contract

A crop request must provide source PNG bytes, PageAsset, and requested BoundingBox.

Before cropping:
- SHA-256 of bytes must equal PageAsset.page_sha256;
- decoded dimensions must equal PageAsset dimensions.

Padding is deterministic and clipped to the page edge.

The output records:
- requested source box;
- actual crop box;
- crop PNG SHA-256;
- crop bytes;
- source page identity.

## Tesseract contract

The adapter uses an argv list with shell disabled.

Reference invocation semantics:
- input: stdin
- output: stdout
- language: eng
- PSM: 7
- timeout: explicit

A missing executable, timeout, non-zero exit, or decoding failure raises EngineRuntimeError. Runtime failure is never converted into an empty successful reading.

Recognized text is stripped of trailing OCR whitespace only. SafeOCR does not rewrite digits, units, or punctuation.

## Acceptance criteria

- [x] EngineFingerprint rejects empty engine/model/backend/version fields.
- [x] Paddle result normalization produces CandidateSpan values bound to the supplied PageAsset.
- [x] Paddle blank reads are dropped without misaligning boxes and scores.
- [x] Paddle length mismatch is rejected.
- [x] Paddle malformed/out-of-page boxes are rejected.
- [x] Paddle confidence is preserved only as CandidateSpan metadata.
- [x] Crop extraction rejects page hash mismatch.
- [x] Crop extraction rejects decoded-dimension mismatch.
- [x] Crop padding is deterministic and clipped to page geometry.
- [x] Crop output hash and bytes are deterministic.
- [x] Tesseract invocation uses argv, stdin/stdout, eng, PSM 7, timeout, and shell=False.
- [x] Tesseract runtime failures raise EngineRuntimeError.
- [x] Tesseract output is not clinically corrected.
- [x] Runtime probe reports engine/package availability without importing heavy models.
- [x] Actual PaddleOCR/ONNX CPU smoke produces at least one in-page span on a clean LabGold page before F3 closeout.
- [x] Actual Tesseract smoke re-reads at least one clean LabGold critical-value crop before F3 closeout.
- [x] pytest, Ruff, Pyright strict, and Graft check pass.

## Disk/runtime hardstop

The current machine has limited free disk. Do not install PaddleOCR, ONNX Runtime, models, or a Tesseract binary until the install footprint has been checked.

Use no-cache installs and avoid Docker/model duplication.

## Hardstop

Do not add verification-policy logic or any clinical correction in F3.

## F3 runtime evidence

Reference runtime smoke:
- evidence: `docs/evidence/F3_RUNTIME_SMOKE.json`
- PaddleOCR: 3.7.0
- PaddleX: 3.7.2
- ONNX Runtime: 1.23.2
- detector: PP-OCRv6_small_det_onnx
- recognizer: PP-OCRv6_small_rec_onnx
- Tesseract: 5.4.0.20240606
- LabGold seed/template: 53 / classic
- normalized Paddle spans: 37
- clean Potassium truth: 3.4
- Paddle truth-value detection: PASS
- Tesseract critical-crop exact read: PASS
