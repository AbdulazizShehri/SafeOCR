# F3 Review Evidence

Date: 2026-10-06
Phase: F3 OCR adapters and critical-crop re-reader

## Mechanical gate before runtime closeout

- pytest: 52 passed
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings
- Graft wiring graph: 121 nodes, 329 edges
- Graft graph check: OK

## Jev advisory review

Pre-runtime:
- spec alignment: 0.89
- adapter safety boundary: 0.86

Jev is advisory evidence, not proof.

## Alibaba Open Code Review

CLI: open-code-review 1.12.12.

Direct provider review is unavailable because no Anthropic API key is configured. Official `ocr delegate` mode was used to resolve Python correctness/security review rules, and the host-agent applied them to:
- `src/safeocr/ocr.py`
- `scripts/smoke_ocr_runtime.py`
- `pyproject.toml`
- F3 tests

## Findings fixed

### NumPy-style Paddle outputs

The first normalizer accepted Python `Sequence` values only. Real PaddleOCR returns `rec_scores` and `rec_boxes` as NumPy arrays.

Fix:
- added array-like `tolist()` normalization without introducing NumPy as a SafeOCR core dependency;
- added a red/green regression test.

### Runtime reproducibility

The initial smoke was ad hoc.

Fix:
- added `scripts/smoke_ocr_runtime.py`;
- pinned optional runtime packages;
- generated `docs/evidence/F3_RUNTIME_SMOKE.json`;
- pinned ONNX and Tesseract English data hashes.

## Real runtime smoke

Reference host:
- Windows 11
- Python 3.12.13
- PaddleOCR 3.7.0
- PaddleX 3.7.2
- ONNX Runtime 1.23.2 CPU
- PP-OCRv6 small detector + recognizer
- Tesseract 5.4.0.20240606

Observed:
- normalized Paddle spans: 37
- all normalized boxes inside the LabGold page: PASS
- Paddle detected the clean Potassium truth value `3.4`: PASS
- Tesseract re-read the exact critical crop as `3.4`: PASS

## Scope check

F3 does not decide VERIFIED/REVIEW/ABSTAIN and does not perform clinical correction. Those remain F4 responsibilities.

## Runtime pytest gate

- SAFEOCR_RUN_OCR_SMOKE=1 pytest tests/test_ocr_runtime_smoke.py -q: 1 passed
- the first attempt exposed a host Temp-directory permission issue; the runtime test was made independent of the host-global pytest temp root by using the git-ignored .jev workspace

## Final closeout

- normal pytest gate: 52 passed, 1 runtime smoke skipped by default
- explicit real-runtime pytest gate: 1 passed
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings
- Graft: 136 nodes / 380 edges, graph check OK
- Jev closeout: 0.79
- Jev final safety boundary: 0.95
