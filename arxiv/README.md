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

1. Use the confirmed author metadata from `ARXIV_METADATA.md`, including the ORCID and correspondence email.
2. Run `python arxiv/build_check.py`.
3. Compile `arxiv/main.tex` in a TeX Live environment compatible with arXiv.
4. Inspect every table, figure, citation, Unicode symbol, and page break in the PDF.
5. Build a clean source archive containing **only** `main.tex` and `references.bib` at the ZIP root. From the `arxiv/` directory, use `zip -X safeocr-arxiv-source.zip main.tex references.bib`.
6. Confirm the arXiv submission category and any endorsement requirements within the author's own account.
7. At submission, choose **arXiv.org perpetual, non-exclusive license 1.0** for the paper, not the Apache-2.0 software license.
8. Upload the clean source archive, inspect arXiv's compiled PDF, check metadata, and finalize submission as the author. Never upload private notes, review logs, credentials, local caches, or raw non-redistributable datasets.
9. Add the real arXiv identifier to the paper/repository/public project pages only after arXiv assigns it.

## Recommended category

Primary candidate: `cs.CV` (clinical OCR/document vision).
Potential cross-list: `cs.AI`.

Final classification is subject to arXiv moderation and the submitting author's account/endorsement status.
