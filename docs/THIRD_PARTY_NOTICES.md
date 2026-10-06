# Third-Party Notices

SafeOCR uses third-party software and standards through adapters and package dependencies. This file records attribution relevant to the v0.1 reference implementation; upstream license texts remain authoritative.

## ucumvert 0.3.2

Role: local case-sensitive UCUM parser used by F4 as a terminology veto.

Source: https://github.com/dalito/ucumvert

The ucumvert software code is distributed under the MIT License. The package also includes UCUM specification/data files that remain under the UCUM Copyright Notice and License.

SafeOCR does not vendor or modify ucumvert source code in this repository.

## UCUM

Unified Code for Units of Measure (UCUM) specification copyright ©1999-2024 Regenstrief Institute, Inc. All rights reserved.

License: UCUM Copyright Notice and License, Version 1.1, June 2024.

Authoritative license: https://github.com/ucum-org/ucum/blob/main/LICENSE.md

SafeOCR uses UCUM through an unmodified parser/data dependency for interoperability and validation. SafeOCR does not create a modified UCUM standard, rewrite UCUM definitions, or infer replacement units from clinical context.

The UCUM work is provided on an "AS IS" basis without warranties or conditions of any kind as described in its license.

## Existing OCR runtime dependencies

The v0.1 source registry separately records the pinned PaddleOCR, PaddleX, ONNX Runtime, PP-OCRv6 ONNX models, Tesseract, Pillow, and other dependencies together with their license/use status.

See docs/SOURCE_REGISTRY.md.

## ClinOCR-Bench / ClinOCR-Bench-Baseline

ClinOCR-Bench v1.0 is used as an external PHI-free clinical OCR benchmark under the MIT License. The external-validation protocol pins release asset SHA-256 `ce1d231138050abf7f458ba5e6bd75c6ee2f3832b72f22296843da4c5ba45457` and dataset repository commit `3b720a951bb7eec4a4f4fb34a636e7335a19981e`.

SafeOCR's `safeocr.clinocr_eval.word_error_rate` follows the MIT-licensed `ClinOCR-Bench-Baseline` WER algorithm and summary-statistics convention so the external experiment is directly comparable with the benchmark's official reporting. Upstream repository: `https://github.com/ClinOCR-Bench/ClinOCR-Bench-Baseline`.
