# Ma2023 Delegated Alibaba Open Code Review Evidence

Date: 2026-10-06
Review mode: Alibaba Open Code Review `ocr delegate` (host-agent delegation; no external LLM required)
Jev: 1.13.0

## Scope

- `paper/MA2023_EXTERNAL_COMPONENT_PROTOCOL.md`
- `src/safeocr/ma2023.py`
- `scripts/run_ma2023_external_ocr.py`
- `scripts/score_ma2023_external_verifier.py`
- `tests/test_ma2023_external.py`

## Review result

One blocking reproducibility defect was identified before external execution.

### Blocking finding — stale resume outputs could mix exact heads

The initial OCR runner skipped pre-existing JSON outputs by filename only. After an interrupted run, a later run from a different source head, engine fingerprint, or dataset byte state could have reused those files and then emitted metadata for the new run. That could create mixed-head evidence.

Resolution:
- compute SHA-256 for every evaluation image;
- freeze a dataset-manifest SHA-256;
- persist an exact `_run_state.json`;
- require resumed outputs to match the frozen run state;
- validate each reused output against the expected source-image hash and engine fingerprint;
- record dataset-manifest and run-state hashes in final metadata;
- add regression coverage that rejects a changed git head.

Status: FIXED before external Ma2023 OCR execution.

## Leakage and claim-boundary review

No blocking annotation-leakage path was found:
- the OCR runner has no labels/annotation argument;
- the runner attests `annotation_source_opened=false` and `tuning_performed=false`;
- gold annotations are opened only by the scorer after OCR-run attestations are checked;
- gold geometry is used only for oracle-localised component evaluation after OCR inference;
- the frozen protocol prohibits reporting this as end-to-end extraction or full SafeOCR policy evaluation;
- patient linkage, FHIR mapping, deployment safety, and prospective clinical utility remain outside the allowed claim boundary.

## Qualification

- Pytest: 5/5 PASS
- Ruff: PASS
- Pyright: 0 errors, 0 warnings, 0 information
- Jev final score: 3.57 / 4
- Jev blocker probability: 0.01
- Remaining delegated Alibaba blocking findings: 0

The direct `ocr review` LLM path was unavailable because the configured Anthropic provider had no API credential. The official `ocr delegate` path was therefore used as intended for host-agent review without a paid external LLM.


## Pre-outcome runtime compatibility repair

The first scoring launch terminated before producing any verifier metric because the public Ma2023 source files are JPEG images while SafeOCR's existing critical-crop contract accepts PNG bytes.

Observed failure:
- `ValueError: critical-crop source must be PNG`
- no result artifact was produced;
- no verifier outcome, accepted-error rate, coverage result, or stratum result was inspected.

Repair:
- decode the source JPEG through Pillow;
- re-encode the decoded RGB pixels losslessly as PNG bytes solely for the existing crop contract;
- do not alter OCR outputs, field matching, thresholds, model selection, cohort, eligibility rules, perturbations, or metrics;
- require the scorer itself to start from a clean exact git head;
- record `scorer_git_head` and `scorer_working_tree_dirty` in the result artifact;
- add regression coverage for the JPEG-to-PNG normalization and scorer exact-head requirement.

Post-repair qualification:
- Pytest: 6/6 PASS
- Ruff: PASS
- Pyright: 0 errors, 0 warnings, 0 information
- Jev repair score: 3.18 / 4
- Delegated Alibaba blocking findings after repair: 0

This repair occurred before any Ma2023 verifier outcome was available and does not change the frozen scientific estimand.


## Pre-outcome page-identity repair

A second fail-closed runtime stop occurred before any result artifact was produced. The JPEG source had been decoded and re-encoded as PNG correctly, but the OCR spans still referenced the original JPEG `PageAsset.page_sha256`. The crop contract therefore rejected the normalized PNG bytes because their SHA-256 differed.

Resolution:
- preserve the original JPEG digest as `document_sha256`;
- create a normalized evidence `PageAsset` with the identical page index and dimensions but a SHA-256 computed from the normalized PNG bytes;
- rebind the already-produced OCR spans to that normalized page without changing box coordinates, OCR text, confidence, engine identity, or fingerprint;
- use the normalized page only for evidence cropping and verifier checks;
- keep gold annotations entirely outside this normalization path.

Qualification after repair:
- Pytest: 6/6 PASS
- Ruff: PASS
- Pyright: 0 errors, 0 warnings, 0 information
- Jev score: 3.38 / 4
- Delegated Alibaba blocking findings: 0

No Ma2023 verifier metric or outcome had been produced or inspected before this repair.
