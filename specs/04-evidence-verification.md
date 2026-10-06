# F4 â€” Evidence Verification

Status: done
Complexity: high
Depends on: F3 OCR adapters and critical-crop re-reader

## Goal

Convert evidence from F3 into explicit, auditable verification signals for one critical laboratory field, then derive the existing F1 EvidenceRecord and terminal decision.

F4 is the first phase that may produce VERIFIED_AUTO from real OCR evidence.

F4 does not export FHIR and does not correct clinical content.

## Safety thesis

A critical laboratory value may be accepted automatically only when:

1. its source geometry is intact and bound to one source page;
2. analyte, value, and unit are structurally associated on one row;
3. the primary OCR value and independent crop read agree after formatting-only normalization;
4. approved non-destructive perturbation reads are stable;
5. the value syntax is unambiguous;
6. the source unit is valid case-sensitive UCUM;
7. patient/document linkage is unambiguous;
8. every required verification runtime completed successfully.

A failure of any mandatory gate routes to REVIEW_REQUIRED or ABSTAINED through the existing F1 policy.

## 1. Formatting-only evidence normalization

SafeOCR may normalize evidence text only by:
- Unicode NFC normalization;
- trimming leading/trailing whitespace;
- collapsing internal whitespace runs to one ASCII space.

It must not:
- change digits;
- change decimal separators;
- change signs/comparators;
- case-fold evidence for agreement;
- replace visually similar characters;
- fix units;
- use clinical plausibility to alter text.

Examples:
- `  3.4  ` -> `3.4`
- `NOT   DETECTED` -> `NOT DETECTED`
- `6.B` remains `6.B`
- `3,4` remains `3,4`
- `mmol/l` remains `mmol/l`

## 2. Critical value parser

The parser recognizes two explicit families.

### Numeric

Accepted grammar:
- optional comparator: <, <=, >, >=;
- optional sign;
- decimal integer/fraction;
- optional scientific exponent.

Examples:
- `3.4`
- `-2.1`
- `<0.01`
- `>=200`
- `1.2e3`

Rejected as ambiguous:
- `3,4`
- `3..4`
- `approx 3.4`
- `3.4 mg/dL`
- `O.5`

Parsing uses Decimal rather than float.

### Qualitative

Recognized tokens after whitespace normalization only:
- POSITIVE
- NEGATIVE
- DETECTED
- NOT DETECTED
- REACTIVE
- NONREACTIVE
- NON-REACTIVE

Case is preserved in evidence. Recognition may compare an uppercase view, but independent-read agreement remains formatting-only and case-sensitive.

## 3. Field evidence binding

Verification input explicitly names:
- analyte span;
- value span;
- optional unit span;
- exact value CriticalCrop.

Visual grounding passes only if:
- analyte and value spans are present;
- every supplied span is a member of the LabFieldCandidate source_spans;
- all required spans share the same PageAsset;
- the value crop source page equals the value span PageAsset;
- the value crop requested_box equals the value span box.

If the field declares unit_text, a unit span is mandatory for automatic acceptance.

## 4. Structural row association

v0.1 supports same-page table rows only.

The analyte/value/unit relationship passes when:
- all required spans share one page;
- spans overlap vertically by at least 50% of the shorter span height;
- left-to-right order is analyte -> value -> unit when a unit exists.

Any multi-page association is unresolved and cannot auto-verify.

Header inheritance and multi-page continuation are not inferred in v0.1; absence of explicit same-page evidence fails closed.

## 5. Independent agreement

The primary value is LabFieldCandidate.value_text.

The secondary value is the F3 Tesseract CropRead.

Agreement requires exact equality after formatting-only evidence normalization.

An empty or missing secondary read does not count as agreement.

Engine-native confidence cannot override disagreement.

## 6. Perturbation stability

F4 records named perturbation reads.

Approved v0.1 perturbations are deliberately mild:
- brightness 0.95;
- brightness 1.05;
- contrast 1.05;
- scale 1.10.

No rotation, denoise, or destructive crop is part of the automatic gate until separately validated.

A perturbation read records:
- variant name;
- variant image SHA-256;
- OCR text or no text;
- runtime health.

Stability passes only when:
- all four approved variants are present exactly once;
- all four runtimes are healthy;
- every normalized read exactly matches the normalized primary value.

Missing, duplicate, failed, or disagreeing perturbations fail stability.

## 7. UCUM terminology veto

F4 uses `ucumvert==0.3.2` as a local case-sensitive UCUM parser.

The adapter:
- validates the source unit string as-is after formatting-only whitespace normalization;
- records parser package/version;
- never rewrites or converts the source unit;
- never substitutes an expected unit based on analyte identity.

Unit status:
- VALID: parser accepts the exact unit code;
- INVALID: parser rejects it;
- MISSING: no source unit was supplied;
- RUNTIME_ERROR: validator failed unexpectedly.

Only VALID satisfies `unit_valid`.

RUNTIME_ERROR also makes the overall verification runtime unhealthy.

No LOINC-based expected-unit inference is in F4.

## 8. Patient/document linkage

F4 accepts:
- expected patient identifier;
- observed patient identifiers from the document evidence.

Linkage is unambiguous only when:
- expected id is non-empty;
- at least one observed id exists;
- all non-empty observed ids collapse to one unique exact identifier;
- that identifier exactly equals the expected id.

Case-folding, fuzzy matching, and demographic inference are prohibited.

## 9. Runtime health

Overall runtime health is false if:
- independent crop read is unavailable because of runtime failure;
- any perturbation read reports runtime failure;
- UCUM validation reports RUNTIME_ERROR;
- caller supplies another explicit verifier runtime error.

Runtime failure must never be represented as ordinary disagreement.

## 10. F4 output

F4 returns a VerificationTrace containing:
- field binding;
- independent read evidence;
- perturbation evidence;
- unit-validation evidence;
- patient-linkage evidence;
- derived VerificationSignals;
- derived F1 EvidenceRecord.

VerificationTrace serializes deterministically.

The F1 `decide()` function remains the sole terminal decision primitive.

## Dependencies

Add:
- `ucumvert==0.3.2`

License handling:
- ucumvert code is MIT;
- vendored UCUM specification files carry the UCUM Copyright Notice and License;
- preserve required notices in the source/license registry.

## Acceptance criteria

- [x] Formatting normalization changes whitespace/NFC only.
- [x] Formatting normalization never changes digits, punctuation, comparator, sign, or case.
- [x] Strict numeric parser accepts documented numeric forms and rejects ambiguous forms.
- [x] Qualitative parser accepts only the frozen token set.
- [x] Visual grounding fails when required spans/crop bindings are missing or inconsistent.
- [x] Same-page row association requires >=50% vertical overlap and correct column order.
- [x] Multi-page associations fail closed.
- [x] Independent agreement is exact after formatting-only normalization.
- [x] Empty/missing independent read cannot count as agreement.
- [x] Exactly four approved perturbation variants are required.
- [x] Any perturbation disagreement/runtime failure makes stability false.
- [x] UCUM valid unit returns VALID without rewriting the source text.
- [x] UCUM invalid unit returns INVALID.
- [x] Unexpected UCUM adapter failure returns RUNTIME_ERROR.
- [x] Patient linkage requires one exact expected/observed identifier.
- [x] Conflicting/missing patient ids fail linkage.
- [x] F4 derives VerificationSignals without using OCR confidence thresholds.
- [x] Missing visual grounding produces ABSTAINED via F1.
- [x] Runtime failure produces ABSTAINED via F1.
- [x] Agreement/structure/parse/unit/linkage/stability failure produces REVIEW_REQUIRED via F1.
- [x] All mandatory evidence passing produces VERIFIED_AUTO.
- [x] VerificationTrace serialization is deterministic.
- [x] VerificationTrace retains and serializes only structured linkage evidence, not raw linkage identifiers.
- [x] Real LabGold/Paddle/Tesseract runtime smoke reaches VERIFIED_AUTO for one clean Potassium field.
- [x] A deliberately corrupted/disagreeing critical read cannot reach VERIFIED_AUTO.
- [x] pytest, Ruff, Pyright strict, and Graft check pass.

## Hardstops

Do not add:
- FHIR export;
- LOINC analyte mapping;
- expected-unit inference from analyte identity;
- clinical plausibility correction;
- confidence thresholds;
- model training;
- final benchmark threshold tuning.

F5 owns FHIR export.
F6 owns benchmark evaluation and operating-point analysis.
