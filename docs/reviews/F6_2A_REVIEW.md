# F6.2a LabGold Split Freeze Review

Date: 2026-10-06
Phase: F6.2a frozen LabGold split and baseline semantics

## Frozen split

Canonical artifact: `docs/evidence/F6_LABGOLD_SPLIT.json`

SHA-256:

`3aa0af90f3d41d5a0b636ded5d784119da81a193b81a907b7bb69a789cc816a5`

The schedule is preregistered in code and independently checked by `scripts/write_evaluation_split.py`.

- calibration: 12 synthetic records × clean/corrupted = 24 document cases
- final evaluation: 24 synthetic records × clean/corrupted = 48 document cases
- each record has six laboratory rows
- calibration/evaluation patient identities are disjoint
- corruption seeds are unique
- all three LabGold templates are represented in both roles
- final-evaluation seeds are not accepted by the calibration-only API

The benchmark retains all three layouts in final evaluation because only three controlled templates exist; withholding one entire layout would materially reduce layout coverage. Leakage protection therefore freezes identities, record seeds, corruption seeds, and role assignment rather than tuning against a held-out layout.

## Baseline semantics

- primary OCR: accepts a complete extracted field and abstains on incomplete extraction
- Tesseract crop baseline: oracle critical-value crop benchmark; field identity is supplied by benchmark truth and only the crop value read is measured
- naive agreement: accepts only when the primary value and independent crop value exactly agree after formatting-only normalization
- SafeOCR remains separately evaluated through the verification policy; these helpers do not alter SafeOCR thresholds

## Mechanical gates

- focused evaluation tests: 17 passed
- full pytest: 156 passed, 3 runtime tests skipped by design
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings
- pip check: PASS
- git diff --check: PASS
- Graft: 381 nodes / 1190 edges, graph check OK
- manifest writer reproduced the exact preregistered SHA-256

## Jev advisory review

- split/baseline correctness expected-level score: 3.23 / 4
- leakage/preregistration safety expected-level score: 3.67 / 4

## Alibaba Open Code Review

Official delegate preview/rules were applied to `src/safeocr/evaluation.py`, `scripts/write_evaluation_split.py`, and the evaluation tests. No blocking correctness or security finding remains.

## Scope boundary

No final-evaluation OCR output has been used to choose thresholds in this grain. F6.2b may run calibration cases to harden runtime plumbing, then the runner must be frozen before first final-evaluation execution.
