# SafeOCR Submission Strategy

## Current recommendation

### Primary target: Journal of Biomedical Informatics (JBI)

Rationale:
- JBI explicitly positions itself as a methodology journal in biomedical informatics.
- SafeOCR's strongest contribution is methodological: a reproducible verification contract between OCR pixels and structured health data, not a clinical-effectiveness claim.
- The manuscript contains system design, formal decision states, evaluation methodology, provenance, interoperability, and reproducibility evidence.
- The study can be submitted without claiming live clinical benefit.
- The journal supports conventional publication as well as optional open access, so immediate APC-funded open access is not required for the scientific submission strategy.

What must be strong before submission:
- external OCR generalization;
- clear novelty positioning against 2025-2026 integrity-gating and verified-abstention work;
- figures that explain the evidence contract;
- exact reproducibility package;
- disciplined separation of conformance, extraction correctness, and clinical safety.

### Secondary target: JAMIA / JAMIA Open

JAMIA is attractive because the topic is directly medical-informatics and the selective-prediction literature we cite already appears there. However, the strongest JAMIA submission would benefit from real multi-institution or clinical-workflow validation.

JAMIA Open is an excellent scope fit for an open, reproducible informatics methods paper and is a realistic fallback if JBI reviewers judge the general methodological contribution too narrow. It is fully open access, so publication charges must be checked before submission.

### Stretch target after stronger clinical evidence: npj Digital Medicine

Do not submit the current v0.1 manuscript there first. The present study is deliberately preclinical, synthetic/PHI-free, and does not demonstrate patient or workflow outcomes. A later paper with:
- independently annotated real-world reports;
- multi-site external validation;
- clinician review study;
- prospective workflow evidence;
- formal risk control;
would be a substantially better fit.

## Preprint strategy

Release a carefully versioned preprint only after:
1. external generalization is frozen;
2. all references are verified;
3. figures are final;
4. code/evidence release is public and persistent;
5. the title/abstract no longer move materially.

Preferred preprint venues:
- arXiv (cs.AI / cs.CV with health-informatics framing where appropriate);
- medRxiv only if its scope and manuscript classification are appropriate at submission time.

## Paper positioning

Use a methods/evaluation title, not a product title.

Recommended title:
**SafeOCR: Evidence-Grounded Selective Verification for Clinical OCR with Provenance-Preserving FHIR Export**

Alternative:
**From Pixels to FHIR: Risk-Limiting Verification of Laboratory-Report OCR with Source-Grounded Evidence**

The first title is safer and more literal. The second is more memorable but should be used only if reviewers/editors are unlikely to interpret "risk-limiting" as a formal statistical guarantee.

## What will determine acceptance

Likely strengths:
- unusually explicit evidence and governance contract;
- transparent negative result against the primary OCR baseline;
- field-level provenance;
- independent OCR-family rereading;
- selective review rather than forced automation;
- reproducible FHIR validator evidence;
- public code and exact evaluation artifacts;
- external benchmark run preregistered before outcomes.

Likely reviewer attacks:
1. synthetic LabGold may be too easy;
2. zero primary-OCR errors mean SafeOCR's safety benefit is not demonstrated;
3. independent engine agreement may fail together under correlated OCR errors;
4. no prospective clinical evaluation;
5. no field-level external benchmark annotations;
6. no formal selective-risk guarantee;
7. no measured human-review burden;
8. FHIR conformance is not mapping correctness;
9. novelty overlaps emerging source-grounded integrity-gate work.

The manuscript should answer these directly rather than bury them.

## Submission package

Required before first submission:
- manuscript;
- cover letter;
- structured highlights / key points;
- graphical abstract or system figure;
- risk/coverage figure;
- external-generalization figure;
- supplementary methods;
- reporting checklist;
- reproducibility statement;
- data/code availability statement;
- author contribution statement;
- competing-interest statement;
- funding statement;
- ethics statement;
- limitations table;
- references with DOI verification.

## Do not optimize for prestige at the expense of fit

A rigorous JBI paper with public artifacts is more valuable academically than an overstated submission to a higher-profile clinical journal that is rejected because it lacks real clinical validation. The project should aim for the strongest journal supported by the evidence actually collected.
