# Grubby Humanization Audit

Date: 2026-10-07

Status: STYLE-DONOR AUDIT — NOT SCIENTIFIC EVIDENCE

The manuscript was processed manually through Grubby in four chunks because of a 1,500-word input limit. The returned text was **not** accepted wholesale. It was treated only as a source of stylistic alternatives and compared against the canonical SafeOCR manuscript.

## Acceptance rule

A Grubby edit was eligible only when it:
- improved readability or sentence flow;
- preserved every number, denominator, interval, citation, endpoint, cohort, and claim boundary;
- preserved technical terminology where terminology carries methodological meaning;
- did not strengthen evidence beyond the frozen artifacts;
- did not alter tables, scorer ordering, or protocol chronology.

## Material Grubby changes rejected

The following changes were rejected because they changed meaning, weakened precision, or introduced errors:

1. **Abstract conclusion drift**
   - Grubby: "decrease in the number of correct values passed"
   - Problem: this reverses the intended endpoint and is scientifically wrong.
   - Canonical boundary retained: no demonstrated reduction in accepted error.

2. **Ma2023 scorer ordering reversal**
   - Grubby changed candidate ranking to OCR confidence and then overlap.
   - Frozen scorer description is overlap first, then OCR confidence.
   - Canonical ordering retained exactly.

3. **Statistical wording corruption**
   - Grubby introduced "distribution inaccuracy" in the Wilson-interval limitation.
   - Canonical wording retained: the intervals are not distribution-free guarantees.

4. **Traceability overstatement**
   - Grubby changed the static artifact from something that "illustrates" traceability to something that "demonstrates" it.
   - The stronger claim was rejected.

5. **Unit-gate semantic drift**
   - Grubby paraphrased unit validation as "correct units".
   - This would imply semantic correctness beyond the implemented syntax/validation gate.
   - Canonical unit-validation terminology retained.

6. **Tuple overstatement**
   - Grubby paraphrased exact analyte-value-unit tuples as "full correctness".
   - The stronger interpretation was rejected.
   - Canonical wording remains tuple exactness.

7. **Risk-control terminology drift**
   - Grubby replaced statistical "risk-control" language with generic "risk management".
   - Canonical literature terminology retained.

8. **Collapsed tables**
   - Grubby flattened all Markdown tables into unstructured text.
   - Original table structure and values were restored unchanged.

9. **Typographical regressions**
   - Examples included "artiface", duplicated concepts in the criticality paragraph, and a duplicated "intervention" in the ethics statement.
   - None were accepted.

10. **Methodological wording drift**
    - Several sentences changed "unambiguous" or "valid" gates into "correct" gates.
    - Those edits were rejected because they imply stronger semantic guarantees than the implementation provides.

## Mechanical invariant audit after selective adoption

Comparison basis:
- canonical pre-humanization manuscript: main merge head `e1957ad11b20e28183d11995a5acb78145b995f0`;
- selective humanization branch: `paper/humanized-style-pass`.

Checks:
- numeric-token multiset: unchanged;
- citation-token multiset: unchanged;
- Markdown result tables: byte-for-byte unchanged;
- scorer ranking phrase `ranked by overlap and then OCR confidence`: preserved;
- oracle-localised verifier-component boundary: preserved;
- zero-event limitation: preserved;
- AI-use disclosure: preserved;
- no Grubby-introduced "distribution inaccuracy" wording;
- no "full correctness" overclaim;
- no incorrect abstract "decrease in the number of correct values passed" wording.

## Interpretation

The accepted edits are language edits only. They do not constitute a new analysis, new endpoint, new cohort, new result, or new scientific claim. The frozen SafeOCR v0.1 evidence remains unchanged.
