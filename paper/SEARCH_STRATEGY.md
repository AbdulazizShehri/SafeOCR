# Literature Search Strategy

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
