# SafeOCR State

## In flight

F6 Evaluation is active. F6.2b calibration runner is qualified but final-evaluation execution remains locked.

## Canonical local foundation

- architecture commit: `6f11ccb`
- F1 foundation commit: `1d05ba4`
- F2 LabGold commit: `a2c626a`
- F3 OCR adapters commit: `3aba8f6`
- F4 evidence verification commit: `b11da0c`
- patient-binding prerequisite fix: `c711a70`
- F5 FHIR R4 gate commit: `448f024`
- F6.1 evaluation contracts commit: `f3810a8`
- F6.2a split freeze commit: `5b328de`
- active branch: `feat/f6-evaluation`

## F6 split

- canonical split SHA-256: `3aa0af90f3d41d5a0b636ded5d784119da81a193b81a907b7bb69a789cc816a5`
- calibration: 24 document cases
- final evaluation: 48 document cases
- final role remains inaccessible to the current calibration runner

## F6.2b runner

- calibration-only runtime plumbing implemented
- clean + corrupted smoke: 12 field cases
- explicit runtime pytest: PASS
- default pytest: 157 passed, 4 skipped
- Ruff / Pyright / Graft / diff check: PASS
- Graft: 402 nodes / 1285 edges
- Jev bounded-runner score: 3.10 / 4
- Alibaba delegate review: no blocking finding
- truth-geometry alignment is explicitly non-headline and not an end-to-end association claim

## Publication state

Local history is canonical. Remote publication is still blocked by local Git credentials authenticating as `TheHalfMoon`, which has read-only permission on `AbdulazizShehri/SafeOCR`. Do not rewrite local history to work around authentication.

## Current objective

Commit F6.2b, rerun calibration from a clean exact head, capture canonical calibration evidence, then build an end-to-end association scorer before any final-evaluation headline claims.
