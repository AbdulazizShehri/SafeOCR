# SafeOCR Engineering Rules

## Product boundary

SafeOCR v0.1 is healthcare-only and laboratory-report-only.

## Stack

- Python 3.11/3.12
- pytest
- ruff
- pyright strict
- CPU-first reference path
- FHIR R4 later in the roadmap

## Build discipline

- Follow the active spec in `specs/`.
- Acceptance criteria become tests before implementation.
- Prefer immutable typed contracts and deterministic pure functions.
- Fail closed: exceptions or missing mandatory verification never permit export.
- Engine confidence is data, never a calibrated correctness probability by assumption.
- Clinical knowledge may veto but never rewrite pixels.
- No paid API or real PHI is required for tests.

## Review discipline

Required before closing a phase:
- mechanical gate: ruff + pyright + pytest;
- Jev advisory verification;
- Alibaba Open Code Review (`ocr`);
- Graft map/check for codebase context and blast-radius awareness.

## Capabilities

- workflow: pstack global skills
- code map: Graft 0.21.1
- plan/logic verification: Jev CLI
- code review: Alibaba Open Code Review CLI (`ocr`)
- web docs: available through the active ChatGPT harness
- browser/UI: not required for F1
- model tiers: unavailable in this harness; use the current session model
