# External OCR Generalization Protocol

Status: preregistered before opening ClinOCR-Bench evaluation images or ground-truth transcripts.

## Objective

Measure how the two SafeOCR v0.1 reference OCR engines generalize across realistic clinical scan artifacts without changing the frozen SafeOCR verification policy.

This experiment is **not** a field-level SafeOCR safety evaluation. ClinOCR-Bench supplies human-audited full-document transcripts, not SafeOCR critical-field, patient-linkage, row-association, or FHIR-mapping annotations.

## Frozen external source

- Dataset: ClinOCR-Bench v1.0
- Release: https://github.com/ClinOCR-Bench/ClinOCR-Bench/releases/tag/v1.0
- Release asset: `ClinOCR-Bench-v1.0.zip`
- Release asset bytes: `119227531`
- Release asset SHA-256: `ce1d231138050abf7f458ba5e6bd75c6ee2f3832b72f22296843da4c5ba45457`
- License: MIT
- Documents: 384 total
- Evaluation split: 328 documents
- Exemplar split: 56 documents
- Subsets: normal, handwriting, poor, rotated, tables, mixed

## Frozen baseline semantics

The official ClinOCR-Bench baseline repository is pinned for metric semantics only:

- repository: `ClinOCR-Bench/ClinOCR-Bench-Baseline`
- inspected commit: `306e5502c9d4f5de39bb03689a8d9bc5df101031`
- primary metric: word error rate (WER)
- tokenization: Python whitespace split
- WER: Levenshtein substitutions + deletions + insertions divided by reference word count

SafeOCR reimplements the metric locally rather than importing the benchmark repository at runtime.

## Engines

No model selection is permitted from ClinOCR-Bench results.

1. SafeOCR primary engine:
   - PaddleOCR 3.7.0
   - detection: PP-OCRv6_small_det
   - recognition: PP-OCRv6_small_rec
   - backend: ONNX Runtime CPU
   - text recognition batch size: 1
   - no document-orientation classifier
   - no document unwarping
   - no text-line orientation model

2. Independent reference engine:
   - Tesseract 5.4.0.20240606
   - default English OCR path used for whole-page external transcription

No VLM, cloud OCR, prompt, exemplar, or one-shot data is used.

## Evaluation set

All 328 official `test` documents are evaluated.

No result may be used to:
- tune SafeOCR thresholds;
- select another PaddleOCR model;
- change image preprocessing;
- change reading order heuristics;
- alter the SafeOCR acceptance policy;
- select or remove subsets;
- select easier cases.

If an engine fails on a document, the failure is recorded and the prediction is treated as empty for WER unless the failure is a benchmark-infrastructure failure that prevents all scoring.

## Outputs

For each engine and document:
- doc_id;
- subset;
- OCR runtime status;
- full predicted text;
- WER;
- substitution rate;
- deletion rate;
- insertion rate;
- runtime seconds.

Aggregate outputs:
- document count;
- failure count;
- median WER by subset;
- mean WER by subset;
- interquartile range by subset;
- overall median and mean WER;
- bootstrap 95% confidence interval for mean WER using a fixed seed;
- paired per-document WER delta between PaddleOCR and Tesseract.

## Interpretation

This experiment may support claims about:
- external OCR robustness;
- artifact-specific degradation;
- relative OCR-engine performance;
- the motivation for independent rereading and explicit review gates.

It may **not** support claims about:
- SafeOCR unsafe-accept rate on ClinOCR-Bench;
- SafeOCR field-level verified coverage on ClinOCR-Bench;
- patient-attribution accuracy;
- table-association accuracy for specific clinical fields;
- FHIR mapping accuracy;
- clinical deployment safety.

## Leakage controls

- Evaluation images and ground-truth transcripts must remain unopened until this protocol is committed.
- The 56 exemplar/train documents are not used for tuning or preprocessing selection.
- There is one zero-shot run per frozen engine configuration.
- Post-hoc changes require a new protocol version and cannot replace the original result.
