# SafeOCR External OCR Generalization Protocol — ClinOCR-Bench v1.0

Status: FROZEN BEFORE OUTCOME INSPECTION
Purpose: external OCR generalization evidence for the SafeOCR paper
Not a SafeOCR field-level safety validation

## Dataset

- ClinOCR-Bench v1.0
- Release asset SHA-256: `ce1d231138050abf7f458ba5e6bd75c6ee2f3832b72f22296843da4c5ba45457`
- Dataset repository commit: `3b720a951bb7eec4a4f4fb34a636e7335a19981e`
- 384 documents total
- 56 train/exemplar documents
- 328 test/evaluation documents
- Six subsets: normal, handwriting, poor, rotated, tables, mixed

The primary analysis uses only the official test/evaluation role.

## Research question

How do the two OCR engines already used by SafeOCR v0.1 generalize, without tuning, to a public external clinical scanned-document benchmark?

This experiment evaluates transcription generalization only. It does **not** estimate SafeOCR unsafe-accept rate, verified coverage, patient-linkage error, table-association error, or FHIR mapping error because ClinOCR-Bench v1.0 does not provide the field-level annotation contract required for those claims.

## Frozen OCR conditions

### Tesseract

- Use the locally installed Tesseract version already frozen by SafeOCR v0.1.
- Language: `eng`
- Page segmentation mode: `3`
- No image-specific tuning.
- No one-shot information.
- No access to ground truth during OCR.

### PaddleOCR

- Use the locally installed PaddleOCR version/model configuration already frozen by SafeOCR v0.1.
- Use the same full-page OCR path as SafeOCR.
- Recognition batch size may remain at the v0.1 memory-safe setting.
- No image-specific preprocessing selected after outcome inspection.
- No one-shot information.
- No access to ground truth during OCR.

## Frozen scoring

Use the official ClinOCR-Bench baseline implementation of:

`WER = (substitutions + deletions + insertions) / reference_word_count`

Tokenization is whitespace split exactly as implemented by the official baseline.

For each OCR engine report:

- overall N;
- mean WER with the official normal-approximation 95% CI;
- median WER with Q1-Q3;
- min-max;
- substitution, deletion, insertion components;
- the same statistics separately for all six artifact subsets.

The official baseline post-processing function may be used only to normalize OCR output formatting before scoring; it must be applied identically for the corresponding engine output.

## Primary comparison

The paper will report:
1. SafeOCR's local Tesseract reproduction versus the official published Tesseract benchmark values as a reproducibility check.
2. SafeOCR's frozen PaddleOCR engine as an external transcription-generalization result.
3. No statistical or qualitative claim that a lower WER proves lower clinical risk.

## Prohibited actions

- no model fine-tuning;
- no threshold tuning;
- no selection of preprocessing based on test outcomes;
- no exclusion of hard subsets;
- no deletion of failed documents from denominators;
- no manual correction of OCR outputs;
- no use of one-shot ground truth or test ground truth as OCR input;
- no conversion of document-level WER into SafeOCR field-level safety metrics;
- no claim of superiority unless directly supported by the prespecified comparison.

## Failure handling

Engine/runtime failures remain in the experiment record. If an OCR engine produces no text for a test image, the prediction is the empty string and is scored accordingly. Infrastructure failures that prevent execution are reported separately and do not silently remove cases.

## Outcome-inspection lock

Ground-truth transcript contents and WER outcomes must not be inspected until:
1. this protocol is committed;
2. the runner code passes tests and static checks;
3. the runner is reviewed for dataset-role leakage.

After outcomes are inspected, the frozen OCR conditions and scoring rules above may not be changed for the primary external experiment.
