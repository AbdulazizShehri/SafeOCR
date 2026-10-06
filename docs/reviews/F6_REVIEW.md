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

## F6.2d governed attempt 2 — primary LabGold result

Recovery commit `e755e36d0379e11b768b573af0c04bb9559be408` changed only PaddleOCR text-recognition batch size to `1` in the calibration and final runners after attempt 1 exhausted memory. The OCR model identities, SafeOCR verification policy, thresholds, frozen split, corruption seeds, truth, and metric definitions were unchanged. Exact-head recovery qualification passed: 165 tests passed / 4 runtime tests skipped by default; Ruff PASS; Pyright strict 0 errors / 0 warnings / 0 informations; pip check PASS; Graft graph check OK; Jev recovery-contract score 3.63 / 4. Alibaba Open Code Review delegated rules were applied; direct LLM-backed OCR review remained unavailable because the configured Anthropic provider had no API key, so no fabricated LLM review is claimed.

Attempt 2 then executed all 48 frozen final documents / 288 field cases from a clean tree at exact head `e755e36d0379e11b768b573af0c04bb9559be408`. The runner completed successfully in 1496.38 seconds and wrote `docs/evidence/F6_FINAL_EVALUATION.json`. The artifact records `working_tree_dirty=false`, the preregistered split SHA-256 `3aa0af90f3d41d5a0b636ded5d784119da81a193b81a907b7bb69a789cc816a5`, PaddleOCR 3.7.0, and Tesseract 5.4.0.20240606.

Primary result: SafeOCR accepted 209 / 288 fields (72.5694% verified coverage), sent 79 / 288 to review (27.4306%), and observed 0 unsafe accepts (UAR 0.0; 95% Wilson upper bound 0.018048451847580686). Naive agreement accepted 242 / 288 (84.0278% coverage) with 0 observed unsafe accepts. Raw primary OCR observed 0 unsafe accepts at 100% coverage on this synthetic benchmark. The Tesseract crop baseline accepted 287 / 288 and had 45 unsafe accepts (UAR 0.156794425087108).

The OCR-only association scorer evaluated 288 / 288 rows with 0 observed table-association errors and did not use truth geometry for row parsing. Patient-attribution and FHIR-mapping headline rates are not established by this LabGold runner.

Interpretation is deliberately conservative: because raw primary OCR also observed zero accepted errors at full coverage, the frozen LabGold final set does not demonstrate that SafeOCR lowers unsafe accepted error versus the primary OCR baseline. Zero observed SafeOCR errors is reported with its interval and is not interpreted as zero risk or superiority.

## F6.3 external benchmark integration

ClinOCR-Bench is pinned to upstream commit `3b720a951bb7eec4a4f4fb34a636e7335a19981e`. The official `oneshot_lookup.json` was fetched from that exact commit only; no evaluation image or ground-truth transcript was opened. Its SHA-256 is `e0a8988ac5661b147f3712882cc1857b551c3dc02766cbda399352c48d58746b`.

The adapter reconstructs the published 384-document universe from the 328 evaluation records plus their 56 unique exemplar references and validates that every homogeneous/heterogeneous one-shot donor resolves only to the exemplar role. The Safety Track manifest is zero-shot for SafeOCR v0.1 and fixes `threshold_tuning_allowed=false`. Any attempt to route external-evaluation records into a calibration/tuning path raises an error.

The integration deliberately does not fabricate SafeOCR critical-field results from transcript-only truth. ClinOCR-Bench v1.0 provides human-audited full-document transcriptions, not SafeOCR field/patient/FHIR annotations. External critical-field outcome claims therefore remain withheld until a separately governed annotation protocol exists.

Canonical metadata evidence: `docs/evidence/F6_CLINOCR_METADATA.json`. It records 384 total documents, 56 exemplars, 328 evaluation documents, subset evaluation counts, the pinned upstream commit and lookup hash, and explicit `false` flags for opening evaluation images/ground truth or inspecting external outcomes.

## F6.4 deterministic closeout

`docs/evidence/F6_RISK_COVERAGE.csv` freezes the preregistered operating points for raw primary OCR, Tesseract crop, naive agreement, and SafeOCR from the immutable primary LabGold result. No post-hoc threshold sweep is performed after final-set inspection.

`docs/evidence/F6_CLOSEOUT.json` reports the SafeOCR fixed-policy metrics, ClinOCR integration lock, and explicit limitations. FHIR mapping error rate is `null`/not estimable from F6 because the preregistered final runner did not perform per-field FHIR export; F5 validator conformance remains separate interoperability evidence. This avoids relabeling conformance evidence as a benchmark mapping-error estimate.

## F6 closeout qualification

Final closeout gates: 175 tests passed / 4 runtime tests skipped by default; Ruff PASS; Pyright strict 0 errors / 0 warnings / 0 informations; pip check PASS; `git diff --check` PASS; Graft 478 nodes / 1529 edges with graph check OK.

Jev F6 closeout governance score: 3.90 / 4 (91% excellent, 9% strong), specifically evaluating no-test-set-tuning, conservative interpretation, and avoidance of unsupported ClinOCR-Bench safety claims.

Alibaba Open Code Review delegate preview/rules covered the new ClinOCR adapter, metadata validator, F6 closeout builder, tests, and JSON evidence surface. The delegated correctness/security rules produced no blocking host-agent finding. A direct LLM-backed `ocr review` is not claimed because the configured Anthropic OCR provider has no API key; this limitation is explicit rather than fabricated.
