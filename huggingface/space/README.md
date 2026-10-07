---
title: SafeOCR
emoji: 🧾
colorFrom: blue
colorTo: indigo
sdk: static
app_file: index.html
pinned: false
license: apache-2.0
short_description: Evidence-grounded selective verification for clinical OCR
---

# SafeOCR Verification Playground

Official public demonstration package for **SafeOCR v0.1**.

This Space is intentionally a **synthetic verification-policy explorer**. It does not accept patient documents and does not run a clinical OCR service. Use the controls to see how the frozen SafeOCR v0.1 decision contract routes evidence to:

- `VERIFIED_AUTO`
- `REVIEW_REQUIRED`
- `ABSTAINED`

The live demo uses only synthetic laboratory examples and mirrors the deterministic terminal decision policy implemented in the SafeOCR repository.

## Why no real patient upload?

SafeOCR v0.1 is research software, not a medical device or production clinical service. The public Space deliberately avoids collecting or processing PHI. The reproducible implementation, OCR adapters, evidence models, evaluation code, and FHIR export gate are available in the GitHub repository.

## Links

- GitHub: https://github.com/AbdulazizShehri/SafeOCR
- Dataset: https://huggingface.co/datasets/MedScaleAI/SafeOCR-LabGold
- Paper: arXiv identifier will be added at publication
- License: Apache-2.0

## Frozen v0.1 result boundary

On SafeOCR-LabGold, the primary OCR baseline made 0/288 errors. SafeOCR accepted 209/288 fields with 0/209 observed errors and routed 79 correct fields to review. Therefore the frozen evaluation does **not** demonstrate that SafeOCR is safer than the primary OCR baseline; it demonstrates a reproducible evidence-gated workflow and its automation/review cost.

Do not use this Space for diagnosis, treatment, or unsupervised clinical decisions.
