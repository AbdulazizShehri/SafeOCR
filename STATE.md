# SafeOCR State

## In flight

F3 OCR + critical-crop verifier closed locally. F4 Evidence Verification is next.

## Canonical local foundation

- architecture commit: `6f11ccb`
- F1 foundation commit: `1d05ba4`
- F2 LabGold commit: `a2c626a`
- active branch: `feat/f3-ocr-adapters`
- remote repository is currently read-only from the connected credentials

## F3 runtime

- PaddleOCR 3.7.0
- PaddleX 3.7.2
- ONNX Runtime 1.23.2 CPU
- PP-OCRv6_small_det_onnx
- PP-OCRv6_small_rec_onnx
- Tesseract 5.4.0.20240606
- runtime evidence: `docs/evidence/F3_RUNTIME_SMOKE.json`

## Current objective

Specify F4 evidence verification: independent agreement, perturbation stability, structural association, and fail-closed signal derivation. F4 must consume F3 engine outputs without adding clinical correction.
