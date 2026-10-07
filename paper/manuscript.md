# SafeOCR: Evidence-Grounded Selective Verification for Clinical OCR with Provenance-Preserving FHIR Export

## Abstract

### Objective

To develop and evaluate SafeOCR, a healthcare-specific verification layer that permits structured export only when critical OCR fields satisfy explicit evidence gates.

### Materials and Methods

SafeOCR v0.1 combines PaddleOCR with second-engine Tesseract rereads, structural checks, perturbation consistency, numeric and unit validation, provenance, and fail-closed review states. We evaluated a frozen policy on 288 synthetic critical-field cases, transcription generalization on 328 ClinOCR-Bench evaluation documents, and an oracle-localised verifier-component study on 238 public laboratory-report images.

### Results

On SafeOCR-LabGold, primary OCR made 0/288 errors (95% Wilson upper bound 1.316%). SafeOCR accepted 209/288 fields with 0/209 errors (upper bound 1.805%) while routing 79 correct fields to review; this endpoint therefore did not demonstrate a safety gain. On ClinOCR-Bench, PaddleOCR mean WER was 0.4769 versus 0.5589 for local Tesseract, but PaddleOCR had 57/328 runtime failures (17.4%), concentrated in rotated and mixed subsets, and failures were scored as empty predictions. In the laboratory-report component study, all 1,850 eligible primary numeric readings were exact; 375/1,850 passed the component gates with 0/375 numeric errors. Post-outcome exploratory analysis found 38/375 passes (10.1%) had an analyte or unit mismatch.

### Discussion

SafeOCR implements an artifact-bound selective-verification pipeline, but the current safety endpoints contained no primary-OCR errors for the gates to intercept.

### Conclusion

The study establishes feasibility, auditability, and failure costs, not a demonstrated reduction in accepted error.

## 1. Background and Significance

Scanned and paper-origin clinical documents remain common in healthcare workflows, including external laboratory reports and legacy records. OCR combined with information extraction can convert such documents into structured data, but published clinical pipelines primarily evaluate transcription or extraction performance. Laboratory-report systems have demonstrated useful OCR and entity-extraction accuracy [@ma2023labocr; @li2024tabular], while scanned-EHR studies show that preprocessing, layout, recognition, and downstream NLP interact materially in end-to-end performance [@hsu2022scanned].

For downstream clinical use, transcription accuracy is necessary but not sufficient. A character-level error can change a decimal point, sign, comparator, or unit; a correctly read value can still be unsafe if linked to the wrong analyte, row, or patient. Conventional OCR confidence does not directly establish whether a field is sufficiently supported for automated structured export.

Selective prediction offers a complementary framing: systems may abstain when the expected cost of error is high rather than force a prediction on every case [@geifman2019selectivenet]. In clinical data abstraction, selective prediction can improve utility when abstention is preferable to an incorrect prediction [@swaminathan2024selective], and recent work has explored statistical risk control and conformal verification for accepted extractions [@angelopoulos2025learntest; @kim2025conformalEHR].

Traceability is also required for trustworthy downstream reuse. FHIR provides a standardized interoperability layer, while prior work has connected clinical text mining and provenance with FHIR-based exchange [@daumke2019fhir; @margheri2020provenance]. However, conformance and provenance do not themselves prove that an OCR-derived field was correctly read from source pixels.

Recent systems narrow the novelty space further. Girda and Groza introduced deterministic source-grounded trust promotion for laboratory data with same-row evidence, provenance, and review retention [@girda2026review]. RAPTOR+ evaluates clinical field extraction together with source-image bounding-box grounding [@abioye2026raptorplus], and verified-abstention OCR has also been reported [@benhmida2025ontology]. SafeOCR therefore does not claim novelty for OCR, grounding, abstention, provenance, or FHIR individually.

SafeOCR instead asks a narrower systems question: **can a fail-closed evidence contract be specified and evaluated transparently, and what automation coverage, review burden, and failure modes result under frozen operating points?** The current primary OCR baselines make no errors on the primary safety endpoints, so this study cannot estimate a reduction in accepted error attributable to the verification gate.

This paper makes four contributions:

1. an evidence-bound clinical OCR data model in which structured fields retain source-page and source-region provenance;
2. a fail-closed selective verification policy with explicit VERIFIED_AUTO, REVIEW_REQUIRED, and ABSTAINED terminal states;
3. a provenance-preserving FHIR R4 export gate that permits automated export only after verification;
4. a prespecified, commit-timestamped evaluation framework that reports accepted error jointly with verified coverage and preserves calibration/final-evaluation separation.

We frame SafeOCR as a systems-and-evaluation contribution. OCR, evidence gating, abstention, provenance, and FHIR are not individually novel. Closely related 2026 work already demonstrates source-grounded trust promotion for laboratory data [@girda2026review]. The contribution claimed here is therefore narrower: the specification and artifact-bound evaluation of a field-level healthcare OCR verification contract that couples pixel evidence, second-engine rereading, perturbation stability, patient linkage, explicit criticality, selective decisions, and gated FHIR export.

### Related Work

#### Clinical OCR and structured extraction

Clinical OCR and information-extraction systems have demonstrated that scanned healthcare documents, including laboratory reports, can be converted into structured data while remaining sensitive to image quality, layout, and table structure [@ma2023labocr; @li2024tabular; @hsu2022scanned]. Recent resources broaden this setting: ClinOCR-Bench evaluates common scan artifacts [@hsu2026clinocr], MedStruct-S and Wang et al. study semi-structured extraction under OCR noise and open key spaces [@li2026medstructs; @wang2026keycoverage], and MedRepBench evaluates report-grounded structured interpretation [@shang2026medrepbench].

The closest safety-oriented precedents substantially narrow SafeOCR's novelty claim. Girda and Groza use deterministic source-grounded trust promotion with same-row evidence, provenance, and review retention for laboratory data [@girda2026review]. RAPTOR+ evaluates clinical field extraction jointly with source-image bounding-box grounding [@abioye2026raptorplus], while ontology-constrained OCR with verified abstention provides an adjacent precedent [@benhmida2025ontology]. SafeOCR therefore does not claim novelty for OCR, visual grounding, evidence gating, or abstention individually; its contribution is the integrated verification and evaluation contract.

#### Selective prediction and abstention

Selective prediction trades automation coverage for lower conditional error [@geifman2019selectivenet] and has shown value in clinical data abstraction when abstention is preferable to a wrong prediction [@swaminathan2024selective]. Learn-then-Test and conformal verification provide stronger accepted-risk control frameworks [@angelopoulos2025learntest; @kim2025conformalEHR]. SafeOCR uses this framing but does not claim a conformal guarantee; v0.1 relies on deterministic gates and descriptive Wilson intervals.

#### Provenance and FHIR interoperability

Clinical text mining, SMART Text2FHIR, printed-form transformation, and healthcare provenance systems establish prior art for mapping extracted clinical information into FHIR and retaining provenance [@daumke2019fhir; @miller2023smarttext2fhir; @werlitz2025printedfhir; @margheri2020provenance]. SafeOCR uses these concepts as an operational verification boundary: accepted fields retain source-region and decision provenance, and non-verified fields are blocked from automated FHIR export.

## 2. Materials and Methods

### 2.1 Scope and safety boundary

SafeOCR v0.1 is research software for laboratory-report OCR verification. It is not a medical device and does not provide diagnosis, treatment recommendations, or clinical decision support. Medication documents, free-form handwritten physician notes, radiology/pathology image interpretation, and automatic correction of clinically implausible text are outside v0.1 scope.

The reference execution path is local-first and PHI-free for public evaluation.

### 2.2 System architecture

The pipeline is:

1. immutable document/page ingestion;
2. primary OCR and layout proposal;
3. construction of evidence-bound clinical field candidates;
4. second-engine critical-crop re-reading;
5. deterministic verification signals;
6. terminal decision: VERIFIED_AUTO, REVIEW_REQUIRED, or ABSTAINED;
7. FHIR R4 export only for VERIFIED_AUTO fields;
8. static evidence report with source crop, decision reason, and provenance.

PaddleOCR 3.7.0 is the primary full-page OCR path. Tesseract 5.4.0.20240606 is used as an independent critical-crop re-reader and classical baseline.

### 2.3 Evidence-bound field representation

An immutable page asset records source-document SHA-256, page index, dimensions, and page-image SHA-256. OCR proposals are represented as candidate spans containing engine identity, source page, bounding box, raw text, and engine-native confidence where available.

A structured laboratory field retains analyte text, value, unit, source spans, structural association, criticality, and patient/document linkage. The associated EvidenceRecord records verification signals, policy version, terminal decision, failed gates, and sufficient information to recover the supporting pixel region.

Correctness includes association. A numerically correct value linked to the wrong analyte, unit, row, date, or patient is considered incorrect.

### 2.4 Criticality

The v0.1 policy treats numeric laboratory values, units, sign/decimal/comparator semantics, patient identity linkage, and meaning-changing row/column associations as critical. Analyte identity, specimen/date/time, reference range, and abnormal flags are treated as high criticality. Criticality controls verification strictness but never rewrites the source reading.

### 2.5 Verification signals

A critical field may be automatically verified only when all mandatory gates pass.

**Visual grounding.** The field must be tied to a unique source page and recoverable pixel region.

**Structural association.** The analyte-value-unit relationship and row/column identity must be unambiguous.

**Second-engine reread.** The primary OCR reading is compared with a Tesseract reading of the bounded critical crop. This provides engine diversity but is not statistically independent because both engines operate on the same primary-defined crop.

**Perturbation stability.** The same Tesseract crop reread is repeated under four frozen, mild non-destructive image perturbations. Instability blocks automatic acceptance; this signal is therefore related to, rather than independent of, the second-engine agreement signal.

**Numeric parsing.** Decimal point, sign, exponent, comparator, and categorical interpretation must be unambiguous.

**Unit validation.** Unit parsing is checked and may veto export. Unit knowledge is not allowed to silently replace source text.

**Patient/document linkage.** Ambiguous patient identity blocks patient-level structured export.

**Runtime health.** OCR, verification, and export exceptions fail closed.

Engine-native confidence is not interpreted as a calibrated probability.

### 2.6 Decision states

Every candidate field reaches exactly one terminal state:

- **VERIFIED_AUTO:** all required evidence gates pass; automated structured export is permitted.
- **REVIEW_REQUIRED:** a plausible candidate exists, but evidence is insufficient or conflicting; automatic export is blocked.
- **ABSTAINED:** the system cannot establish a reliable field value; automatic export is blocked.

No fallback converts REVIEW_REQUIRED or ABSTAINED into VERIFIED_AUTO.

### 2.7 FHIR R4 export gate

Only VERIFIED_AUTO fields may enter the FHIR export path. The export artifact includes provenance linking the structured resource back to source-document evidence. v0.1 targets FHIR R4 (4.0.1).

The FHIR runtime gate used HL7 validator CLI 6.10.4. The canonical valid bundle passed with zero validator errors; a deliberately invalid control was rejected with two errors. The validator produced seven warnings and one note on the valid bundle. These results demonstrate structural/conformance validation, not extraction correctness.

### 2.8 Evaluation contract

The evaluation contract was prespecified in version-controlled, commit-timestamped protocols and separates calibration and final-evaluation roles. It was not registered in an external preregistration service. Final-evaluation outcomes cannot be routed into a tuning API, and threshold or policy changes after final-set inspection are prohibited.

Primary metrics are:

- Critical Field Exact Accuracy (CFEA);
- Unsafe Accept Rate (UAR): incorrect accepted fields / accepted fields;
- Verified Coverage (VC): accepted fields / evaluable fields;
- Review Rate;
- Abstention Rate;
- Patient Attribution Error Rate, where estimable;
- Table Association Error Rate, where estimable;
- FHIR Mapping Error Rate, where estimable.

Binomial 95% Wilson intervals are reported descriptively for field-level unsafe accepted error proportions. They do not account for within-report clustering or paired acquisition variants and are not presented as population-level or distribution-free guarantees. Zero observed errors is never interpreted as zero underlying risk.

### 2.9 SafeOCR-LabGold

The frozen final SafeOCR-LabGold split contains 48 documents and 288 critical-field cases: 24 synthetic records, each rendered as a clean/corrupted pair across three templates (classic, compact, and grid), with six critical fields per document. The final split hash was frozen before execution. The primary final run was executed from a clean exact source head after calibration and qualification. Legacy per-field method metrics use benchmark truth geometry only to align OCR spans to known field regions for scoring; they are not end-to-end field-discovery metrics. The separate table-association scorer uses OCR geometry only.

The compared operating points were:

- raw primary OCR;
- Tesseract critical-crop reading;
- naive exact agreement;
- SafeOCR verification policy.

The primary v0.1 SafeOCR policy has one frozen operating point. We do not retrospectively sweep thresholds on the final set.

### 2.10 External OCR generalization

ClinOCR-Bench was pinned as a synthetic, template-generated, PHI-free clinical-document OCR benchmark. Its release contains 384 documents, including 56 exemplars and 328 evaluation documents spanning normal, handwriting, poor-quality, rotated, table, and mixed-artifact subsets [@hsu2026clinocr]. Before outcome inspection, we froze a no-tuning protocol for the two OCR engines already used by SafeOCR. Ground-truth transcripts were inaccessible to the OCR runner and were opened only by a separate scorer after all predictions had been written. Word error rate (WER), substitution, deletion, and insertion components were calculated using whitespace tokenization compatible with the official ClinOCR-Bench baseline implementation.

The external experiment evaluates transcription generalization only. ClinOCR-Bench v1.0 provides full-document transcript ground truth rather than the field, patient-linkage, association, and FHIR annotations required for SafeOCR safety endpoints; therefore document-level WER is not converted into unsafe-accept or verified-coverage claims.

### 2.11 External laboratory-report verifier-component evaluation

We used the public laboratory-report image collection released by Xue et al. and subsequently used and described by Ma et al. [@xue2020labocr; @ma2023labocr]. Ma et al. describe 238 de-identified Chinese laboratory-report images derived from 119 paper reports and captured by scanners and smartphones under varied illumination. Their reported dual-annotation Cohen's kappa of 0.89 applies to the separate PKU1 dataset, not to this public image collection; the provenance of the public collection's text/cell labels is not documented in the source materials available to this study. Before scoring, frozen PaddleOCR inference was executed on all 238 images with the annotation source inaccessible to the OCR runner; no OCR runtime failures occurred.

Gold annotations were opened only after OCR to identify analyte, numeric-value, and unit regions for an **oracle-localised verifier-component evaluation**. They were not used to generate OCR predictions, choose preprocessing, tune thresholds, or locate regions during OCR inference. Scoring used laboratory table 2, excluding the header row, and aligned OCR spans to gold cells only after OCR with a minimum truth-area overlap of 0.25; candidates were ranked by overlap and then OCR confidence. Eligible rows required non-empty analyte, value, and unit annotations plus a parseable numeric value. Duplicate annotations in the estimand-relevant analyte/value/unit cells were excluded fail-closed rather than arbitrarily adjudicated.

A component pass required visual grounding, second-engine Tesseract agreement on the numeric-value crop, stability across the four frozen perturbations, structural association, successful numeric parsing, and valid unit syntax. The primary external component endpoint was prespecified in code before outcome generation as an incorrect numeric value among component-passed fields (commit 47433ae8fb429671489ac530dfd05c95a82bfaf4; the result was frozen later at commit 6f082d8dad6d576c8add7a5914609c68785ef665). This endpoint is narrower than the paper's general full-field correctness definition and does not test end-to-end field discovery, analyte semantic verification, patient linkage, the complete VERIFIED_AUTO policy, or FHIR mapping.

## 3. Results

### 3.1 Primary final evaluation

The frozen final set contained 288 evaluable critical-field cases.

| Method | Accepted | Review | Abstain | Verified coverage | Unsafe accepts | Unsafe accept rate |
|---|---:|---:|---:|---:|---:|---:|
| Primary OCR | 288 | 0 | 0 | 100.00% | 0 | 0.00% observed |
| Tesseract crop | 287 | 0 | 1 | 99.65% | 45 | 15.68% |
| Naive agreement | 242 | 46 | 0 | 84.03% | 0 | 0.00% observed |
| SafeOCR | 209 | 79 | 0 | 72.57% | 0 | 0.00% observed |

SafeOCR accepted 209 fields and sent 79 to review. Among accepted SafeOCR fields, zero unsafe accepts were observed; the 95% Wilson interval was 0 to 0.01805. However, raw primary OCR also made 0/288 errors at full coverage, with a tighter 95% Wilson upper bound of 0.01316. Thus all 79 SafeOCR reviews were correct fields under benchmark truth, and this endpoint provided no errors for the verification gate to intercept. The result measures feasibility and review cost, not a demonstrated safety gain over the primary OCR baseline.

The Tesseract crop baseline produced 45 unsafe accepts among 287 accepted fields, corresponding to an unsafe accept rate of 0.1568 (95% Wilson interval approximately 0.1193-0.2034).

### 3.2 Table association

A separate OCR-geometry-only association scorer evaluated 288/288 cases and observed zero table-association errors. The scorer did not use truth geometry to parse rows. This result is limited to the synthetic LabGold structure and should not be generalized to arbitrary real-world report layouts.

### 3.3 FHIR validator evidence

The canonical FHIR R4 bundle passed HL7 validator CLI 6.10.4 with zero errors. Seven warnings and one note were recorded. A deliberately invalid control was rejected with two errors.

This establishes that the tested export artifact conformed sufficiently to the validator gate. It does not provide a benchmark estimate of clinical FHIR mapping correctness because per-field FHIR mapping error was not included in the prespecified, commit-timestamped F6 final run.

### 3.4 Evidence traceability

The static evidence artifact illustrates field-level traceability for one verified laboratory value. The example includes source-page SHA-256, bounding boxes for analyte/value/unit spans, OCR engine/version, policy version, verification signals, decision state, failed gates, and a deterministic explanation. The corresponding source crop is hash-bound.

### 3.5 External OCR generalization on ClinOCR-Bench

Both frozen OCR engines were scored across all 328 ClinOCR-Bench evaluation documents under the frozen failure policy. Local Tesseract produced a mean WER of 0.5589 (95% CI 0.5209-0.5968) and median WER of 0.5647. Frozen PaddleOCR produced a mean WER of 0.4769 (95% CI 0.4372-0.5165) and median WER of 0.3659, but it incurred 57/328 runtime failures (17.4%): 33/56 rotated documents and 24/48 mixed-artifact documents. Under the frozen failure policy, these failures were retained in the denominator and scored as empty predictions.

Performance varied substantially by artifact type. PaddleOCR mean WER was 0.1149 on normal documents, 0.2694 on poor-quality documents, 0.2847 on tables, 0.4256 on handwriting, 0.9035 on rotated documents, and 0.9276 on mixed-artifact documents. The PaddleOCR run recorded 57/328 runtime failures (17.4%); these were retained in the denominator and scored as empty predictions under the frozen failure policy. Failures were concentrated in rotated documents (33/56) and mixed-artifact documents (24/48), making runtime robustness a material part of the external transcription result. Tesseract similarly showed strong artifact sensitivity, with mean WER ranging from 0.1089 on normal documents to 0.9225 on mixed-artifact documents.

The prespecified reproducibility comparison also showed substantial differences between the official ClinOCR-Bench Tesseract medians and the local frozen Tesseract medians: normal 0.0866 vs 0.1099, handwriting 0.8228 vs 0.8135, poor-quality 0.8184 vs 0.8205, rotation 1.0000 vs 0.5802, tables 0.4578 vs 0.3244, and mixed 1.0000 vs 0.9846. The large rotation discrepancy likely reflects environment or orientation/page-segmentation differences and prevents treating the local run as an exact reproduction of the authors' Tesseract environment.

| ClinOCR subset | Official Tesseract median WER | Local frozen Tesseract median WER |
|---|---:|---:|
| Normal | 0.0866 | 0.1099 |
| Handwriting | 0.8228 | 0.8135 |
| Poor quality | 0.8184 | 0.8205 |
| Rotation | 1.0000 | 0.5802 |
| Tables | 0.4578 | 0.3244 |
| Mixed | 1.0000 | 0.9846 |

These results are transcription-generalization evidence only. ClinOCR-Bench is synthetic and not laboratory-report-specific, and the SafeOCR verification contract is not exercised on it. The failure concentration in rotated and mixed documents is therefore interpreted as a fail-closed engineering finding rather than field-level clinical safety evidence.

### 3.6 External verifier-component evaluation on public laboratory reports

The public laboratory-report dataset yielded 1,850 eligible analyte-value-unit rows from 2,219 candidate laboratory rows after frozen eligibility and annotation-integrity rules. Exclusions were 275 unsupported gold values, 74 missing units, 13 ambiguous duplicate rows, 4 missing values, and 3 missing analytes. Eligible rows came from 180/238 images; 58 images contributed no eligible row under the frozen table/eligibility rules.

| Ma2023 cohort step | Rows |
|---|---:|
| Candidate laboratory rows | 2,219 |
| Excluded: unsupported gold value | 275 |
| Excluded: missing unit | 74 |
| Excluded: ambiguous duplicate critical cell | 13 |
| Excluded: missing value | 4 |
| Excluded: missing analyte | 3 |
| Eligible rows | 1,850 | The primary value span was localised in 1,850/1,850 cases and the complete analyte/value/unit context in 1,849/1,850. Primary OCR reproduced the annotated numeric value in all 1,850 eligible cases, while the complete analyte-value-unit tuple was exact in 1,461/1,850 (78.97%).

The component gates passed 375/1,850 fields (20.27%). Second-engine numeric-value agreement passed in 654/1,850 (35.35%), perturbation stability in 449/1,850 (24.27%), structural association in 1,837/1,850 (99.30%), and unit validation in 1,347/1,850 (72.81%). The overlapping gate funnel was 654 with second-engine agreement, 442 with both agreement and perturbation stability, 377 after additionally requiring valid unit syntax, and 375 after additionally requiring structural association.

| Frozen component funnel | Rows | Coverage |
|---|---:|---:|
| Eligible | 1,850 | 100.00% |
| Second-engine agreement | 654 | 35.35% |
| Agreement + perturbation stability | 442 | 23.89% |
| + valid unit syntax | 377 | 20.38% |
| + structural association / component pass | 375 | 20.27% | No runtime failures occurred. No component-passed field contained an incorrect numeric value (0/375; observed rate 0%, 95% Wilson interval 0-1.014%), but the ungated primary numeric reading was also exact in 1,850/1,850 rows (95% Wilson upper bound 0.207%). Therefore the numeric endpoint contained no primary-OCR errors for the component gates to intercept; all 1,475 rejected numeric values were correct under the frozen reference labels.

Component-pass coverage was similar for scanner images (192/926; 20.73%) and illumination/smartphone variants (183/924; 19.81%). In contrast, complete primary field exactness fell from 814/926 (87.90%) on scans to 647/924 (70.02%) under illumination variants.

A prespecified primary claim is not made for full field-tuple correctness among component passes because the frozen component endpoint concerns the numeric value. A separately labelled post-outcome diagnostic found that 38/375 passed fields (10.13%; 95% Wilson interval 7.47%-13.60%) had an analyte or unit mismatch: 36 analyte mismatches and 2 unit mismatches, with no numeric-value mismatches. Equivalently, 337/375 tuples were exact. This exploratory diagnostic is given equal prominence because it exposes the narrower scope of numeric verification; it does not alter the frozen primary component endpoint.

## 4. Discussion

### 4.1 Principal findings

SafeOCR shows that a clinical OCR pipeline can make **acceptance** an explicit, auditable decision rather than treating every OCR output as equally eligible for structured export. The system binds fields to source pixels, applies independent and structural checks, exposes review/abstention as first-class outcomes, and gates FHIR export on verification.

The primary SafeOCR operating point traded automation coverage for a conservative acceptance policy: 72.57% of critical fields were automatically verified, while 27.43% were routed to review. Because primary OCR was already correct on all 288 fields, the 79 reviews intercepted no endpoint errors and the gated confidence bound was wider than the ungated bound. This result therefore quantifies review cost and feasibility rather than demonstrating reduced accepted error.

### 4.2 Why the primary OCR result matters

The most important negative result is that raw primary OCR also observed zero accepted errors at 100% coverage on LabGold. This prevents a stronger claim that the SafeOCR gate reduced unsafe accepted error relative to the primary OCR baseline.

This is not a result to hide. It identifies a limitation of the synthetic benchmark: the primary recognizer performed too well on the frozen cases to expose enough failure modes for a comparative safety claim. SafeOCR's current contribution is therefore the **verification contract, traceability, and governed evaluation framework**, not demonstrated superiority on this benchmark.

Future evaluation should deliberately increase realism without tuning to the final set: more heterogeneous scanners, compression artifacts, handwritten overlays, multi-page reports, unusual units, ambiguous identities, multi-column layouts, and real-world field-level annotations.

### 4.3 Relation to selective prediction

The SafeOCR policy is consistent with the clinical selective-prediction principle that abstention can be preferable to forced prediction [@swaminathan2024selective]. However, SafeOCR's mechanism differs from learned reject-option models such as SelectiveNet [@geifman2019selectivenet]. It uses deterministic evidence gates rather than a single learned confidence function.

This design favors inspectability: a blocked field can state whether the cause was failed independent agreement, instability, unit invalidity, association ambiguity, identity ambiguity, or runtime failure. The trade-off is that the v0.1 policy is likely conservative and may sacrifice coverage.

### 4.4 Relation to conformal verification and risk control

Recent clinical extraction work uses conformal methods to control accepted extraction risk [@kim2025conformalEHR]. Learn-then-Test provides a more general framework for finite-sample risk control [@angelopoulos2025learntest]. SafeOCR v0.1 does not yet offer such a guarantee. The Wilson interval is descriptive and should not be confused with a distribution-free acceptance-risk guarantee.

A strong next research direction is to retain SafeOCR's evidence gates while calibrating a higher-level acceptance policy with a formal risk-control procedure on an independent calibration set.

### 4.5 Provenance as a clinical OCR property

Provenance in SafeOCR is not a retrospective log added after extraction. It is part of the field contract. A critical field that cannot be tied back to source pixels cannot reach VERIFIED_AUTO. This makes provenance operational: it constrains automation rather than merely documenting it.

This aligns with prior work emphasizing provenance and semantic interoperability in healthcare [@daumke2019fhir; @margheri2020provenance], while moving the provenance boundary down to OCR evidence regions.

### 4.6 External validity

ClinOCR-Bench improves the availability of public, PHI-free clinical OCR evaluation and includes realistic scan artifacts [@hsu2026clinocr]. SafeOCR's v0.1 integration uses the benchmark under a no-tuning contract, but we deliberately do not report critical-field safety metrics from transcript-only ground truth.

To evaluate SafeOCR properly on external documents, a future study should add a governed annotation layer containing field identity, exact value, unit, patient/document linkage, structural association, and source-region evidence. Those annotations must be created without using SafeOCR outputs to define the gold standard.

### 4.7 What the real-report component evaluation establishes

The public laboratory-report evaluation moves the verifier component from synthetic documents to a de-identified image collection with scanner and smartphone/illumination variants. Under the frozen numeric endpoint, no accepted numeric value was incorrect among 375 passes; however, the primary OCR value was also correct in all 1,850 eligible rows, so the 20.27% component coverage bought no measured numeric-error reduction and instead quantifies a substantial rejection cost.

The same experiment exposes the paper's most important external failure mode. Thirty-eight of 375 component-passed rows (10.1%) were not exact across the entire analyte-value-unit tuple even though every accepted numeric value was correct. Most diagnostic mismatches involved the analyte text and two involved the unit. Some observed differences appear to be OCR/format variants, whereas others can change field identity; without independent clinical adjudication they should not be collapsed into a single semantic-error category. The result therefore supports second-engine verification of the numeric value, not complete semantic correctness of the field tuple.

A direct design implication is that future SafeOCR versions should extend second-engine verification beyond the numeric crop to analyte identity and unit semantics, with explicit adjudication of clinically equivalent formatting variants. This finding also reinforces the decision to keep patient linkage and FHIR correctness as separate, unclaimed endpoints in the present external component study.

### Limitations

First, SafeOCR-LabGold is synthetic. It is useful for deterministic corruption and prespecified, commit-timestamped evaluation, but it does not represent the full distribution of real clinical scanning failures.

Second, the primary OCR baseline had zero observed errors on the frozen final set. The study therefore cannot establish SafeOCR superiority over that baseline.

Third, only one frozen SafeOCR operating point is reported. A post-hoc final-set threshold sweep would violate the evaluation contract, so the current paper does not present a continuous SafeOCR risk-coverage curve.

Fourth, the patient-attribution result is limited by benchmark construction and does not constitute real-world multi-patient identity evaluation.

Fifth, FHIR validator conformance is not equivalent to clinical mapping correctness. The prespecified final benchmark did not estimate a FHIR mapping error rate.

Sixth, the static evidence report demonstrates traceability mechanics but is not a validated clinical human-factors interface.

Seventh, the external laboratory-report experiment is oracle-localised after OCR: gold geometry identifies which OCR spans are evaluated, so it is a verifier-component study rather than end-to-end extraction validation. The public collection's label-generation provenance is undocumented, and contamination of a long-public dataset in modern OCR training data cannot be excluded. The experiment does not evaluate patient linkage, full VERIFIED_AUTO behavior, or FHIR mapping; 13 estimand-relevant rows with duplicate annotations were excluded fail-closed; and the full-tuple mismatch analysis is explicitly post-outcome and exploratory.

Eighth, field-level Wilson intervals do not model dependence within the 24 clean/corrupt LabGold record pairs or within the external laboratory-report images, nor do they model the asserted scan/illumination pairing; they are descriptive bounds rather than cluster-robust population inference.

Ninth, the study does not evaluate diagnosis, treatment, or clinical decision-making and must not be interpreted as a medical-device validation.

### Future Work

Priority next steps are independently adjudicated multi-institution field-level validation; second-engine verification of analyte identity, unit semantics, and patient linkage in addition to numeric values; formal risk-control calibration on a held-out set; and prospective human-review studies measuring correction burden, agreement, and FHIR mapping correctness separately from structural conformance.

## 5. Conclusion

Clinical OCR should not be evaluated only as a transcription problem when its output is intended for structured healthcare data. SafeOCR introduces a field-level verification contract in which evidence binding, independent checks, explicit review/abstention, and provenance-preserving FHIR export are connected in one fail-closed pipeline.

On the frozen v0.1 synthetic evaluation, SafeOCR automatically verified 72.57% of critical fields, but the primary OCR baseline also produced zero observed errors and all 79 reviewed fields were correct under benchmark truth. In the oracle-localised public laboratory-report evaluation, the primary numeric reading was exact in all 1,850 eligible rows, so 0/375 numeric errors among component passes could not demonstrate a safety gain; exploratory analysis instead found analyte or unit mismatches in 38/375 passes. The appropriate conclusion is therefore not that SafeOCR is safer, superior, or clinically validated, but that an evidence-gated workflow can be implemented and audited, at substantial coverage cost, and that future prespecified evaluation must include genuine primary-OCR errors and verification beyond numeric values.

## Data and Code Availability

SafeOCR is intended for public research release under Apache-2.0 with source code, frozen protocols, scoring code, and derived evidence artifacts. SafeOCR-LabGold is synthetic and ClinOCR-Bench is public and PHI-free. The public de-identified Ma et al. source images are not redistributed by SafeOCR; they should be obtained from the original source subject to upstream terms.

## Ethics and Safety Statement

SafeOCR-LabGold is synthetic and ClinOCR-Bench is PHI-free. The external laboratory-report analysis uses a public image collection described by Ma et al. as de-identified and originally released with Xue et al.'s work; SafeOCR does not redistribute those source images. This study involved no new participant recruitment, intervention, or access to identifiable patient data. SafeOCR is research software and is not intended for diagnosis, treatment decisions, or unsupervised clinical use. Any journal-specific institutional-review statement will be limited to a determination actually obtained or required for the author's jurisdiction and affiliation.

## AI-use Disclosure

Generative AI tools were used for drafting assistance, code generation and review, literature-discovery support, and language editing. All scientific claims, citations, code changes, analyses, and manuscript text were reviewed and verified by the human author(s). AI tools were not authors and did not determine authorship or final scientific conclusions.

## References

See `references.bib`.
