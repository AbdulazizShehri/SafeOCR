# F1 — Foundation Contracts

Status: done
Complexity: medium
Depends on: F0 architecture freeze

## Goal

Define the immutable typed contracts and fail-closed decision primitive that every later SafeOCR phase must use.

## Requirements

1. Source evidence is represented by a page asset identified by SHA-256, page index, and pixel geometry.
2. OCR proposals are represented as candidate spans bound to source geometry and exact engine identity.
3. Laboratory fields carry criticality and explicit source-span references.
4. Verification inputs are explicit booleans; engine confidence is not a decision probability.
5. The terminal automation states are exactly:
   - VERIFIED_AUTO
   - REVIEW_REQUIRED
   - ABSTAINED
6. Automatic export is permitted only for VERIFIED_AUTO.
7. The decision function is deterministic and fail-closed.
8. Foundation contracts must serialize deterministically for evidence manifests.

## Decision policy for F1

For a critical laboratory field:

- If no candidate value exists: ABSTAINED.
- If source visual grounding is absent: ABSTAINED.
- If the verification runtime did not complete safely: ABSTAINED.
- If any remaining mandatory gate fails: REVIEW_REQUIRED.
- Only when every mandatory gate passes: VERIFIED_AUTO.

Mandatory gates:
- visual grounding;
- independent critical-crop agreement;
- perturbation stability;
- structural analyte/value/unit association;
- numeric/comparator/sign parsing unambiguous;
- unit check valid;
- patient/document linkage unambiguous;
- verification runtime healthy.

## Acceptance criteria

- [x] Invalid or inverted bounding boxes are rejected.
- [x] Invalid SHA-256 values are rejected.
- [x] CandidateSpan requires non-empty engine name/version and source text.
- [x] VerificationSignals reject non-boolean runtime values.
- [x] A missing candidate produces ABSTAINED.
- [x] Missing visual grounding produces ABSTAINED.
- [x] Verification runtime failure produces ABSTAINED.
- [x] Any non-runtime mandatory-gate failure produces REVIEW_REQUIRED.
- [x] All mandatory gates passing produces VERIFIED_AUTO.
- [x] The export gate accepts a validated EvidenceRecord and permits only its VERIFIED_AUTO decision.
- [x] EvidenceRecord binds field + signals + derived decision, rejects inconsistent decisions, and serializes deterministically.
- [x] One laboratory field cannot combine evidence spans from different source documents.
- [x] ruff, pyright strict, and pytest pass.

## Hardstop

Do not add OCR libraries, FHIR libraries, UI code, terminology data, or benchmark rendering in F1.
