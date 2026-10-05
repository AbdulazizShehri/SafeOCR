# SafeOCR Product

SafeOCR is healthcare-only verification infrastructure for clinical OCR.

## v0.1 promise

Given a laboratory report, SafeOCR may propose structured laboratory fields, but it permits automatic FHIR export only when each critical field is bound to source pixels and passes a transparent, fail-closed verification policy.

## User value

- See exactly which source pixels support a clinical value.
- Distinguish verified automation from review-required and abstained fields.
- Prevent unresolved critical fields from silently entering structured health data.
- Reproduce every acceptance decision from pinned evidence.

## Non-goals

- diagnosis;
- treatment recommendation;
- automatic clinical correction;
- general-purpose OCR;
- medication extraction in v0.1;
- claims of clinical effectiveness or medical-device readiness.
