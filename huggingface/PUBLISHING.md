# Hugging Face Publication Plan

Target organization: `MedScaleAI`

Target repositories:

- Space: `MedScaleAI/SafeOCR`
- Dataset: `MedScaleAI/SafeOCR-LabGold`

## Publication principle

The Hugging Face launch must go live at the same time as the arXiv submission package.

The public release surface should give a reviewer one clear path:

`arXiv paper -> GitHub source/evidence -> HF Space -> HF dataset`

## Space boundary

The official v0.1 Space is intentionally static and PHI-free.

It:

- demonstrates the terminal decision policy interactively;
- uses synthetic laboratory examples only;
- contains no patient-document upload;
- does not pretend to execute PaddleOCR or Tesseract in the browser;
- links to the full local implementation on GitHub.

This avoids turning a research verification package into an unvalidated public clinical OCR service.

## Dataset boundary

Publish only SafeOCR-generated synthetic artifacts and metadata.

Do not redistribute:

- Xue/Ma laboratory-report source images;
- ClinOCR-Bench files outside their upstream terms;
- any external benchmark content not explicitly permitted.

## Canonical renderer and manifest gate

The canonical SafeOCR-LabGold v0.1 Hugging Face publication package has:

- `manifest_sha256 = 3a3fcdf1e3e045c0b6f8b334457d1e22dbd247a6a556e08235f808143abf5cec`;
- Python 3.12.13;
- Pillow 12.3.0;
- FreeType 2.14.3;
- JPEG feature version 8.0;
- zlib 1.3.1.zlib-ng;
- platform `win32:AMD64`.

The corruption pipeline includes a JPEG round-trip. Regeneration under a different underlying JPEG implementation can produce different corrupted PNG bytes. A package with a different manifest hash is non-canonical for the v0.1 publication and must not be uploaded as the paper-linked benchmark.

## Release sequence

1. Generate or stage `dist/SafeOCR-LabGold` from the canonical renderer stack.
2. Verify `manifest.jsonl`, root `metadata.jsonl`, derived `images/metadata.jsonl`, `dataset_info.json`, the copied dataset card, and every generated image hash.
3. Require `dataset_info.json.manifest_sha256` to equal `3a3fcdf1e3e045c0b6f8b334457d1e22dbd247a6a556e08235f808143abf5cec`.
4. Create `MedScaleAI/SafeOCR-LabGold` and upload the verified `dist/SafeOCR-LabGold` directory as the dataset repository root.
5. Create `MedScaleAI/SafeOCR` as a Static Space and upload `huggingface/space/*` as the Space repository root.
6. Verify both public URLs anonymously.
7. Insert the final arXiv identifier into the GitHub README, HF Space README, and HF dataset card.
8. Create the frozen paper/software release and tag.
9. Re-run GitHub CI, CodeQL, and arXiv Preflight on the exact release head.
10. Submit arXiv.
11. Immediately verify all cross-links.

## Publication gate

Do not publish the final arXiv submission until:

- canonical scholarly author identity is confirmed;
- arXiv manuscript license is selected;
- HF repositories are live and public;
- no dead links remain;
- the Space clearly states that it is synthetic/research-only;
- the GitHub release head is exact-head qualified.
