# F5 Review Evidence

Date: 2026-10-06
Phase: F5 FHIR R4 export gate

## Mechanical gate

- normal pytest: 139 passed, 3 runtime tests skipped by default
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings
- Graft: 333 nodes / 1063 edges, graph check OK
- git diff --check: PASS

## Official FHIR runtime

- validator: HL7-maintained validator CLI 6.10.4
- FHIR version: 4.0.1
- validator JAR SHA-256: 1106b9d58f9e363e47bea7c4fc065841e5fc91fe9d062775c3bfdd212bd653cc
- valid bundle: 0 errors, 7 warnings, 1 note
- deliberately invalid control: rejected with 2 errors
- explicit runtime pytest: 1 passed
- exact-tree official runtime pytest: 1 passed after final safety hardening
- canonical evidence: docs/evidence/F5_RUNTIME_SMOKE.json

## Warning disposition

The seven validator warnings are intentionally retained rather than silenced by inventing clinical facts:

1. DocumentReference missing narrative XHTML (dom-6) â€” best-practice recommendation only.
2. Observation missing performer â€” SafeOCR has no verified performer evidence and must not invent one.
3. Observation missing effective[x] â€” SafeOCR has no verified effective time in F5.
4. UCUM code cannot be terminology-validated because validator runs with -tx n/a; F4 separately validates the exact unit locally with pinned ucumvert.
5. Observation missing narrative XHTML (dom-6) â€” best-practice recommendation only.
6. DiagnosticReport missing narrative XHTML (dom-6) â€” best-practice recommendation only.
7. Provenance missing narrative XHTML (dom-6) â€” best-practice recommendation only.

The previous local Provenance activity warnings were removed by using the standard R4-bound v3-DataOperation#CREATE code. The Java platform-encoding startup warning was removed by forcing UTF-8 before -jar.

## Hardening findings fixed

### Patient identity binding

F4 stores only a domain-separated HMAC-SHA256 binding tag for an exact patient-id match. F5 recomputes it from caller-supplied patient identity with the same external key and uses constant-time comparison. The raw key is never serialized.

### Export identity collision

Initial resource UUIDs were derived from evidence only, so changing caller-controlled export context could reuse IDs with different resource content. F5 now derives resource UUIDs from an export-identity hash that binds evidence SHA-256, patient identifier system, verified patient HMAC tag, source content type, and explicit Provenance recorded instant.

### Provenance activity interoperability

Initial mapping used a SafeOCR-local activity code. F5 now uses the standard FHIR R4 provenance activity code http://terminology.hl7.org/CodeSystem/v3-DataOperation#CREATE; SafeOCR identity remains in Provenance.agent and policy.

### Validator encoding

The local validator invocation forces -Dfile.encoding=UTF-8 for deterministic Windows behavior.

## Review status

- Jev functional acceptance: 3.21 / 4 expected-level score (57% strong, 35% excellent)
- Jev safety/interoperability: 3.55 / 4 expected-level score (43% robust, 56% excellent)
- Alibaba Open Code Review delegate preview/rules: applied to the final reviewable workspace; no blocking finding remains

### Runtime assert hardening

Alibaba delegated review rules prohibit relying on `assert` for safety-relevant runtime validation. Four internal asserts in `fhir.py` were replaced with explicit fail-closed checks so optimized Python cannot weaken the export gate.

### Structural release gate

A final Jev closeout scored 0.67 and correctly identified that the mapper could return an artifact before official validation. The public export API was refactored so the mapper is private and unreleased. The public export function now writes an exact-hash candidate, requires successful pinned validator execution, rechecks the validated file hash, and only then returns a validated release object. Validator failure, unexpected validator exception, or post-validation tampering removes the candidate and returns no release object.

### Public validated release runtime

After the structural release-gate refactor, the exact current tree was exercised through `export_verified_lab_field` itself. The runtime pytest passed 1/1 using HL7 validator 6.10.4. The returned validated path is named by the exact bundle SHA-256, validator errors remain zero, seven documented warnings remain, and the deliberately invalid control remains rejected. Canonical evidence was refreshed from that exact runtime.

## Exact-tree final runtime

- official-validator runtime pytest on the current working tree: 1 passed in 72.51s
- canonical evidence content matches the exact-tree runtime payload: bundle SHA-256 a32634e68edd221cf919f2259c7f8481b15495b49099c5cb44b3f8405633df65; evidence SHA-256 f18df5c928e21b57bc159eb3a3356c75c26b61d394b193f04ae43f5e9993fb0d
- validator result: 0 errors, 7 documented warnings, 1 note
- invalid control: rejected with 2 errors

## Final closeout rerun

The final uncommitted tree was requalified after the structural release-gate hardening:

- default pytest: 139 passed, 3 skipped
- Ruff: PASS
- Pyright strict: 0 errors, 0 warnings, 0 informations
- pip check: PASS
- git diff --check: PASS
- Graft rebuild/check: 333 nodes, 1063 edges, graph check OK
- official-validator runtime pytest: 1 passed in 72.51s
- canonical FHIR smoke refreshed from this tree: 0 errors, 7 warnings, 1 note; invalid control rejected with 2 errors
- Jev functional acceptance expected-level score: 3.21 / 4
- Jev fail-closed safety/interoperability expected-level score: 3.55 / 4
- Alibaba Open Code Review delegate preview/rules applied to all reviewable F5 production/config files

No blocking correctness, security, or interoperability finding remains. F5 is ready for exact-head commit and remote publication.