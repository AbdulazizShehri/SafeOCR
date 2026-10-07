# Literature Search Strategy

Last updated: 2026-10-07

## Objective

Identify prior work needed to position SafeOCR without overstating novelty or performance.

## Concept blocks

1. Clinical OCR / scanned medical documents / laboratory reports
2. Structured information extraction under OCR noise
3. Selective prediction / reject option / abstention in healthcare
4. Calibration / conformal prediction / accepted-error risk control
5. FHIR / provenance / traceability for extracted clinical data
6. Public clinical OCR benchmarks

## Sources used

- PubMed / PMC
- OpenAlex
- Cross-publisher web search for DOI verification
- PMLR / ICML
- AAAI Symposium Series
- arXiv
- HL7 FHIR R4 specification
- TinyFish academic-paper search
- SciSpace public discovery pages where useful for navigation

## Tool availability notes

- Consensus was available but the connected account had exhausted its monthly search quota during this review.
- Scite was connected but its MCP endpoint required a paid plan or active trial.
- Exa and Firecrawl were installed during the work; the manuscript does not depend on any single discovery provider.
- Discovery-tool output is not treated as a citation by itself. Bibliographic claims are anchored to publisher, PubMed/PMC, PMLR, arXiv, OpenAlex, or standards records.

## Inclusion criteria

Include papers that materially inform at least one SafeOCR design or evaluation claim:
- scanned clinical document OCR or IE;
- laboratory-report extraction;
- clinical selective prediction or abstention;
- risk control / conformal verification relevant to accepted extractions;
- FHIR/provenance/traceability;
- public clinical OCR benchmark design.

## Exclusion criteria

Exclude:
- generic OCR papers with no document/clinical relevance unless needed for a specific method;
- purely diagnostic imaging OCR;
- papers whose only relevance is broad "AI in healthcare" commentary;
- unverified secondary summaries when a primary paper/standard is available.

## Screening rule

A paper is cited only for the proposition directly supported by its reported task, methods, or results. SafeOCR-specific claims come only from canonical SafeOCR evidence artifacts.

## Update rule

Before submission, rerun the search for the period 2026-01-01 through the submission date and screen newly published clinical OCR, selective prediction, and clinical extraction-verification papers.


## 2026-10-07 adversarial-review update

The final preprint-oriented update specifically re-checked:

- original provenance of the public laboratory-report image collection;
- the distinction between the Xue public collection and Ma et al.'s separate PKU1 annotation exercise;
- peer-reviewed clinical document-AI predecessors;
- publication status of 2025-2026 OCR/structured-extraction references;
- current JAMIA reference and preprint policies;
- metadata for references flagged by independent adversarial review.

Verified additions/corrections from primary or publisher records include:

- Xue et al. 2020, IEEE Access, DOI 10.1109/ACCESS.2019.2961964, as the original published source associated with the public laboratory-report image collection;
- RAPTOR, MICCAI 2025, DOI 10.1007/978-3-032-04981-0_47, as a published clinical document-AI prior-art anchor;
- Werlitz et al. 2025, Stud Health Technol Inform 331:162-169, DOI 10.3233/SHTI251392;
- Ren et al. 2025, DIGITAL HEALTH 11:20552076251334431;
- Schäfer et al. 2025, EMBC, pp. 1-7;
- MedStruct-S as KSEM 2026 / LNCS 16636, pp. 131-141.

## Discovery-versus-evidence rule

Search and synthesis tools may identify candidate papers, but every manuscript bibliographic fact and substantive proposition is checked against a publisher, PubMed/PMC, proceedings, PMLR, official repository/release, or normative standards source before inclusion.

Consensus exhausted the connected monthly search allowance during the final review. Scite MCP required a paid plan or trial. These tool limits do not determine the evidence base: the final audit continued through primary publisher, PubMed/PMC, proceedings, standards, and official benchmark sources.

## Preprint surveillance

ArXiv-only work remains useful for novelty surveillance even when it is not eligible for a target journal's formal reference list. The literature matrix therefore distinguishes:

1. evidence suitable for the current arXiv preprint;
2. published/in-press references suitable for a future JAMIA bibliography;
3. unpublished preprints that constrain novelty wording internally.

Publication status must be refreshed again immediately before journal submission.
