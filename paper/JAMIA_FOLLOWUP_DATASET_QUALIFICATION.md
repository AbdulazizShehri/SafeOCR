# JAMIA Follow-up Dataset Qualification — RJUA-MedDQA

Status: PRE-OUTCOME METADATA QUALIFICATION ONLY — NO SAFEORC OUTPUTS INSPECTED

Date: 2026-10-07

This note evaluates whether RJUA-MedDQA is a plausible source dataset for the separate follow-up error-interception study defined in `paper/JAMIA_FOLLOWUP_ERROR_STUDY_PROTOCOL.md`.

It does **not** freeze the study, select a final cohort, run SafeOCR, inspect OCR outcomes, or establish that the dataset is suitable. The study remains DRAFT until annotation sufficiency is verified.

## Published identity

Published paper:

Congyun Jin, Ming Zhang, Xiaowei Ma, Yujiao Li, Yingbo Wang, Yabo Jia, Yuliang Du, Tao Sun, Haowen Wang, Cong Fan, Jinjie Gu, Chenfei Chi, Xiangguo Lv, Fangzhou Li, Wei Xue, Yiran Huang. *RJUA-MedDQA: A Multimodal Benchmark for Medical Document Question Answering and Clinical Reasoning*. Proceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and Data Mining. 2024:5218–5229. DOI: 10.1145/3637528.3671644.

Official repository: `AQ-MedAI/medDQA_benchmark`.

## Public metadata verified before model execution

The official repository describes:
- 2,000 medical-report images;
- real-world Chinese medical reports with a urology emphasis;
- photographs, scanned-PDF images, and screenshots;
- challenging image conditions including rotation, skew, blur, and incomplete information;
- dataset licensing under CC BY-NC-SA 4.0;
- repository code under AGPL.

These characteristics make the dataset relevant to the failure modes missing from the current SafeOCR evidence, especially acquisition variability and low-quality document images.

## Why it is only a candidate

The published benchmark is primarily a multimodal document-question-answering and clinical-reasoning resource. SafeOCR requires a different reference standard: field-level analyte-value-unit truth plus enough row/source identity to score end-to-end laboratory extraction.

Therefore the following questions are **unresolved** and must be answered from dataset files/annotations before the protocol can be frozen:

1. Which released documents can be identified as laboratory reports without looking at SafeOCR predictions?
2. Do released ESRA/restored-text annotations preserve laboratory-table rows and analyte/value/unit structure at sufficient fidelity?
3. Can a deterministic, prediction-blind extraction from released annotations create full-tuple gold?
4. If not, can a blinded manual annotation layer be created lawfully under the dataset license?
5. Does the laboratory-report subset contain enough documents and enough baseline OCR errors to support the planned study?
6. Can all derived annotation artifacts be shared under compatible CC BY-NC-SA terms?

## Leakage firewall

Before these questions are resolved:
- do not run PaddleOCR or SafeOCR on a prospective final subset;
- do not inspect model-specific errors to choose documents;
- do not tune document filters against OCR outcomes;
- do not change SafeOCR v0.1 gates, thresholds, models, language packs, or preprocessing.

A metadata/annotation inspection may identify document type and determine whether gold construction is possible. It must not inspect SafeOCR outputs.

## Qualification decision

Current decision: **PROMISING BUT NOT YET QUALIFIED**.

Reasons:
- publication status is strong (peer-reviewed KDD 2024);
- acquisition diversity directly addresses a current evidence gap;
- the dataset has an explicit public dataset license;
- however, full-tuple laboratory-field annotation sufficiency has not yet been established.

No final-set manifest should be created until the annotation-sufficiency gate is resolved.
