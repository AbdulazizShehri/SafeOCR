"""SafeOCR healthcare verification core."""

from safeocr.contracts import (
    BoundingBox,
    CandidateSpan,
    Criticality,
    DecisionRecord,
    DecisionState,
    EvidenceRecord,
    LabFieldCandidate,
    PageAsset,
    VerificationSignals,
    decide,
    export_allowed,
)

__all__ = [
    "BoundingBox",
    "CandidateSpan",
    "Criticality",
    "DecisionRecord",
    "DecisionState",
    "EvidenceRecord",
    "LabFieldCandidate",
    "PageAsset",
    "VerificationSignals",
    "decide",
    "export_allowed",
]
