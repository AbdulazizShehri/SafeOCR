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

## Release sequence

1. Run `python scripts/prepare_hf_labgold.py --output dist/SafeOCR-LabGold`.
2. Verify `manifest.jsonl`, `metadata.jsonl`, `dataset_info.json`, the copied dataset card, and generated image hashes.
3. Create `MedScaleAI/SafeOCR-LabGold` and upload the generated `dist/SafeOCR-LabGold` directory as the dataset repository root.
4. Create `MedScaleAI/SafeOCR` as a Static Space and upload `huggingface/space/*` as the Space repository root.
5. Verify both public URLs anonymously.
6. Insert the final arXiv identifier into the GitHub README, HF Space README, and HF dataset card.
7. Create the frozen paper/software release and tag.
8. Re-run GitHub CI, CodeQL, and arXiv Preflight on the exact release head.
9. Submit arXiv.
10. Immediately verify all cross-links.

## Publication gate

Do not publish the final arXiv submission until:

- canonical scholarly author identity is confirmed;
- arXiv manuscript license is selected;
- HF repositories are live and public;
- no dead links remain;
- the Space clearly states that it is synthetic/research-only;
- the GitHub release head is exact-head qualified.
