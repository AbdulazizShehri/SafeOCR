# SafeOCR arXiv source package

This directory is the submission-oriented source package for the SafeOCR preprint.

## Frozen scientific boundary

The arXiv package is a presentation layer over the frozen SafeOCR evidence. It must not change thresholds, cohorts, preprocessing, eligibility rules, or outcome definitions after Ma2023 outcome inspection.

## Contents

- `main.tex`: self-contained LaTeX manuscript generated from the current submission manuscript.
- `references.bib`: bibliography snapshot for the preprint.
- `ARXIV_METADATA.md`: title, abstract, category and submission notes.
- `build_check.py`: static package checks that require only Python.

The two main figures are rendered natively with TikZ so the package does not depend on external SVG conversion.

## Before submission

1. Confirm the public author display name and any affiliation to be shown on the preprint.
2. Run `python arxiv/build_check.py`.
3. Compile `arxiv/main.tex` in a TeX Live environment compatible with arXiv.
4. Inspect every table, figure, citation, Unicode symbol, and page break in the PDF.
5. Confirm the exact paper commit/tag and add it to the metadata.
6. Confirm arXiv endorsement/category requirements in the submitting account.
7. Upload only source files required to compile the paper; do not include private notes, review logs, credentials, local caches, or raw non-redistributable datasets.

## Recommended category

Primary candidate: `cs.CV` (clinical OCR/document vision).
Potential cross-list: `cs.AI`.

Final classification is subject to arXiv moderation and the submitting author's account/endorsement status.
