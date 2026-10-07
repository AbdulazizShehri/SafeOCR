# SafeOCR

**Trust pixels, not predictions.**

SafeOCR is healthcare-only verification infrastructure for clinical document extraction. It sits between OCR/document-understanding engines and structured health data, and blocks unverified clinical facts from automatic downstream use.

> If SafeOCR cannot bind a clinical datum to source evidence and pass a risk-appropriate verification gate, it does not export that datum to FHIR.

## Public resources

- **Live PHI-free verification playground:** https://huggingface.co/spaces/MedScaleAI/SafeOCR
- **Frozen synthetic benchmark:** https://huggingface.co/datasets/MedScaleAI/SafeOCR-LabGold
- **How to use SafeOCR:** [docs/USING_SAFEOCR.md](docs/USING_SAFEOCR.md)
- **Paper:** arXiv identifier will be added at publication

The public Hugging Face Space is a synthetic policy explorer. It does not accept patient documents and does not run a production clinical OCR service. The full reproducible implementation, frozen evidence, and FHIR export gate remain in this repository.

## Why

A low character-error rate is not a clinical safety guarantee. A one-character error can turn `0.5` into `5`, lose a minus sign, change a laboratory unit, or attach a correct number to the wrong analyte row.

SafeOCR treats those failures as a selective-verification problem, not merely an OCR-accuracy problem.

## v0.1 scope

SafeOCR v0.1 supports one healthcare document family only:

- laboratory reports.

Inputs are printed, scanned, fax-like, or photographed laboratory reports. Handwritten free-text is a stress condition, not a promised capability. Medication documents are explicitly deferred to v0.2.

Core decisions are:

- `VERIFIED_AUTO`
- `REVIEW_REQUIRED`
- `ABSTAINED`

Only `VERIFIED_AUTO` fields may enter automatic FHIR export in v0.1. Human review resolution is deferred to v0.2; v0.1 produces evidence-rich review reports.

## Core invariants

1. No evidence -> no automatic export.
2. Missing is never interpreted as negative.
3. Agreement between OCR engines is evidence, not proof.
4. Clinical plausibility may block an extraction but must never rewrite source pixels.
5. Safety-critical disagreement routes to review or abstention.
6. Every accepted field is reproducible from pinned inputs, model revisions, transforms, and policy versions.
7. No real PHI is required for the public benchmark or demo.

## Architecture

```
Clinical document
       |
       v
Safe ingestion + rendering
       |
       v
OCR / parsing adapters
       |
       v
Evidence-bound clinical fields
       |
       v
Verification signals
       |
       v
Risk-aware decision policy
   /       |        \
verified  review   abstain
   |
   v
FHIR R4 export gate
   |
   +--> Provenance
   +--> Evidence manifest
```

SafeOCR is model-agnostic. OCR engines are replaceable readers; SafeOCR owns the evidence contract, verification logic, decision policy, audit trail, benchmark, and FHIR gate.

## v0.1 engine paths

- PaddleOCR: primary OCR/layout path.
- Tesseract: second-engine critical-crop re-reader and classical baseline.

docTR and TeleOCR remain planned adapters, but they do not block v0.1.

## Evaluation

Headline metrics:

- Critical Field Exact Accuracy
- Unsafe Accept Rate
- Verified Coverage
- Review Rate
- Abstention Rate
- Patient Attribution Error Rate
- Table Association Error Rate
- FHIR Mapping Error Rate

v0.1 reports prespecified, commit-timestamped risk/coverage operating points and confidence intervals. It does not perform a post-hoc threshold sweep after final-set inspection.

See [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md), [docs/SAFETY_CONTRACT.md](docs/SAFETY_CONTRACT.md), and [docs/SOURCE_REGISTRY.md](docs/SOURCE_REGISTRY.md).

## Safety

SafeOCR is research software. It is not a medical device and must not be used to make diagnosis or treatment decisions. v0.1 is designed to evaluate whether extracted clinical facts are sufficiently evidenced for structured-data export; it does not infer missing facts, diagnose conditions, or recommend treatment.


## Install

Core package:

    python -m pip install -e .

Development environment:

    python -m pip install -e ".[dev]"

Reference OCR runtime:

    python -m pip install -e ".[ocr,dev]"

Tesseract and Java are external binaries for the second-engine reread and official FHIR validator paths. The default unit-test suite does not require runtime downloads, real PHI, or paid APIs.

## Verify the release

    python -m pytest -q
    ruff check .
    pyright
    python -m pip check
    graft build .
    graft check .

Runtime smoke tests are explicit opt-in gates and use the pinned local engines/models.

## Frozen v0.1 result

The primary SafeOCR-LabGold final set contains 48 frozen documents / 288 critical-field cases.

| Method | Verified coverage | Unsafe accept rate |
| --- | ---: | ---: |
| Primary OCR | 100.00% | 0.00% observed |
| Tesseract critical crop | 99.65% | 15.68% |
| Naive exact agreement | 84.03% | 0.00% observed |
| SafeOCR | 72.57% | 0.00% observed |

SafeOCR accepted 209/288 fields and sent 79/288 to review. It observed zero unsafe accepts; the field-level 95% Wilson upper bound is approximately 1.805%.

The raw primary OCR baseline also had 0/288 errors at full coverage, with a tighter field-level Wilson upper bound of approximately 1.316%. Therefore all 79 SafeOCR reviews were correct fields under benchmark truth and this endpoint does **not** demonstrate a safety gain. It measures automation coverage and review cost on this synthetic benchmark. This does not establish SafeOCR superiority over the primary OCR baseline. Zero observed errors is not proof of zero risk.

Canonical evaluation artifacts are in docs/evidence/F6_FINAL_EVALUATION.json, docs/evidence/F6_RISK_COVERAGE.csv, and docs/evidence/F6_CLOSEOUT.json.

## External benchmark integration

ClinOCR-Bench v1.0 is pinned as a synthetic, template-generated, PHI-free external OCR benchmark. SafeOCR validates its published train/test metadata and locks external evaluation records out of tuning paths.

ClinOCR-Bench v1.0 provides full-document transcript ground truth rather than SafeOCR field/patient/FHIR annotations. Frozen PaddleOCR mean WER was 0.4769 versus 0.5589 for local Tesseract, but PaddleOCR also had 57/328 runtime failures retained as empty predictions, including 33/56 rotated and 24/48 mixed-artifact documents. SafeOCR therefore treats this as transcription/fail-closed engineering evidence, not field-level safety validation.

## Public laboratory-report verifier component

The external component study uses the public laboratory-report image collection originally associated with Xue et al. (IEEE Access 2020) and later used/described by Ma et al. (2023). It is an oracle-localised verifier-component study, not end-to-end extraction validation.

Of 2,219 candidate laboratory rows, 1,850 met the frozen eligibility rules. The primary numeric OCR reading was exact in all 1,850 eligible rows. The component gates passed 375/1,850 rows, also with 0/375 numeric errors; because the ungated endpoint already had zero errors, this cannot demonstrate numeric-error reduction. A separately labelled post-outcome diagnostic found analyte or unit mismatches in 38/375 component passes, motivating verification beyond numeric values.

See paper/MA2023_EXTERNAL_COMPONENT_PROTOCOL.md and paper/MA2023_EXTERNAL_COMPONENT_PROTOCOL_ADDENDUM.md for the frozen protocol and the post-outcome provenance/method audit.

## Static evidence report

The v0.1 report is self-contained HTML with an embedded source crop, exact source-page identity, source box, policy version, decision state, failed gates, and deterministic why-verified / why-blocked explanation. The companion JSON retains the complete EvidenceRecord provenance.

Canonical artifacts:

- docs/evidence/F7_EVIDENCE_REPORT.html
- docs/evidence/F7_EVIDENCE_REPORT.json

Rebuild locally:

    python scripts/build_f7_report.py

## License

SafeOCR source code is released under Apache License 2.0. Third-party software, model weights, standards, terminology, and benchmark data retain their own licenses and terms.

See LICENSE, NOTICE, docs/THIRD_PARTY_NOTICES.md, and docs/RELEASE_NOTES_v0.1.0.md.
