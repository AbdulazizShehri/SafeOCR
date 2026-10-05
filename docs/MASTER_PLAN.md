# SafeOCR Master Plan

Status: architecture freeze candidate  
Target: SafeOCR v0.1 research-grade public release  
Domain: healthcare only  
Primary objective: minimize incorrectly accepted safety-critical clinical fields while preserving useful automated coverage.

## 1. Product thesis

SafeOCR is not an OCR foundation model and not a generic document parser.

SafeOCR is a risk-limiting verification gateway between clinical-document pixels and structured health data. OCR engines propose readings. SafeOCR decides whether each clinical field is sufficiently supported to be automatically exported, must be reviewed, or must be withheld.

The central research question is:

> How low can the accepted error rate for safety-critical clinical fields be driven while retaining useful automated coverage?

The primary engineering question is:

> Can every automatically exported clinical datum be made reproducibly traceable to source pixels, independent checks, transformation history, and a versioned decision policy?

## 2. v0.1 boundaries

### In scope

- PDF, PNG, JPEG, and TIFF-like rendered clinical documents.
- Printed, scanned, fax-like, and photographed documents.
- Laboratory reports only.
- Local-first execution.
- Evidence-bound extraction.
- FHIR R4 export.
- Synthetic and public PHI-free evaluation.

### Explicitly out of scope

- Diagnosis generation.
- Treatment recommendations.
- Clinical decision support.
- Radiology/pathology image interpretation.
- Free-form handwritten physician-note understanding.
- Automatic correction of clinically implausible OCR text.
- Medication lists, medication orders, and medication FHIR mapping.
- Drug-drug interaction checking.
- Full SNOMED CT integration.
- Real-patient deployment claims.
- Training a new OCR foundation model.
- Cloud dependency as a mandatory path.

## 3. Safety states

Every candidate field is in exactly one terminal automation state:

- VERIFIED_AUTO: evidence contract satisfied; automatic export permitted.
- REVIEW_REQUIRED: plausible candidate exists but evidence is insufficient or conflicting; export blocked.
- ABSTAINED: SafeOCR cannot establish a reliable field value; export blocked.
Human review resolution is deferred to v0.2. v0.1 emits evidence-rich REVIEW_REQUIRED artifacts but does not implement a clinical review workflow.

No hidden fallback converts REVIEW_REQUIRED or ABSTAINED into VERIFIED_AUTO.

## 4. Clinical criticality

v0.1 uses deterministic policy, not a generative model, to set criticality.

### Critical

- numeric laboratory value;
- laboratory unit;
- positive/negative or detected/not-detected status;
- decimal point, sign, exponent, and comparator;
- patient/document identity linkage;
- row/column association that changes clinical meaning.

### High

- laboratory analyte;
- specimen/date/time;
- reference range;
- abnormal flag.

### Normal

- headings;
- administrative text;
- non-decisive narrative text.

Criticality determines verification strictness. It never changes the source reading.

## 5. Data model

### PageAsset

Immutable rendered page:
- source document SHA-256;
- page index;
- renderer name/version;
- DPI and pixel dimensions;
- page-image SHA-256.

### CandidateSpan

One OCR/parser proposal:
- engine identity and exact revision;
- source PageAsset;
- polygon/bounding box;
- raw text;
- engine-native confidence if available;
- decoding/settings metadata.

### ClinicalFieldCandidate

Structured candidate assembled from spans:
- field type;
- raw value;
- unit/text qualifiers;
- source spans;
- document section/table coordinates;
- document-family classification;
- criticality tier.

### EvidenceRecord

Evidence used for one decision:
- pixel region hash;
- all engine proposals;
- perturbation outputs;
- layout/association checks;
- terminology checks;
- patient/document linkage checks;
- policy version;
- decision;
- reasons and failed gates.

### ExportRecord

Maps one verified field to:
- FHIR resource id;
- FHIR resource type;
- source DocumentReference;
- Provenance id;
- EvidenceRecord id.

## 6. Verification signals

No single signal can prove correctness.

### 6.1 Visual grounding

Mandatory for all structured clinical fields. The exact page region must be recoverable and hash-bound.

Failure to localize a critical field -> REVIEW_REQUIRED or ABSTAINED.

### 6.2 Independent critical-crop reading

v0.1 does not run two complete document-understanding pipelines.

PaddleOCR performs the primary page/layout read. For a critical candidate, SafeOCR crops the exact evidence region and asks Tesseract to independently re-read only that critical crop.

This keeps the independent check narrow and cheap while preserving model-family diversity.

Independence is tracked by engine family. Agreement raises support but never overrides contradictory pixel/stability evidence. A secondary failure to read is not converted into agreement.

### 6.3 Perturbation stability

Re-read semantically preserving variants:
- slight contrast/brightness changes;
- small scale change;
- bounded rotation;
- conservative crop-margin changes;
- optional mild denoise.

Every perturbation is recorded. Destructive perturbations are prohibited from being treated as evidence against a clean source.

Instability in a critical numeric span -> REVIEW_REQUIRED or ABSTAINED.

### 6.4 Structural association

For tabular clinical data verify:
- row identity;
- column identity;
- analyte-to-value relationship;
- value-to-unit relationship;
- header inheritance;
- multi-page continuation boundaries.

A correct number attached to the wrong analyte is counted as incorrect.

### 6.5 Clinical-semantic veto

Terminology and unit knowledge may identify inconsistencies and block export.

It may not silently rewrite a value, unit, analyte, date, or comparator.

Example: if a visually grounded HbA1c row reads an unexpected unit, SafeOCR raises a review condition; it does not substitute a expected unit.

### 6.6 Patient/document linkage

Patient attribution is safety-critical.

If a document contains multiple identities, uncertain identity, or insufficient linkage, structured patient-level export is blocked.

No cross-patient merging is permitted.


## 6A. v0.1 automatic-acceptance policy

v0.1 intentionally uses a conservative, transparent policy.

A critical laboratory field may reach VERIFIED_AUTO only when all mandatory gates pass:

1. the field is bound to a unique source page and region;
2. the laboratory analyte/value/unit association is structurally unambiguous;
3. the primary full-page read and the independent critical-crop re-read agree on the normalized critical value at the configured calibration policy;
4. the primary critical-crop read is stable across the approved non-destructive perturbation set;
5. decimal/sign/comparator parsing is unambiguous;
6. unit parsing is valid and does not trigger a hard semantic veto;
7. patient/document linkage is unambiguous for patient-level export;
8. no ingestion, verification, or FHIR-validation exception occurred.

Thresholds or tolerated normalization differences are defined only from the calibration split and versioned with the decision policy.

Engine-native confidence is never treated as a calibrated probability by default.

If any mandatory gate fails, the result is REVIEW_REQUIRED or ABSTAINED. The system fails closed.

## 6B. Canonical laboratory field representation

Before comparison or FHIR mapping, a laboratory candidate is represented as a typed tuple:

- analyte source text;
- optional normalized analyte identifier;
- value type;
- exact normalized numeric or categorical value;
- comparator if present;
- sign/exponent if present;
- source unit text;
- optional canonical UCUM unit;
- reference-range components when explicitly present;
- abnormal flag when explicitly present;
- specimen/result timestamp when explicitly present;
- patient/document linkage;
- evidence span ids.

Correctness includes association. A correct numeric string mapped to the wrong analyte, unit, patient, date, or row is incorrect.

Normalization may canonicalize formatting such as whitespace or equivalent numeric representation; it may not infer an absent value or silently repair a source discrepancy.

## 7. Engine strategy

SafeOCR Core defines a stable adapter interface.

v0.1 reference adapters:
1. PaddleOCR - primary full-page OCR/layout path.
2. Tesseract - independent critical-crop re-reader and raw classical baseline.

Tesseract is not required to reproduce the full page structure; it only verifies bounded critical evidence regions in the SafeOCR gate.

Deferred adapters:
- docTR;
- TeleOCR.

v0.1 must remain functional with only the two reference adapters.

Reason: SafeOCR must not become a wrapper around one model, and CPU-accessible evaluation must remain possible.

Each engine run pins:
- package version;
- model name;
- model revision/hash when available;
- decoding/inference parameters;
- hardware/runtime metadata.

## 8. Ingestion and security

Clinical documents are untrusted inputs.

Required controls:
- file-size limit;
- page-count limit;
- maximum rendered-pixel budget;
- render-time limit;
- supported MIME/type allowlist;
- safe PDF rendering through a non-executing renderer;
- no embedded script/macro execution;
- temporary-file lifecycle and cleanup;
- deterministic source hashes.

Document text is also untrusted. Instructions embedded inside a document must never grant tools, network access, file access, or policy overrides to VLM adapters.

Model output is untrusted data until SafeOCR verifies it.

## 9. Privacy model

Default operation is local-first.

Public development/evaluation uses:
- ClinOCR-Bench;
- Synthea-generated synthetic records;
- SafeOCR-generated synthetic clinical documents.

No real PHI is required.

Default logging:
- no document body telemetry;
- no remote analytics containing clinical content;
- hashes and structured diagnostics only when possible;
- explicit opt-in required for any future cloud adapter.

## 10. SafeOCR-LabGold exact-truth benchmark

v0.1 does not depend on Synthea.

SafeOCR-LabGold is a small deterministic PHI-free benchmark generated specifically for laboratory-field verification.

Scope:
- three controlled laboratory-report templates;
- fake patient identifiers/names generated locally;
- typed laboratory rows with analyte, value, unit, reference range, flag, and timestamp;
- exact source coordinates captured at rendering time;
- deterministic seeds and versioned template definitions.

Pipeline:
1. Generate a typed fake laboratory record from a versioned seed.
2. Render one of three controlled report templates.
3. Record exact field truth and exact source regions.
4. Produce a clean page image/PDF.
5. Apply versioned corruption variants.
6. Run raw OCR and SafeOCR.
7. Compare accepted fields back to the original typed truth.

The benchmark is intentionally small and auditable. It is not intended to model population epidemiology or realistic longitudinal EHRs.

## 11. Corruption suite

Corruptions are versioned and seeded.

Whole-document conditions:
- blur;
- compression;
- resolution loss;
- skew;
- bounded perspective distortion;
- low contrast;
- shadow/illumination;
- fax-like noise;
- rotation;
- partial crop.

Critical-span stressors:
- decimal visibility;
- minus-sign visibility;
- small-unit glyphs;
- digit ambiguity such as 0/O, 1/l, 5/S, 8/B;
- scientific notation/exponents;
- comparator symbols;
- row/column proximity;
- handwritten overwrite and strike-through as abstention/review tests.

The corruption engine must never change ground truth labels silently.

## 12. External benchmark

ClinOCR-Bench is used as the public external benchmark for full-document conditions.

SafeOCR adds a derived Safety Track focused on clinically critical fields and association errors.

No public benchmark test examples are used to tune decision thresholds.

A calibration/development split and a locked evaluation split are maintained.


## 12A. Split and leakage control

SafeOCR-LabGold evaluation is partitioned before policy tuning.

At minimum:
- patient identities do not cross calibration and final evaluation splits;
- document templates used for final evaluation are held out from policy tuning where feasible;
- corruption random seeds for final evaluation are locked and not inspected during threshold tuning;
- the external ClinOCR-Bench evaluation split is never used to set SafeOCR acceptance thresholds.

Any benchmark result produced after test-set inspection is labeled exploratory and is not used as the primary v0.1 claim.

## 13. Evaluation contract

### Headline metrics

Critical Field Exact Accuracy (CFEA):
Exact correctness of normalized critical fields, including field association.

Unsafe Accept Rate (UAR):
incorrect accepted critical fields / all accepted critical fields.

Verified Coverage (VC):
automatically verified critical fields / all evaluable critical fields.

Review Rate:
review-required critical fields / all evaluable critical fields.

Abstention Rate:
abstained critical fields / all evaluable critical fields.

Patient Attribution Error Rate:
incorrect patient-linked accepted fields / patient-linked accepted fields.

Table Association Error Rate:
accepted values attached to incorrect row/column semantics / accepted table fields.

FHIR Mapping Error Rate:
accepted fields represented with incorrect FHIR semantics / exported fields.

### Curves and intervals

The primary safety result is a risk-coverage curve.

Report confidence intervals for accepted error rates. Observing zero errors is reported as zero observed errors, never as proof of zero risk.

### Baselines

At minimum compare:
- raw primary OCR;
- raw Tesseract crop reads on the critical-field test set;
- naive exact-agreement gate without SafeOCR's stability/association checks;
- SafeOCR verification policy.

A SafeOCR improvement claim requires lower unsafe accepted error at a comparable or explicitly reported coverage point.

## 14. FHIR R4 contract

Target FHIR release for v0.1: R4.

Source document:
- DocumentReference.

Laboratory extraction:
- DiagnosticReport for report context;
- Observation for atomic laboratory results.

Provenance:
- each exported clinical resource is linked through Provenance to the source DocumentReference and SafeOCR transformation activity.

Exact pixel coordinates, engine disagreement, perturbation details, and verification signals live in a SafeOCR Evidence Manifest sidecar.

v0.1 does not invent custom FHIR extensions unless a standards gap is demonstrated and documented.

All emitted FHIR is validated in CI with an R4 validator.

## 15. Terminology contract

LOINC:
- optional/target normalization for lab identity;
- never used to hallucinate a missing analyte or result.

UCUM:
- unit parsing/canonicalization and compatibility checks;
- a failed unit check blocks or reviews; it does not rewrite visual evidence silently.

SNOMED CT is excluded from v0.1 to avoid unnecessary licensing/scope complexity.

## 16. Human review boundary

v0.1 does not implement a clinical human-review workflow.

It produces review artifacts containing the candidate, source crop, evidence, failed gates, and decision rationale.

Interactive reviewer confirmation/correction, reviewer identity, and VERIFIED_HUMAN provenance are v0.2 work. This avoids implying a validated clinical review process in the first release.

## 17. Reproducibility

Every benchmark run records:
- git commit;
- Python/package lock;
- engine/model revisions;
- dataset version/checksum;
- rendering settings;
- corruption seed;
- SafeOCR policy version;
- OS/hardware summary.

Result artifacts must be reproducible without a paid API.


## 17A. Implementation environment

v0.1 targets Python 3.11 and 3.12.

The reference path must run on CPU without a discrete GPU. GPU/VLM acceleration is optional and may not be required to reproduce the core safety benchmark.

CI target:
- Windows;
- Ubuntu;
- unit/contract tests;
- deterministic synthetic benchmark smoke test;
- FHIR validation;
- dependency/license metadata check.

A container image may be provided for reproducibility, but Docker is not a mandatory runtime requirement.

## 18. Repository structure

```
SafeOCR/
  safeocr/
    ingest/
    engines/
    evidence/
    clinical/
      labs/
    verification/
    decision/
    terminology/
    fhir/
    review/
  benchmarks/
    clinocr/
    safeocr_synth/
  corruptions/
  evaluation/
  examples/
  ui/
  tests/
  docs/
  .github/workflows/
```

## 19. Milestones and exit criteria

### F0 - Foundation freeze

Deliver:
- master plan;
- safety contract;
- source/license registry;
- threat model embedded in plan;
- acceptance metrics.

Exit:
- no unresolved architectural ambiguity that changes v0.1 scope;
- source licenses have an explicit verification status;
- no clinical-use claim.

### F1 - Skeleton and contracts

Deliver:
- Python package;
- typed schemas;
- adapter interfaces;
- evidence manifest schema;
- decision-state schema;
- deterministic CLI shell.

Exit:
- contract tests pass;
- no OCR-specific logic leaks into core interfaces.

### F2 - SafeOCR-LabGold harness

Deliver:
- typed fake laboratory-record generator;
- three laboratory-report templates;
- seeded corruption engine;
- exact field/region annotations.

Exit:
- every generated field can be traced from typed truth to exact rendered region;
- corruption does not mutate labels;
- all templates and seeds are versioned.

### F3 - OCR and critical-crop verifier

Deliver:
- PaddleOCR full-page adapter;
- Tesseract critical-crop re-reader;
- deterministic crop handoff contract.

Exit:
- PaddleOCR produces normalized page/span/layout candidates;
- Tesseract accepts a bounded crop and returns a normalized critical read;
- engine/version metadata is recorded;
- CPU baseline path works.

### F4 - Evidence and verification

Deliver:
- visual grounding;
- critical-crop independent agreement;
- critical-crop perturbation stability;
- primary-layout table association;
- terminology veto;
- patient linkage checks.

Exit:
- every critical-field decision has an EvidenceRecord;
- critical hard-gate failures cannot reach automatic export.

### F5 - FHIR gate

Deliver:
- R4 mapping;
- DocumentReference;
- DiagnosticReport/Observation;
- Provenance;
- validator CI.

Exit:
- only verified fields are exported;
- all sample bundles validate;
- review/abstain fields cannot silently appear in FHIR.

### F6 - Evaluation

Deliver:
- raw OCR baselines;
- naive agreement baseline;
- SafeOCR evaluation;
- ClinOCR-Bench integration;
- Safety Track;
- risk-coverage curves;
- confidence intervals.

Exit:
- no test-set threshold tuning;
- all headline metrics reported;
- limitations documented.

### F7 - Evidence report

Deliver:
- deterministic CLI report;
- generated static HTML evidence report;
- source crop for every critical field;
- why-verified / why-blocked explanation.

Exit:
- every displayed critical field resolves to source evidence;
- no interactive application framework is required for v0.1.

### F8 - v0.1 release

Deliver:
- installation docs;
- reproducible demo;
- pinned benchmark report;
- SBOM/third-party notices;
- security/safety limitations;
- tagged release.

Exit:
- clean install on supported CPU machine;
- zero mandatory paid services;
- benchmark and demo reproduce from public/synthetic inputs.

## 20. Deferred work

v0.2 candidates:
- medication lists/orders and RxNorm normalization;
- docTR and TeleOCR adapters;
- calibrated selective prediction;
- conformal risk control;
- richer document families;
- improved handwriting handling;
- interactive human-review UI;
- R5 export adapter.

None of these may block v0.1.

## 21. Release claims policy

Allowed claims must be directly supported by benchmark evidence.

Prohibited without evidence:
- "zero-error";
- "clinically safe";
- "medical-device grade";
- "guaranteed correct";
- real-world outcome benefit;
- superiority outside tested document families.

The preferred framing is:
- observed accepted-error rate;
- verified coverage;
- tested document conditions;
- exact engine/dataset versions;
- explicit limitations.


## 21A. Naming and namespace risk

The public project name is SafeOCR.

A separate general-purpose OCR product already uses the SafeOCR name. Before publishing packages or a public website, perform a naming/trademark/package-index collision review.

If needed, preserve the project identity while using a collision-resistant package namespace such as `safeocr-health` or `safeocr-clinical`.

This naming issue must not change the healthcare-only scope.

## 22. Definition of v0.1 success

SafeOCR v0.1 is successful if an independent user can:

1. run a public/synthetic laboratory report locally;
2. inspect evidence for each critical extracted field;
3. observe VERIFIED/REVIEW/ABSTAIN decisions;
4. confirm that unverified critical fields are absent from automatic FHIR output;
5. reproduce the benchmark comparison between raw OCR and SafeOCR;
6. understand precisely what SafeOCR does not claim.

That is the v0.1 finish line. Anything beyond it is future work.
