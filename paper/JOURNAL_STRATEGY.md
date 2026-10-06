# SafeOCR Publication Strategy

Checked: 2026-10-06

## Primary target — JAMIA

Article type: Research and Applications.

Why it fits:
- SafeOCR is a biomedical/health informatics methods-and-evaluation study.
- The article type explicitly accepts formulation, implementation, evaluation, innovative IT applications, and detailed new methodology.
- The current study has a reproducible software artifact, frozen evaluation contract, public benchmark integration, and explicit safety/limitations reporting.
- JAMIA is the strongest realistic first submission for the present evidence level.

Current format constraints:
- main text: up to 4,000 words;
- structured abstract: up to 250 words;
- tables: up to 4;
- figures: up to 6;
- references: unlimited;
- required main-text section: Background and Significance;
- abstract headings: Objective, Materials and Methods, Results, Discussion, Conclusion.

Cost strategy:
- standard subscription publication does not require an open-access fee;
- open access is optional after acceptance.
- This makes JAMIA preferable to a mandatory-APC journal when publication funding is uncertain.

## Transfer-ready backup — JAMIA Open

Article type: Research and Applications.

Why it fits:
- same broad biomedical and health informatics domain;
- same 4,000-word / 250-word structured-abstract envelope;
- encourages public code and reusable non-sensitive data;
- indexed in PubMed Central and Scopus.

Important difference:
- JAMIA Open is Gold Open Access and requires an APC unless covered by an institutional agreement, waiver, or discount.
- A lay summary of up to 200 words is required/encouraged in current instructions.

The manuscript should be formatted so a JAMIA rejection can be converted rapidly to JAMIA Open without redesigning the study.

## Stretch target — npj Digital Medicine

Do not submit the current v0.1 manuscript here unless the evidence package materially strengthens.

Reason:
- scope strongly values clinical application and validated AI/digital tools;
- current journal guidance states that it typically does not consider pre-clinical basic studies or small-scale preliminary studies;
- SafeOCR v0.1 is intentionally preclinical and does not yet include prospective clinical workflow validation or independent field-level clinical annotation on real reports.

A future multi-institution external field-level validation or prospective review study could make npj Digital Medicine substantially more plausible.

## Additional fallback

BMC Medical Informatics and Decision Making is scientifically aligned with clinical informatics and has already published closely related laboratory-report OCR work. It is a defensible fallback if AMIA journals decline the manuscript.

## Submission sequence

1. Complete the frozen ClinOCR-Bench external transcription-generalization experiment.
2. Integrate external results without changing the preregistered protocol.
3. Reduce main text to <=4,000 words after all results are known.
4. Build no more than 4 main tables and 6 main figures.
5. Move reproducibility detail, full per-subset metrics, and extended claims ledger to supplement.
6. Run final literature update through the submission date.
7. Run a claim-by-claim source audit and statistical audit.
8. Prepare JAMIA title page, structured abstract, data/code availability, funding, competing interests, CRediT, and AI-use disclosure.
9. Submit to JAMIA Research and Applications.
10. Keep a transfer-ready JAMIA Open package.

## Decision rule

If the external ClinOCR experiment reveals credible generalization and the full paper remains methodologically coherent, submit to JAMIA.

If external results expose substantial OCR brittleness, do not hide them. Reframe the paper around evidence-gated failure containment, document the failure modes, and still target JAMIA if the safety-system contribution remains strong.

Never retune the frozen primary policy to make the external results look better.
