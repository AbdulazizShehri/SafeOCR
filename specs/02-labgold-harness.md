# F2 â€” SafeOCR-LabGold Harness

Status: in progress
Complexity: medium
Depends on: F1 Foundation contracts

## Goal

Create a small, deterministic, PHI-free laboratory-report benchmark with exact typed truth and exact pixel regions. F2 establishes ground truth only; it does not run OCR.

## Scope

- One deterministic fake-laboratory-record generator.
- Three renderer templates: classic, compact, grid.
- Single-page PNG output.
- Exact text-region annotations captured during rendering.
- Header identity regions and laboratory row regions.
- Deterministic, geometry-preserving corruption profiles.
- Deterministic JSON manifest.

## Explicit non-goals

- OCR integration.
- PDF ingestion.
- FHIR.
- LOINC/UCUM normalization.
- geometric transforms that require box remapping.
- real patient data.
- clinically validated reference intervals.

## Truth model

Each fake record contains seed, synthetic patient id/name, report id, collected timestamp, and fixed synthetic lab rows.

Each lab row contains stable row id, analyte text, value text, unit text, reference-range text, and optional flag text.

All values are benchmark strings, not clinical recommendations.

## Rendering contract

Every visible truth-bearing text item receives a TruthRegion with semantic role, row id when applicable, exact text, and exact BoundingBox.

The renderer must capture regions from the same draw operation that writes the text; it must not infer coordinates after the fact.

## Corruption contract

F2 corruptions preserve image geometry so truth boxes remain valid.

Allowed F2 transforms: Gaussian blur, contrast adjustment, and JPEG round-trip compression.

The corruption profile is derived from a seed and serialized with the output.

Rotation, perspective, crop, and skew are deferred because they require explicit box transforms.

## Acceptance criteria

- [x] Same record seed produces exactly equal typed truth.
- [x] Generated identifiers/names are visibly synthetic.
- [x] All three templates render valid PNGs.
- [x] Same record + template renders identical bytes within the pinned runtime.
- [x] Different templates produce different page bytes.
- [x] Every lab row has analyte, value, unit, and reference-range truth regions.
- [x] Every TruthRegion is non-empty and contained within page geometry.
- [x] Patient id/name and report id are annotated as header truth regions.
- [x] Render manifest serialization is deterministic and records schema/template plus Pillow/Python/FreeType/JPEG/zlib runtime fingerprint.
- [x] Same record + template has the same page hash in a fresh Python process using the same pinned runtime.
- [x] A committed canonical-runtime golden manifest locks all three template hashes plus one corrupted-page hash to detect renderer drift on Windows x64 + Python 3.12; other supported runtimes rely on deterministic fresh-process checks rather than portable pixel hashes.
- [x] Same corruption seed produces identical corrupted bytes/profile.
- [x] Corrupted bytes differ from clean bytes for a non-zero profile.
- [x] Corruption preserves width, height, and every truth region exactly.
- [x] No real PHI or external data source is required.
- [x] pytest, Ruff, Pyright strict, Graft check pass.

## Hardstop

Do not add OCR engines, FHIR libraries, OpenCV, web services, real datasets, or interactive UI in F2.
