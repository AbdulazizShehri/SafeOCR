# F6 Review Evidence

Date: 2026-10-06
Phase: F6 Evaluation

## F6.2b clean-head calibration evidence

Canonical artifact: `docs/evidence/F6_CALIBRATION_SMOKE.json`

- source head: `abccceed200736a1e45e945b826991ecdd7673e9`
- working tree reported clean during capture
- split SHA-256: `3aa0af90f3d41d5a0b636ded5d784119da81a193b81a907b7bb69a789cc816a5`
- 2 calibration documents / 12 field cases
- no final-evaluation case executed
- legacy truth-geometry scoring remains explicitly non-headline

## F6.2c OCR-only association scorer

The new LabGold association scorer reconstructs table rows from OCR span geometry and frozen benchmark column bands. Row construction does not consume TruthRegion objects, truth row IDs, truth strings, or corruption metadata.

Truth is consulted only after parsing for evaluation. Association errors are deliberately high-precision: unmatched OCR text is left unscored for table association, and a cross-row error is confirmed only by reciprocal exact row-value evidence. This prevents ordinary OCR character errors from automatically being mislabeled as table-association errors.

Extra parsed rows fail closed rather than being silently dropped.

## Mechanical qualification

- focused association tests: 5 passed
- evaluation contract tests: 18 passed
- full default suite: 162 passed, 4 runtime tests skipped by default
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings, 0 informations
- Graft: 420 nodes / 1342 edges, graph check OK

## Review tools

Alibaba Open Code Review delegate preview covered the final workspace reviewable production/config surface. The same Python correctness/security rules used in earlier SafeOCR grains apply; no blocking issue was found during host-agent review.

Jev advisory checks:
- row parser truth-independence: 0.86
- conservative association-error isolation: 0.58

The second Jev result is treated as uncertainty, not as a pass certificate. The implementation therefore retains conservative `None`/unscored behavior for ambiguous association cases and regression tests for reciprocal row swaps, OCR-only errors, and spurious extra rows.

## Governance

Final LabGold evaluation remains locked. The next gate is an implementation commit followed by a clean exact-head calibration rerun and mechanical requalification. Only then may final-evaluation execution be enabled.
