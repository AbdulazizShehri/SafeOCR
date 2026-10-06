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


## F6.2c exact-head qualification

Implementation commit: `c6abed545b531834a46784f06997ac7fcbb8291b`

Clean-head calibration evidence reports `working_tree_dirty=false` at the exact implementation head. The rerun covered 2 calibration documents / 12 field cases. OCR-only association parsing used no truth geometry and produced 12/12 association-evaluable rows with 0 observed association errors on this bounded smoke.

Mechanical rerun: 162 passed / 4 skipped; Ruff PASS; Pyright strict 0 errors / 0 warnings / 0 informations; Graft 420 nodes / 1342 edges with graph check OK. This closes F6.2c and permits a separate final-role-only runner grain. No final-evaluation case was executed during this closeout.


## F6.2d final-only runner pre-execution review

The final LabGold runner is intentionally separate from the calibration runner. Its CLI exposes only runtime path/output controls: there is no partial-case selector, calibration role, threshold parameter, policy mutation, or tuning input.

Execution guards:
- selects all 48 frozen `EvaluationRole.EVALUATION` document cases;
- verifies the final split cardinality before loading OCR models;
- refuses to overwrite an existing primary final evidence artifact;
- requires a clean working tree at run start;
- records the clean exact git head and preregistered split SHA-256;
- preserves the OCR-only association scorer and separately labels legacy truth-geometry-aligned per-field metrics.

Mechanical pre-commit tests cover the CLI surface and rerun refusal without executing final-role data. Final-role execution remains prohibited until the runner commit receives exact-head qualification.

Pre-execution review evidence: Jev final-runner governance score 3.31/4 (57% strong, 39% excellent). Alibaba Open Code Review delegated Python/default rules were applied to the final runner, tests, and spec; host-agent review found no blocking correctness or security issue. Full pre-commit gates: 165 passed / 4 skipped, Ruff PASS, Pyright strict 0 errors / 0 warnings, pip check PASS, Graft 440 nodes / 1424 edges with graph check OK.

## F6.2d attempt 1 infrastructure failure

The exact-head runner at `162a9c03536a82e1e1b346ecfdaeb56124de7940` started the frozen final role but terminated after 804.72 seconds with `numpy._core._exceptions._ArrayMemoryError` while PaddleOCR attempted to allocate a 17.1 MiB recognition array of shape `(6, 40, 18710)`. No `F6_FINAL_EVALUATION.json` artifact was created and no final metric payload was emitted or inspected. The failure is preserved at `docs/evidence/F6_FINAL_ATTEMPT_1_FAILURE.json`.

Recovery is infrastructure-only: reduce PaddleOCR text-recognition batch size while preserving the exact OCR model names/revisions, SafeOCR verification policy, thresholds, frozen split SHA-256, corruption seeds, truth, and metric definitions. Recovery must be requalified entirely on calibration data before a second final-role attempt.

Recovery calibration check: PaddleOCR text-recognition batch size was reduced from its default to `1` in both calibration and final runners. The OCR model identities, SafeOCR policy, frozen split, corruption seeds, and metric definitions were unchanged. A 2-document / 12-field calibration rerun completed without memory failure and reproduced the prior bounded metrics exactly, including SafeOCR CFEA 1.0 / UAR 0.0 / coverage 1.0 and Tesseract crop CFEA 0.8333333333333334 / UAR 0.16666666666666666.
