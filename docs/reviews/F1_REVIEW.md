# F1 Review Evidence

Date: 2026-10-06
Phase: F1 Foundation contracts
Review scope: staged F1 implementation

## Mechanical gate

- pytest: 21 passed
- ruff: PASS
- pyright strict: 0 errors, 0 warnings
- Graft wiring graph: 34 nodes, 78 edges
- Graft graph check: OK

## Jev

Jev was used as an advisory independent checker, not as proof of correctness.

Final safety question before closeout returned 0.96 probability that the stated fail-closed invariants are structurally enforced.

Earlier review passes exposed scope/spec ambiguity and led to additional tests and tighter contracts.

## Alibaba Open Code Review

CLI: open-code-review 1.12.12

The configured Anthropic provider currently has no API key, so direct LLM review could not run. The official `ocr delegate` mode was used instead:

- `ocr delegate preview` identified the reviewable F1 code surface.
- `ocr delegate rule` supplied the Python/default review rules.
- The host-agent review applied those rules to the full source and test diff.

Findings resolved during review:

1. **Evidence record gap** — the spec required deterministic evidence records but the first implementation only had DecisionRecord.
   - Fixed by adding EvidenceRecord.
   - EvidenceRecord recomputes and validates the supplied decision from signals.
   - Deterministic evidence serialization is tested.

2. **Weak export boundary** — the first export helper accepted a DecisionState directly.
   - Fixed so `export_allowed` requires a validated EvidenceRecord.
   - REVIEW_REQUIRED cannot pass automatic export.
   - Inconsistent manually supplied decisions are rejected by EvidenceRecord.

3. **Runtime truthiness risk** — Python type hints alone allowed non-boolean values such as strings to reach verification signals.
   - Fixed by exact runtime bool validation.
   - Regression test added.

4. **Cross-document evidence risk** — a laboratory field could initially reference spans from multiple source documents.
   - Fixed by requiring all field evidence spans to share one document hash.
   - Regression test added.

Final delegated review: no remaining blocking correctness/security findings identified in F1.

## Focused closeout Jev review

Using only the F1 spec, implementation, tests, and review evidence:

- acceptance support: 0.87
- fail-closed foundation: 0.90

These are advisory probabilities, not correctness proofs.

## Limitations

- No external Alibaba OCR LLM verdict is claimed because no provider API credential is configured.
- Graft deep semantic enrichment was not used; the deterministic wiring graph is current.
- This review covers F1 contracts only, not OCR model behavior, FHIR semantics, or clinical deployment.
