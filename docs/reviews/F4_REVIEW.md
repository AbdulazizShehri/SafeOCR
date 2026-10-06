# F4 Review Evidence

Date: 2026-10-06
Phase: F4 Evidence Verification

## Engineering workflow

pstack source: https://github.com/backnotprop/pstack
- TDD skill SHA: ca6f24c963001d9d518db2936dfe3d12f29b4e94
- blast-radius skill SHA: 1713b283d477530be64e925ede2bdbe5ce2d6e31

Red-first regressions proved and then fixed:
- mismatched independent crop provenance was not initially a runtime hard failure;
- tampered perturbation provenance was not initially a runtime hard failure;
- serialized trace initially retained more linkage identity data than required.

After fixes, provenance failures route fail-closed and trace output retains only structured linkage diagnostics.

## Final gates

- default pytest: 104 passed, 2 runtime tests skipped by design
- focused F4 tests: 52 passed
- explicit F3 + F4 runtime tests: 2 passed
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings
- pip check: PASS
- Graft: 227 nodes, 681 edges, graph check OK
- git diff --check: PASS

## Runtime evidence

Canonical artifact: docs/evidence/F4_RUNTIME_SMOKE.json

Clean LabGold field:
- Paddle full-page read, Tesseract independent crop read, perturbation reads, UCUM validation, and linkage checks all passed;
- terminal decision: VERIFIED_AUTO.

Negative control:
- changed independent value;
- independent_agreement failed;
- terminal decision: REVIEW_REQUIRED.

Additional regressions prove misbound provenance routes to ABSTAINED.

## Review tools

Jev advisory evidence:
- spec coherence: 0.86
- scope boundedness: 0.82
- verifier fail-closed safety: 0.85
- real-runtime evidence sufficiency: 0.91
- focused identifier-minimization review: 0.62
- final F4 closeout after spec/evidence reconciliation: 0.80.

The lower minimization score is advisory uncertainty; executable regression tests directly verify the trace fields and serialized output.

Alibaba Open Code Review 1.12.12 official delegate mode was applied to the production Python and project configuration. No blocking correctness or security finding remains after the provenance fixes.

## Dependency and scope review

- ucumvert 0.3.2 is pinned.
- UCUM validation is case-sensitive and veto-only.
- required notices are recorded in docs/THIRD_PARTY_NOTICES.md and docs/SOURCE_REGISTRY.md.
- no FHIR export, clinical correction, confidence threshold, model training, or benchmark tuning was added in F4.

F5 owns the FHIR R4 export gate.
