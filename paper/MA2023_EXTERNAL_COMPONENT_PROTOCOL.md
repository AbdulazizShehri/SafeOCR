# Ma et al. 2023 External Verifier Component Protocol

Status: FROZEN BEFORE VERIFIER OUTCOME INSPECTION

This protocol evaluates verification-component generalization on the public de-identified laboratory-report dataset used by Ma et al. (2023). It is not an end-to-end extraction evaluation and not a full SafeOCR policy evaluation.

## Dataset

- 238 public de-identified report images from 119 source reports.
- 119 scanner images and 119 illumination/photo variants.
- 18,402 annotated text regions in labels_src.json.
- Main laboratory-table annotations include test item, result, unit, reference range, method, source coordinates, and row/column indices.
- The separate PKU1 validation set is not public and is excluded.

## Redistribution boundary

No dataset-wide license statement was identified in the repository audit. The public dataset will be used only for research evaluation with attribution. SafeOCR will not redistribute the source images or annotations. Only derived aggregate metrics and reproducibility metadata may be released.

## Oracle-localisation boundary

Gold geometry may be used only after OCR inference to identify which OCR spans correspond to annotated analyte, value, and unit regions for evaluation.

Gold text or geometry must not be passed into PaddleOCR or Tesseract, alter preprocessing, alter recognition thresholds, rewrite OCR text, select a model, tune verifier thresholds, or create evidence that the OCR engines did not produce.

The manuscript must describe this as an oracle-localised verifier component evaluation.

## Frozen cohort and runtime

- Include every annotated laboratory row with non-empty analyte and result text.
- Numeric critical-field analysis is restricted to result strings accepted by the existing SafeOCR parse_critical_value grammar.
- Unit-dependent analysis is restricted to rows with a non-empty annotated unit.
- OCR-empty and unmatched cases remain in coverage denominators.
- Report scanner and illumination/photo variants separately and together.
- PaddleOCR 3.7.0 with PP-OCRv6_small_det and PP-OCRv6_small_rec on ONNX Runtime CPU.
- Tesseract 5.4.0.20240606.
- Existing SafeOCR crop, perturbation, parsing, geometry, and unit rules.
- No fine-tuning, model substitution, language-pack substitution, or outcome-driven preprocessing changes.

## Outcomes and claim boundary

Report total images and rows, eligible numeric fields, OCR-region match coverage, primary OCR exact-value accuracy, independent Tesseract agreement, perturbation stability, structural association, unit-valid rate where evaluable, component-pass coverage, incorrect component passes per component passes with a 95% Wilson interval, and scanner-versus-photo stratification.

The public dataset does not supply the governed patient-linkage truth contract required by the full SafeOCR v0.1 policy. This study therefore does not estimate full VERIFIED_AUTO coverage, patient-attribution error, FHIR mapping error, clinical deployment safety, or prospective clinical utility. No candidate from this study is promoted through the production FHIR export gate.
