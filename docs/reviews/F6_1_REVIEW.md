# F6.1 Evaluation Contracts Review

Date: 2026-10-06
Phase: F6.1 deterministic evaluation contracts

## TDD evidence

The evaluation test module was created before the production module. Initial collection failed with ModuleNotFoundError: safeocr.evaluation, proving the red state. The implementation then made the focused suite pass.

## Implemented contract

- typed evaluation method and role enums;
- typed truth, prediction, field-evaluation, aggregate metrics, and risk/coverage records;
- exact normalized analyte/value/unit comparison with row association;
- explicit accepted/review/abstain denominators;
- unsafe accepted error accounting;
- patient attribution, table association, and FHIR mapping error denominators;
- 95% Wilson interval with explicit zero-denominator behavior;
- zero observed events retain a non-zero upper confidence bound;
- calibration-only guard rejects held-out evaluation and external-evaluation records.

## Mechanical gates

- focused F6.1 pytest: 8 passed
- full pytest: 147 passed, 3 runtime tests skipped by design
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings
- pip check: PASS
- git diff --check: PASS
- Graft: 361 nodes / 1133 edges, graph check OK

## Jev advisory review

- functional correctness expected-level score: 3.20 / 4
  - 53% strong
  - 36% excellent
- leakage/metric safety expected-level score: 3.35 / 4
  - 51% robust
  - 43% excellent

Jev is advisory evidence, not proof of correctness.

## Alibaba Open Code Review

Official delegate mode was applied to the workspace. The reviewable production surface is src/safeocr/evaluation.py; resolved Python rules were also applied to 	ests/test_evaluation.py.

No blocking correctness or security finding remains after host-agent review against the delegated rules.

## Scope boundary

F6.1 does not run OCR, inspect final benchmark outcomes, tune thresholds, download ClinOCR-Bench, or claim clinical performance. It only freezes deterministic evaluation semantics. F6.2 owns the LabGold split manifest and baseline runners.