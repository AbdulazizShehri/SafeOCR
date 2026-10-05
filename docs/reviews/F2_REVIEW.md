# F2 Review Evidence

Date: 2026-10-06
Phase: F2 SafeOCR-LabGold harness
Review scope: staged F2 implementation

## Mechanical gate

- pytest: 36 passed
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings
- Graft wiring graph: 74 nodes, 194 edges
- Graft graph check: OK

## Jev

Jev was used as an advisory independent checker, not as proof of correctness.

Pre-closeout:
- benchmark-integrity question: 0.80
- acceptance question: 0.64 before acceptance checkboxes were reconciled to passing tests

The low acceptance signal triggered a spec-versus-evidence reconciliation rather than being ignored.

## Alibaba Open Code Review

CLI: open-code-review 1.12.12.

The configured Anthropic provider still has no API credential, so direct LLM review cannot be claimed. Official `ocr delegate` mode was used:
- delegate preview resolved the F2 review surface;
- delegate rules supplied Python/default correctness and security rules;
- the host-agent applied those rules to labgold.py, the golden-update script, pyproject metadata, and tests.

## Review finding fixed

### Golden drift could be silently skipped

The initial golden test skipped whenever any renderer fingerprint field differed. That could hide renderer drift on the canonical platform.

Fix:
- skip only when the platform itself differs from the runtime-bound golden;
- on the canonical platform, require the entire renderer fingerprint to match before checking hashes;
- fresh-process determinism now runs for all three templates rather than Classic only.

## Final review bars

- correctness: PASS — typed truth, exact draw-time regions, deterministic seeded corruption, runtime-bound golden, no post-hoc geometry inference
- parsimony: PASS — Pillow only; no OCR/FHIR/OpenCV/UI scope creep
- product/spec: PASS — all F2 acceptance criteria are backed by passing tests
- security: no new external-input execution surface; generated data are local and synthetic

## Limitations

- Golden hashes are intentionally canonical-runtime-specific: Windows x64 + Python 3.12. Other supported runtimes validate determinism without claiming portable pixel hashes.
- F2 does not establish OCR accuracy or clinical safety.
- No real PHI or external clinical dataset is used.
- Direct Alibaba LLM review is not claimed; delegate mode was used because no provider key is configured.
