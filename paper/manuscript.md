# SafeOCR: Evidence-Grounded Selective Verification for Clinical OCR with Provenance-Preserving FHIR Export

**Draft status:** working manuscript
**Study type:** methods and evaluation study
**Domain:** laboratory-report OCR verification
**Software version:** SafeOCR v0.1.0

## Abstract

### Objective

Optical character recognition can digitize scanned clinical documents, but transcription accuracy alone does not establish whether a safety-critical clinical field is sufficiently supported for automatic downstream use. We developed SafeOCR, a healthcare-specific verification layer that treats OCR output as an untrusted proposal and permits structured export only when a field is bound to source pixels and passes deterministic verification gates.

### Materials and Methods

SafeOCR v0.1 targets laboratory reports. PaddleOCR provides the primary page read and Tesseract independently re-reads bounded critical-field crops. The verification policy evaluates visual grounding, analyte-value-unit association, independent agreement, perturbation stability, numeric parsing, unit validity, patient/document linkage, and runtime health. Each field terminates as VERIFIED_AUTO, REVIEW_REQUIRED, or ABSTAINED; only VERIFIED_AUTO fields may enter the FHIR R4 export path. We preregistered calibration/evaluation roles and evaluated a fixed v0.1 policy on SafeOCR-LabGold, a PHI-free synthetic benchmark with 48 frozen final documents and 288 critical-field cases. Primary outcomes were unsafe accept rate and verified coverage. We additionally validated FHIR R4 conformance with the official HL7 validator and integrated ClinOCR-Bench metadata under a no-tuning external-evaluation contract.

### Results

SafeOCR accepted 209/288 fields (verified coverage 72.57%) and routed 79/288 (27.43%) to review. No unsafe accepts were observed among accepted SafeOCR fields (observed unsafe accept rate 0%; 95% Wilson interval 0-1.805%). A naive exact-agreement gate accepted 242/288 fields (84.03%) with zero observed unsafe accepts. The raw primary OCR baseline also had zero observed errors at 100% coverage on this synthetic final set, while the Tesseract crop baseline produced 45 unsafe accepts among 287 accepted fields (15.68%). An OCR-geometry-only association scorer observed no row-association errors in 288 evaluable cases. The FHIR R4 smoke artifact passed the official validator with zero errors; a deliberately invalid control was rejected.

### Discussion

The evaluation demonstrates a reproducible selective-verification workflow, not superiority over the primary OCR baseline. Because the raw primary OCR path was error-free on the frozen synthetic final set, LabGold alone cannot show that SafeOCR reduces errors relative to that baseline. SafeOCR instead contributes an explicit evidence contract linking field acceptance, abstention/review, source-pixel provenance, and gated FHIR export. External validation on real scanned clinical documents with field-level safety annotations remains necessary.

### Conclusion

SafeOCR reframes clinical OCR as a selective verification problem: the system must establish sufficient evidence before automated structured export rather than forcing a prediction for every field. The v0.1 results support the feasibility and reproducibility of this design while defining clear limits on current claims.

## 1. Introduction

Scanned and paper-origin clinical documents remain common in healthcare workflows, including external laboratory reports, pathology records, referral documents, and legacy archives. OCR combined with information extraction can convert these documents into structured data and has shown strong performance in several clinical settings. Ma et al. developed an OCR and information-extraction pipeline for paper laboratory reports, reporting an average OCR accuracy of 0.93 and overall entity-extraction F1 of 0.86 on 153 real laboratory reports [@ma2023labocr]. Laique et al. similarly demonstrated large-scale extraction from scanned colonoscopy and pathology reports with a hybrid OCR/NLP pipeline [@laique2021ocrnlp]. These studies establish the practical value of clinical OCR pipelines, but they primarily evaluate whether values can be extracted correctly. Hsu et al. further showed on 955 scanned sleep-study reports that preprocessing, OCR, document layout, and downstream NLP interact materially in end-to-end performance [@hsu2022scanned].

For downstream clinical data use, a second question is equally important: **when should an extracted field be trusted enough for automatic structured export?** A character-level error can have disproportionate clinical meaning when it changes a decimal point, sign, comparator, unit, or row association. A number can be transcribed correctly yet still be unsafe if it is attached to the wrong analyte or patient. Conventional OCR confidence scores do not directly answer this question, and forcing a prediction for every field can convert uncertainty into silent structured-data errors.

Selective prediction provides a useful conceptual framework. Instead of requiring a model to predict on every case, a system may abstain when the expected cost of error is high. SelectiveNet formalized risk-coverage optimization with an explicit reject option [@geifman2019selectivenet]. In clinical data abstraction, Swaminathan et al. showed that selective prediction can improve extraction utility when abstention is preferable to an incorrect prediction [@swaminathan2024selective]. More recent work has explored statistical risk control and conformal verification for accepted extractions [@angelopoulos2025learntest; @kim2025conformalEHR]. These approaches motivate treating acceptance itself as a controlled decision rather than a by-product of OCR confidence.

A third requirement is traceability. FHIR provides a standardized interoperability layer for clinical data, and prior work has connected clinical text mining with FHIR and emphasized provenance as part of trustworthy data exchange [@daumke2019fhir; @margheri2020provenance]. However, FHIR conformance and provenance do not by themselves establish whether an OCR-derived field was correctly read from source pixels.

Recent work also shows that source-grounded integrity gating and visually grounded clinical extraction are emerging as distinct design patterns. Girda and Groza introduced a deterministic trust-promotion monitor for laboratory data that requires unique source support, same-row evidence, preserved provenance, and review retention for refused candidates [@girda2026review]. RAPTOR+ jointly evaluates structured clinical-field extraction and source-image bounding-box localisation on clinically curated referral forms, showing that high reading accuracy can coexist with weak evidence localisation [@abioye2026raptorplus]. Ben Hmida et al. independently combined ontology-constrained OCR with verified abstention [@benhmida2025ontology]. These studies materially narrow the novelty space: SafeOCR does not claim invention of evidence gating, visual grounding, or abstention in isolation. SafeOCR instead combines source-region binding with independent OCR-family rereading, perturbation stability, patient/document linkage, explicit criticality, governed risk/coverage evaluation, and verification-gated FHIR export.

SafeOCR combines these lines of work into a healthcare-specific verification gateway. OCR engines propose readings; SafeOCR decides whether each critical field has sufficient evidence to be automatically exported, must be reviewed, or must be withheld. The v0.1 system targets laboratory reports and uses a fixed, deterministic policy. Its central research question is not "How high is OCR accuracy?" but:

> How low can the accepted error rate for safety-critical clinical fields be driven while retaining useful automated coverage?

The engineering counterpart is:

> Can every automatically exported clinical datum be reproducibly traced to source pixels, independent checks, transformation history, and a versioned decision policy?

This paper makes four contributions:

1. an evidence-bound clinical OCR data model in which structured fields retain source-page and source-region provenance;
2. a fail-closed selective verification policy with explicit VERIFIED_AUTO, REVIEW_REQUIRED, and ABSTAINED terminal states;
3. a provenance-preserving FHIR R4 export gate that permits automated export only after verification;
4. a preregistered evaluation framework that reports unsafe accepted error jointly with verified coverage and preserves calibration/final-evaluation separation.

We frame SafeOCR as a systems-and-evaluation contribution. OCR, evidence gating, abstention, provenance, and FHIR are not individually novel. Closely related 2026 work already demonstrates source-grounded trust promotion for laboratory data [@girda2026review]. The contribution claimed here is therefore narrower: the integration and reproducible evaluation of a field-level healthcare OCR safety contract that couples pixel evidence, independent rereading, perturbation stability, patient linkage, explicit criticality, selective decisions, and gated FHIR export.

## 2. Related Work

### 2.1 Clinical OCR and structured extraction

Clinical OCR research has shown that scanned healthcare documents can be converted into structured information with useful accuracy. Ma et al. addressed paper-based laboratory reports containing heterogeneous layouts and mixed text, numeric values, units, and reference ranges [@ma2023labocr]. Their pipeline combined OCR with downstream entity extraction and demonstrated feasibility in a hospital setting. Li et al. directly studied deep-learning table extraction from scanned laboratory reports, reinforcing that table structure itself is a major source of difficulty in clinical OCR [@li2024tabular]. Ren et al. later proposed a serialization pipeline for 330 image-based medical laboratory reports, combining layout analysis, text detection, and recognition for structured digitization [@ren2025serialization]. Laique et al. applied OCR followed by NLP to scanned colonoscopy and pathology reports and reported high variable-level extraction accuracy [@laique2021ocrnlp].

Recent benchmarks and large-scale extraction studies broaden the evaluation landscape. ClinOCR-Bench provides 384 PHI-free scanned clinical documents spanning normal scans, handwriting, poor quality, rotation, tables, and mixed artifacts [@hsu2026clinocr]. MedStruct-S evaluates semi-structured extraction under unknown keys and OCR-induced noise across 3,582 clinical report pages [@li2026medstructs]. Wang et al. report canonical-key-conditioned extraction over a much larger real-world archive collected from more than 20 hospitals, showing that end-to-end performance depends strongly on key coverage and degrades under OCR corruption [@wang2026keycoverage]. MedRepBench extends evaluation toward structured understanding of medical report images [@shang2026medrepbench]. Together, these resources reinforce that clinical document understanding must handle recognition noise, document structure, and open-ended schema variation.

SafeOCR differs in primary objective. It does not propose a new recognizer or maximize end-to-end extraction F1. Instead, it assumes OCR proposals may be wrong and asks whether the evidence supporting each critical field is sufficient for automatic downstream use.

The closest parallel systems identified in our search are Girda and Groza's source-grounded integrity gate for AI-assisted personal health records and RAPTOR+. The former keeps laboratory candidates provisional until a deterministic monitor verifies unique source support, same-row evidence, and provenance, while retaining refused candidates for review [@girda2026review]. RAPTOR+ instead uses end-to-end vision-language models to emit field values together with source-image bounding boxes and evaluates both reading accuracy and evidence localisation [@abioye2026raptorplus]. Ontology-constrained OCR with verified abstention provides an additional adjacent precedent [@benhmida2025ontology]. SafeOCR should therefore be compared against these systems as a distinct integration: visual grounding and evidence gating are prior art, while SafeOCR's evaluated contract adds independent OCR-family rereading, perturbation-stability admission, patient/document linkage, explicit criticality, governed selective states, and verified-only FHIR export.

### 2.2 Selective prediction and abstention

Selective prediction allows a system to trade coverage for lower conditional error by declining uncertain cases. SelectiveNet demonstrated learned risk-coverage optimization in general machine-learning tasks [@geifman2019selectivenet]. In clinical information extraction, Swaminathan et al. found that selective classifiers could improve extraction performance and total misclassification cost when abstention was explicitly allowed [@swaminathan2024selective].

Statistical risk-control methods further motivate separating model prediction from acceptance. Learn-then-Test provides finite-sample methods for calibrating predictive algorithms to satisfy explicit risk constraints without model retraining [@angelopoulos2025learntest]. Kim et al. applied conformal verification to large-language-model extraction from unstructured EHR narratives and emphasized controlling the error rate among accepted extractions [@kim2025conformalEHR].

SafeOCR adopts the selective-prediction framing but does not claim a conformal guarantee in v0.1. Its policy is deterministic and its primary statistical reporting uses observed unsafe accepted errors, verified coverage, and Wilson confidence intervals.

### 2.3 Provenance and FHIR interoperability

Clinical text mining has been mapped into FHIR resources to support semantic interoperability [@daumke2019fhir]. The SMART Text2FHIR pipeline further demonstrates that clinical concept extraction can be mapped into FHIR resources in an open-source workflow [@miller2023smarttext2fhir], and printed-form-to-FHIR transformation has been explored for care-transition records [@werlitz2025printedfhir]. Provenance systems for healthcare data have likewise emphasized traceability across data exchange and shown how provenance records can be represented through FHIR [@margheri2020provenance]. The HL7 FHIR R4 specification provides resource identity, metadata, source information, and Provenance relationships for data exchange [@hl7fhirr4].

SafeOCR uses provenance at a finer-grained verification boundary: every accepted clinical field retains the source page, bounding region, engine identity, verification signals, policy version, and decision explanation. FHIR export is downstream of this evidence contract and is blocked for non-verified fields.

## 3. Materials and Methods

### 3.1 Scope and safety boundary

SafeOCR v0.1 is research software for laboratory-report OCR verification. It is not a medical device and does not provide diagnosis, treatment recommendations, or clinical decision support. Medication documents, free-form handwritten physician notes, radiology/pathology image interpretation, and automatic correction of clinically implausible text are outside v0.1 scope.

The reference execution path is local-first and PHI-free for public evaluation.

### 3.2 System architecture

The pipeline is:

1. immutable document/page ingestion;
2. primary OCR and layout proposal;
3. construction of evidence-bound clinical field candidates;
4. independent critical-crop re-reading;
5. deterministic verification signals;
6. terminal decision: VERIFIED_AUTO, REVIEW_REQUIRED, or ABSTAINED;
7. FHIR R4 export only for VERIFIED_AUTO fields;
8. static evidence report with source crop, decision reason, and provenance.

PaddleOCR 3.7.0 is the primary full-page OCR path. Tesseract 5.4.0.20240606 is used as an independent critical-crop re-reader and classical baseline.

### 3.3 Evidence-bound field representation

An immutable page asset records source-document SHA-256, page index, dimensions, and page-image SHA-256. OCR proposals are represented as candidate spans containing engine identity, source page, bounding box, raw text, and engine-native confidence where available.

A structured laboratory field retains analyte text, value, unit, source spans, structural association, criticality, and patient/document linkage. The associated EvidenceRecord records verification signals, policy version, terminal decision, failed gates, and sufficient information to recover the supporting pixel region.

Correctness includes association. A numerically correct value linked to the wrong analyte, unit, row, date, or patient is considered incorrect.

### 3.4 Criticality

The v0.1 policy treats numeric laboratory values, units, sign/decimal/comparator semantics, patient identity linkage, and meaning-changing row/column associations as critical. Analyte identity, specimen/date/time, reference range, and abnormal flags are treated as high criticality. Criticality controls verification strictness but never rewrites the source reading.

### 3.5 Verification signals

A critical field may be automatically verified only when all mandatory gates pass.

**Visual grounding.** The field must be tied to a unique source page and recoverable pixel region.

**Structural association.** The analyte-value-unit relationship and row/column identity must be unambiguous.

**Independent reread.** The primary OCR reading is compared with an independent Tesseract reading of the bounded critical crop.

**Perturbation stability.** The critical region is re-read under approved non-destructive image perturbations. Instability blocks automatic acceptance.

**Numeric parsing.** Decimal point, sign, exponent, comparator, and categorical interpretation must be unambiguous.

**Unit validation.** Unit parsing is checked and may veto export. Unit knowledge is not allowed to silently replace source text.

**Patient/document linkage.** Ambiguous patient identity blocks patient-level structured export.

**Runtime health.** OCR, verification, and export exceptions fail closed.

Engine-native confidence is not interpreted as a calibrated probability.

### 3.6 Decision states

Every candidate field reaches exactly one terminal state:

- **VERIFIED_AUTO:** all required evidence gates pass; automated structured export is permitted.
- **REVIEW_REQUIRED:** a plausible candidate exists, but evidence is insufficient or conflicting; automatic export is blocked.
- **ABSTAINED:** the system cannot establish a reliable field value; automatic export is blocked.

No fallback converts REVIEW_REQUIRED or ABSTAINED into VERIFIED_AUTO.

### 3.7 FHIR R4 export gate

Only VERIFIED_AUTO fields may enter the FHIR export path. The export artifact includes provenance linking the structured resource back to source-document evidence. v0.1 targets FHIR R4 (4.0.1).

The FHIR runtime gate used HL7 validator CLI 6.10.4. The canonical valid bundle passed with zero validator errors; a deliberately invalid control was rejected with two errors. The validator produced seven warnings and one note on the valid bundle. These results demonstrate structural/conformance validation, not extraction correctness.

### 3.8 Evaluation contract

The evaluation contract separates calibration and final-evaluation roles. Final-evaluation outcomes cannot be routed into a tuning API. Threshold or policy changes after final-set inspection are prohibited.

Primary metrics are:

- Critical Field Exact Accuracy (CFEA);
- Unsafe Accept Rate (UAR): incorrect accepted fields / accepted fields;
- Verified Coverage (VC): accepted fields / evaluable fields;
- Review Rate;
- Abstention Rate;
- Patient Attribution Error Rate, where estimable;
- Table Association Error Rate, where estimable;
- FHIR Mapping Error Rate, where estimable.

Binomial 95% Wilson intervals are reported for unsafe accepted error proportions. Zero observed errors is never interpreted as zero underlying risk.

### 3.9 SafeOCR-LabGold

The frozen final SafeOCR-LabGold split contains 48 documents and 288 critical-field cases. The final split hash was frozen before execution. The primary final run was executed from a clean exact source head after calibration and qualification.

The compared operating points were:

- raw primary OCR;
- Tesseract critical-crop reading;
- naive exact agreement;
- SafeOCR verification policy.

The primary v0.1 SafeOCR policy has one frozen operating point. We do not retrospectively sweep thresholds on the final set.

### 3.10 External OCR generalization

ClinOCR-Bench was pinned as an external realism benchmark. Its published metadata contains 384 documents, including 56 exemplars and 328 evaluation documents spanning normal, handwriting, poor-quality, rotated, table, and mixed-artifact subsets [@hsu2026clinocr]. Before outcome inspection, we froze a no-tuning protocol for the two OCR engines already used by SafeOCR. Ground-truth transcripts were inaccessible to the OCR runner and were opened only by a separate scorer after all predictions had been written. Word error rate (WER), substitution, deletion, and insertion components were calculated using whitespace tokenization compatible with the official ClinOCR-Bench baseline implementation.

The external experiment evaluates transcription generalization only. ClinOCR-Bench v1.0 provides full-document transcript ground truth rather than the field, patient-linkage, association, and FHIR annotations required for SafeOCR safety endpoints; therefore document-level WER is not converted into unsafe-accept or verified-coverage claims.

## 4. Results

### 4.1 Primary final evaluation

The frozen final set contained 288 evaluable critical-field cases.

| Method | Accepted | Review | Abstain | Verified coverage | Unsafe accepts | Unsafe accept rate |
|---|---:|---:|---:|---:|---:|---:|
| Primary OCR | 288 | 0 | 0 | 100.00% | 0 | 0.00% observed |
| Tesseract crop | 287 | 0 | 1 | 99.65% | 45 | 15.68% |
| Naive agreement | 242 | 46 | 0 | 84.03% | 0 | 0.00% observed |
| SafeOCR | 209 | 79 | 0 | 72.57% | 0 | 0.00% observed |

SafeOCR accepted 209 fields and sent 79 to review. Among accepted SafeOCR fields, zero unsafe accepts were observed. The 95% Wilson interval for the unsafe accept proportion was 0 to 0.01805.

The raw primary OCR baseline also observed zero accepted errors at full coverage. Therefore, this synthetic final set does not establish that SafeOCR is more accurate or safer than the primary OCR baseline.

The Tesseract crop baseline produced 45 unsafe accepts among 287 accepted fields, corresponding to an unsafe accept rate of 0.1568 (95% Wilson interval approximately 0.1193-0.2034).

### 4.2 Table association

A separate OCR-geometry-only association scorer evaluated 288/288 cases and observed zero table-association errors. The scorer did not use truth geometry to parse rows. This result is limited to the synthetic LabGold structure and should not be generalized to arbitrary real-world report layouts.

### 4.3 FHIR validator evidence

The canonical FHIR R4 bundle passed HL7 validator CLI 6.10.4 with zero errors. Seven warnings and one note were recorded. A deliberately invalid control was rejected with two errors.

This establishes that the tested export artifact conformed sufficiently to the validator gate. It does not provide a benchmark estimate of clinical FHIR mapping correctness because per-field FHIR mapping error was not included in the preregistered F6 final run.

### 4.4 Evidence traceability

The static evidence artifact demonstrates field-level traceability for a verified laboratory value. The example includes source-page SHA-256, bounding boxes for analyte/value/unit spans, OCR engine/version, policy version, verification signals, decision state, failed gates, and a deterministic explanation. The corresponding source crop is hash-bound.

### 4.5 External OCR generalization on ClinOCR-Bench

Both frozen OCR engines were evaluated on all 328 ClinOCR-Bench evaluation documents. Local Tesseract produced a mean WER of 0.5589 (95% CI 0.5209-0.5968) and median WER of 0.5647. Frozen PaddleOCR produced a lower overall mean WER of 0.4769 (95% CI 0.4372-0.5165) and median WER of 0.3659.

Performance varied substantially by artifact type. PaddleOCR mean WER was 0.1149 on normal documents, 0.2694 on poor-quality documents, 0.2847 on tables, 0.4256 on handwriting, 0.9035 on rotated documents, and 0.9276 on mixed-artifact documents. The PaddleOCR run recorded 57 runtime failures; these cases were retained in the denominator and scored as empty predictions under the frozen failure policy. Tesseract similarly showed strong artifact sensitivity, with mean WER ranging from 0.1089 on normal documents to 0.9225 on mixed-artifact documents.

These results are reported as transcription-generalization evidence only. They do not establish field-level clinical safety, and the local Tesseract run is not described as an exact reproduction of the benchmark authors' software environment.

## 5. Discussion

### 5.1 Principal findings

SafeOCR demonstrates that a clinical OCR pipeline can make **acceptance** an explicit, auditable decision rather than treating every OCR output as equally eligible for structured export. The system binds fields to source pixels, applies independent and structural checks, exposes review/abstention as first-class outcomes, and gates FHIR export on verification.

The primary SafeOCR operating point traded automation coverage for a conservative acceptance policy: 72.57% of critical fields were automatically verified, while 27.43% were routed to review. No unsafe accepts were observed among the 209 automatically verified fields, but the confidence interval remains non-zero and the result cannot be interpreted as proof of zero risk.

### 5.2 Why the primary OCR result matters

The most important negative result is that raw primary OCR also observed zero accepted errors at 100% coverage on LabGold. This prevents a stronger claim that the SafeOCR gate reduced unsafe accepted error relative to the primary OCR baseline.

This is not a result to hide. It identifies a limitation of the synthetic benchmark: the primary recognizer performed too well on the frozen cases to expose enough failure modes for a comparative safety claim. SafeOCR's current contribution is therefore the **verification contract, traceability, and governed evaluation framework**, not demonstrated superiority on this benchmark.

Future evaluation should deliberately increase realism without tuning to the final set: more heterogeneous scanners, compression artifacts, handwritten overlays, multi-page reports, unusual units, ambiguous identities, multi-column layouts, and real-world field-level annotations.

### 5.3 Relation to selective prediction

The SafeOCR policy is consistent with the clinical selective-prediction principle that abstention can be preferable to forced prediction [@swaminathan2024selective]. However, SafeOCR's mechanism differs from learned reject-option models such as SelectiveNet [@geifman2019selectivenet]. It uses deterministic evidence gates rather than a single learned confidence function.

This design favors inspectability: a blocked field can state whether the cause was failed independent agreement, instability, unit invalidity, association ambiguity, identity ambiguity, or runtime failure. The trade-off is that the v0.1 policy is likely conservative and may sacrifice coverage.

### 5.4 Relation to conformal verification and risk control

Recent clinical extraction work uses conformal methods to control accepted extraction risk [@kim2025conformalEHR]. Learn-then-Test provides a more general framework for finite-sample risk control [@angelopoulos2025learntest]. SafeOCR v0.1 does not yet offer such a guarantee. The Wilson interval is descriptive and should not be confused with a distribution-free acceptance-risk guarantee.

A strong next research direction is to retain SafeOCR's evidence gates while calibrating a higher-level acceptance policy with a formal risk-control procedure on an independent calibration set.

### 5.5 Provenance as a clinical OCR property

Provenance in SafeOCR is not a retrospective log added after extraction. It is part of the field contract. A critical field that cannot be tied back to source pixels cannot reach VERIFIED_AUTO. This makes provenance operational: it constrains automation rather than merely documenting it.

This aligns with prior work emphasizing provenance and semantic interoperability in healthcare [@daumke2019fhir; @margheri2020provenance], while moving the provenance boundary down to OCR evidence regions.

### 5.6 External validity

ClinOCR-Bench improves the availability of public, PHI-free clinical OCR evaluation and includes realistic scan artifacts [@hsu2026clinocr]. SafeOCR's v0.1 integration uses the benchmark under a no-tuning contract, but we deliberately do not report critical-field safety metrics from transcript-only ground truth.

To evaluate SafeOCR properly on external documents, a future study should add a governed annotation layer containing field identity, exact value, unit, patient/document linkage, structural association, and source-region evidence. Those annotations must be created without using SafeOCR outputs to define the gold standard.

## 6. Limitations

First, SafeOCR-LabGold is synthetic. It is useful for deterministic corruption and preregistered evaluation, but it does not represent the full distribution of real clinical scanning failures.

Second, the primary OCR baseline had zero observed errors on the frozen final set. The study therefore cannot establish SafeOCR superiority over that baseline.

Third, only one frozen SafeOCR operating point is reported. A post-hoc final-set threshold sweep would violate the evaluation contract, so the current paper does not present a continuous SafeOCR risk-coverage curve.

Fourth, the patient-attribution result is limited by benchmark construction and does not constitute real-world multi-patient identity evaluation.

Fifth, FHIR validator conformance is not equivalent to clinical mapping correctness. The preregistered final benchmark did not estimate a FHIR mapping error rate.

Sixth, the static evidence report demonstrates traceability mechanics but is not a validated clinical human-factors interface.

Seventh, the study does not evaluate diagnosis, treatment, or clinical decision-making and must not be interpreted as a medical-device validation.

## 7. Future Work

The next study should focus on **external field-level validation** rather than additional synthetic optimization. Priority work includes:

1. a field-level ClinOCR-Bench annotation extension with independent adjudication;
2. real-world de-identified laboratory reports from multiple institutions and scanner sources;
3. explicit stress sets for decimal/sign/comparator corruption, ambiguous units, wrong-row association, and patient identity conflict;
4. formal risk control or conformal calibration layered over the evidence gates;
5. prospective human-review studies measuring review time, correction rate, and reviewer agreement;
6. FHIR mapping correctness measured separately from structural validator conformance;
7. cross-engine evaluation to determine whether the verification contract generalizes beyond the PaddleOCR/Tesseract reference pair.

## 8. Conclusion

Clinical OCR should not be evaluated only as a transcription problem when its output is intended for structured healthcare data. SafeOCR introduces a field-level verification contract in which evidence binding, independent checks, explicit review/abstention, and provenance-preserving FHIR export are connected in one fail-closed pipeline.

On the frozen v0.1 synthetic evaluation, SafeOCR automatically verified 72.57% of critical fields with zero observed unsafe accepts, but the primary OCR baseline also produced zero observed errors at full coverage. The appropriate conclusion is therefore not that SafeOCR is superior, but that selective, evidence-grounded OCR verification is technically feasible, reproducible, and ready for stronger external validation.

## Data and Code Availability

SafeOCR is intended for public research release under Apache-2.0. The v0.1 release contains the source code, frozen evaluation artifacts, risk/coverage output, FHIR validation evidence, and static evidence-report artifacts. The public benchmark path uses synthetic and public PHI-free data.

## Ethics and Safety Statement

No real protected health information is required for the public v0.1 evaluation. SafeOCR is research software and is not intended for diagnosis, treatment decisions, or unsupervised clinical use.

## References

See `references.bib`.
