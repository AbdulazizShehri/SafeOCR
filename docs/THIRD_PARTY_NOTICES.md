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
