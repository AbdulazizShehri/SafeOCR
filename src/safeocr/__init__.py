"""SafeOCR healthcare verification core."""

__version__ = "0.1.0"

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
    "__version__",
    "decide",
    "export_allowed",
]
