# F5 — FHIR R4 Export Gate

Status: in progress
Complexity: high
Depends on: F4 Evidence Verification + HMAC patient-binding prerequisite

## Goal

Export one VERIFIED_AUTO numeric laboratory field as deterministic FHIR R4 (4.0.1) JSON while preserving source-document and SafeOCR provenance, and release it only after the pinned official validator succeeds.

F5 is an export gate, not a clinical inference layer.

## Core rule

No FHIR clinical resource is emitted unless the supplied F4 VerificationTrace is internally consistent, terminally VERIFIED_AUTO, and the caller-supplied patient identifier verifies against the F4 HMAC patient-binding tag.

REVIEW_REQUIRED and ABSTAINED evidence is never represented as a successful clinical FHIR export.

## 1. Supported FHIR release and validator

Target specification: HL7 FHIR R4 version 4.0.1.

Authoritative release validator:
- repository: hapifhir/org.hl7.fhir.core
- release: 6.10.4
- artifact: validator_cli.jar
- artifact SHA-256: 1106b9d58f9e363e47bea7c4fc065841e5fc91fe9d062775c3bfdd212bd653cc
- Java runtime: 17 or newer.

Validation is run explicitly with FHIR version 4.0.1.

Remote terminology validation is disabled for the local v0.1 gate. F4 already performs exact UCUM validation, and F5 emits no inferred LOINC code. Validator warnings are recorded; any error/fatal validation result blocks export release.

## 2. No model-library dependency

FHIR resources are constructed as transparent typed Python mappings and validated by tests plus the official validator.

F5 does not depend on fhir.resources R5/R4B models and does not silently upgrade R4 semantics.

## 3. Export context

The caller supplies:
- patient_identifier_system: explicit URI namespace;
- patient_identifier_value: exact identifier intended for FHIR subject;
- patient_binding_key: same external secret used to create the F4 HMAC binding;
- source_content_type: explicit MIME type for the source document;
- recorded_at: explicit UTC FHIR instant for Provenance.recorded.

The caller does not supply:
- clinical value;
- analyte name;
- unit;
- verification state;
- document SHA;
- policy version.

Those come only from verified evidence.

## 4. Patient identity binding

Before export:
1. F4 patient linkage must be exact.
2. F4 must contain a matched_identifier_hmac_sha256 tag.
3. The caller-supplied patient_identifier_value is normalized using the same formatting-only normalization as F4.
4. F5 recomputes the HMAC using patient_binding_key.
5. Comparison uses constant-time comparison.

A mismatch blocks export.

The HMAC key is never serialized into FHIR, provenance, evidence JSON, logs, or IDs.

## 5. Trace consistency gate

F5 rechecks before mapping:
- evidence_record.field equals binding.field;
- evidence_record.signals equals trace.signals;
- evidence_record decision is VERIFIED_AUTO;
- parsed_value exists and corresponds to the field value;
- unit validation is VALID and matches the field source unit;
- patient-linkage evidence is exact;
- source spans resolve to one document SHA-256;
- no runtime error is present.

F5 does not trust a manually constructed VerificationTrace merely because one nested decision says VERIFIED_AUTO.

## 6. v0.1 numeric-only export

F5 v0.1 exports numeric critical values only.

Supported:
- decimal numeric value;
- optional comparator <, <=, >, >=;
- exact source UCUM unit.

Qualitative F4 values are not exported by F5 v0.1 even if parsed; they fail closed until a separately reviewed FHIR valueCodeableConcept policy exists.

Decimal conversion must be lossless for the emitted JSON number. If Python numeric conversion would change the Decimal value, export is blocked rather than rounded.

## 7. Deterministic resource identities

Resource IDs are UUIDv5 values derived from:
- a fixed SafeOCR namespace;
- an export-identity SHA-256;
- resource role.

The export-identity SHA-256 binds:
- the deterministic VerificationTrace SHA-256;
- patient identifier system;
- the verified patient HMAC binding tag (never the raw key);
- source content type;
- explicit Provenance recorded instant.

This prevents the same resource IDs from being reused when caller-controlled export context changes while preserving deterministic repeated exports for identical inputs.

Resources emitted:
1. DocumentReference
2. Observation
3. DiagnosticReport
4. Provenance

All Bundle fullUrl values use urn:uuid references.

The Bundle is type collection and has deterministic entry ordering.

## 8. DocumentReference mapping

DocumentReference represents the exact source document identity.

Required mapping:
- status = current;
- masterIdentifier.system = urn:safeocr:document-sha256;
- masterIdentifier.value = source document SHA-256 from F4 spans;
- subject = caller-supplied patient identifier after HMAC verification;
- content.attachment.contentType = source_content_type;
- content.attachment.title = SafeOCR source laboratory document.

v0.1 does not invent an Attachment.url and does not embed source bytes by default. Pixel coordinates and OCR evidence remain in the sidecar evidence manifest.

FHIR Attachment.hash is not used for the SafeOCR SHA-256 because R4 defines Attachment.hash specifically as SHA-1.

## 9. Observation mapping

Observation mapping:
- status = unknown because source clinical finality is not modeled by F4;
- identifier contains the evidence-trace SHA-256;
- code.text = exact verified analyte source text;
- subject = HMAC-verified caller patient identifier;
- valueQuantity.value = lossless numeric value;
- valueQuantity.comparator = parsed comparator when present;
- valueQuantity.unit = exact source unit text;
- valueQuantity.system = http://unitsofmeasure.org;
- valueQuantity.code = exact validated UCUM unit;
- derivedFrom references the source DocumentReference.

F5 does not invent LOINC coding.

## 10. DiagnosticReport mapping

DiagnosticReport mapping:
- status = unknown because report finality is not modeled by F4;
- code.text = Laboratory report;
- subject = HMAC-verified caller patient identifier;
- result references the exported Observation.

No result timestamp or specimen is invented when absent from verified evidence.

## 11. Provenance mapping

Provenance mapping:
- target references the Observation and DiagnosticReport;
- recorded = explicit caller-supplied UTC instant;
- activity uses the standard FHIR R4-bound http://terminology.hl7.org/CodeSystem/v3-DataOperation#CREATE code;
- agent.who.identifier identifies safeocr-health under urn:safeocr:software;
- entity role source references the source DocumentReference;
- a second source entity uses identifier system urn:safeocr:evidence-sha256 with the trace SHA-256;
- policy references the exact SafeOCR verification policy version as a local urn.

No custom FHIR extension is introduced in v0.1.

## 12. Deterministic artifact

F5 returns an immutable FhirExportArtifact containing:
- bundle mapping;
- evidence_sha256;
- bundle_sha256;
- deterministic canonical JSON.

Repeated export from identical trace + context must produce byte-identical JSON.

## 12A. Structural release gate

The production export_verified_lab_field API does not return an unvalidated FHIR bundle.

Flow:
1. a private mapper builds an unreleased candidate;
2. candidate canonical bytes are SHA-256 checked before validation;
3. the candidate is written atomically into the caller-supplied local validation workspace;
4. the pinned official R4 validator must succeed;
5. the exact validated file SHA-256 is rechecked after validation;
6. only then is a ValidatedFhirExportArtifact returned.

If validation fails or the validated file changes, the candidate JSON is removed and no release object is returned.

The private candidate mapper exists only to keep mapping logic unit-testable; it is not the production release API.

## 13. Fail-closed validator wrapper

The validator runner:
- invokes Java with argv and shell disabled;
- forces UTF-8 with -Dfile.encoding=UTF-8 before loading the validator JAR;
- uses the pinned validator_cli.jar only after SHA-256 verification;
- passes version 4.0.1 explicitly;
- disables remote terminology service for the local structural gate;
- has an explicit timeout;
- captures stdout/stderr;
- treats missing Java/JAR, checksum mismatch, timeout, non-zero process result, or validator errors as export-validation failure.

Successful validation evidence records validator release, JAR SHA-256, FHIR version, command mode, and warning count.

## 14. Security/privacy boundaries

- FHIR output intentionally contains the caller-approved patient identifier after cryptographic binding verification.
- The patient-binding key is never serialized.
- The source document bytes are not duplicated into FHIR by default.
- The raw F4 patient identifier is not reintroduced into the evidence sidecar.
- No network call is required after validator/core-package bootstrap.
- No clinical correction or plausibility inference occurs in F5.

## Acceptance criteria

- [x] REVIEW_REQUIRED evidence cannot export.
- [x] ABSTAINED evidence cannot export.
- [x] A manually inconsistent VerificationTrace cannot export.
- [x] HMAC patient mismatch cannot export.
- [x] Weak/invalid patient binding key cannot export.
- [x] Invalid patient identifier system cannot export.
- [x] Invalid source MIME type cannot export.
- [x] Invalid/non-UTC Provenance instant cannot export.
- [x] Qualitative value cannot export in v0.1.
- [x] Lossy Decimal conversion cannot export.
- [x] DocumentReference uses the verified document SHA-256 and does not misuse Attachment.hash.
- [x] Observation uses exact analyte/value/comparator/UCUM evidence and status unknown.
- [x] DiagnosticReport references the Observation and uses status unknown.
- [x] Provenance targets Observation + DiagnosticReport and references both source DocumentReference and evidence-trace SHA-256.
- [x] Patient subject identifier is emitted only after HMAC verification.
- [x] No HMAC key appears anywhere in serialized FHIR.
- [x] Resource IDs/fullUrl references are deterministic.
- [x] Changing export context changes deterministic resource identity.
- [x] Repeated export produces byte-identical canonical JSON.
- [x] Official HL7 validator 6.10.4 validates the sample bundle as R4 4.0.1 with zero errors/fatal findings.
- [x] A deliberately invalid FHIR sample is rejected by the validator gate.
- [x] Validator JAR checksum mismatch is rejected before Java execution.
- [x] Public export returns only after validator success.
- [x] Validator failure removes the unreleased candidate file.
- [x] Any validator exception removes the unreleased candidate file.
- [x] Post-validation file-hash changes block release.
- [x] pytest, Ruff, Pyright strict, Graft check, Jev, and Alibaba delegated review pass.

## Hardstops

Do not add:
- FHIR R4B/R5 mapping;
- LOINC inference;
- qualitative-result FHIR policy;
- source-document upload/server storage;
- FHIR server/network client;
- custom FHIR extensions;
- terminology server dependency;
- clinical correction;
- benchmark operating-point tuning.

F6 owns evaluation.
