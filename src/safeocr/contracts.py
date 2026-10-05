from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-fA-F]{64}$")


class Criticality(StrEnum):
    """Clinical verification strictness tier."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"


class DecisionState(StrEnum):
    """Terminal automation decision for one field."""

    VERIFIED_AUTO = "VERIFIED_AUTO"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ABSTAINED = "ABSTAINED"


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Pixel-space evidence rectangle using half-open bounds."""

    x1: int
    y1: int
    x2: int
    y2: int

    def __post_init__(self) -> None:
        if min(self.x1, self.y1) < 0:
            raise ValueError("bounding-box coordinates must be non-negative")
        if self.x2 <= self.x1 or self.y2 <= self.y1:
            raise ValueError("bounding box must have positive width and height")


@dataclass(frozen=True, slots=True)
class PageAsset:
    """Immutable identity and geometry for one rendered source page."""

    document_sha256: str
    page_index: int
    width_px: int
    height_px: int
    page_sha256: str

    def __post_init__(self) -> None:
        if not _SHA256_RE.fullmatch(self.document_sha256):
            raise ValueError("document_sha256 must be a 64-character hexadecimal SHA-256")
        if not _SHA256_RE.fullmatch(self.page_sha256):
            raise ValueError("page_sha256 must be a 64-character hexadecimal SHA-256")
        if self.page_index < 0:
            raise ValueError("page_index must be non-negative")
        if self.width_px <= 0 or self.height_px <= 0:
            raise ValueError("page dimensions must be positive")

        object.__setattr__(self, "document_sha256", self.document_sha256.lower())
        object.__setattr__(self, "page_sha256", self.page_sha256.lower())


@dataclass(frozen=True, slots=True)
class CandidateSpan:
    """One untrusted OCR proposal bound to exact source geometry."""

    page: PageAsset
    box: BoundingBox
    text: str
    engine_name: str
    engine_version: str
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("candidate span text must be non-empty")
        if not self.engine_name.strip():
            raise ValueError("engine_name must be non-empty")
        if not self.engine_version.strip():
            raise ValueError("engine_version must be non-empty")
        if self.box.x2 > self.page.width_px or self.box.y2 > self.page.height_px:
            raise ValueError("candidate span bounding box must be contained by its source page")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("engine-native confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class LabFieldCandidate:
    """Structured laboratory-field candidate with explicit visual evidence."""

    analyte_text: str
    value_text: str
    unit_text: str | None
    criticality: Criticality
    source_spans: tuple[CandidateSpan, ...]

    def __post_init__(self) -> None:
        if not self.analyte_text.strip():
            raise ValueError("analyte_text must be non-empty")
        if not self.value_text.strip():
            raise ValueError("value_text must be non-empty")
        if not self.source_spans:
            raise ValueError("a laboratory field must reference at least one source span")
        document_hashes = {span.page.document_sha256 for span in self.source_spans}
        if len(document_hashes) != 1:
            raise ValueError(
                "a laboratory field cannot combine source spans from multiple documents"
            )
        if self.unit_text is not None and not self.unit_text.strip():
            raise ValueError("unit_text must be non-empty when provided")


@dataclass(frozen=True, slots=True)
class VerificationSignals:
    """Explicit verification gates.

    These booleans are policy inputs, not calibrated probabilities.
    """

    candidate_present: bool
    visual_grounded: bool
    independent_agreement: bool
    perturbation_stable: bool
    structural_association: bool
    numeric_parse_unambiguous: bool
    unit_valid: bool
    patient_linkage_unambiguous: bool
    runtime_healthy: bool

    def __post_init__(self) -> None:
        for name in (
            "candidate_present",
            "visual_grounded",
            "independent_agreement",
            "perturbation_stable",
            "structural_association",
            "numeric_parse_unambiguous",
            "unit_valid",
            "patient_linkage_unambiguous",
            "runtime_healthy",
        ):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be a bool")


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """Deterministic terminal decision and the gates that failed."""

    state: DecisionState
    criticality: Criticality
    failed_gates: tuple[str, ...]

    def to_json(self) -> str:
        """Serialize deterministically for evidence manifests."""

        payload = {
            "criticality": self.criticality.value,
            "failed_gates": list(self.failed_gates),
            "state": self.state.value,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """Immutable evidence bundle for one laboratory-field decision."""

    field: LabFieldCandidate
    signals: VerificationSignals
    decision: DecisionRecord
    policy_version: str

    def __post_init__(self) -> None:
        if not self.policy_version.strip():
            raise ValueError("policy_version must be non-empty")
        expected = decide(self.signals, criticality=self.field.criticality)
        if self.decision != expected:
            raise ValueError("decision must be derived from the supplied verification signals")

    def to_json(self) -> str:
        """Serialize the complete evidence record deterministically."""

        payload = {
            "decision": {
                "criticality": self.decision.criticality.value,
                "failed_gates": list(self.decision.failed_gates),
                "state": self.decision.state.value,
            },
            "field": {
                "analyte_text": self.field.analyte_text,
                "criticality": self.field.criticality.value,
                "source_spans": [
                    {
                        "box": {
                            "x1": span.box.x1,
                            "x2": span.box.x2,
                            "y1": span.box.y1,
                            "y2": span.box.y2,
                        },
                        "confidence": span.confidence,
                        "engine_name": span.engine_name,
                        "engine_version": span.engine_version,
                        "page": {
                            "document_sha256": span.page.document_sha256,
                            "height_px": span.page.height_px,
                            "page_index": span.page.page_index,
                            "page_sha256": span.page.page_sha256,
                            "width_px": span.page.width_px,
                        },
                        "text": span.text,
                    }
                    for span in self.field.source_spans
                ],
                "unit_text": self.field.unit_text,
                "value_text": self.field.value_text,
            },
            "policy_version": self.policy_version,
            "signals": {
                "candidate_present": self.signals.candidate_present,
                "independent_agreement": self.signals.independent_agreement,
                "numeric_parse_unambiguous": self.signals.numeric_parse_unambiguous,
                "patient_linkage_unambiguous": self.signals.patient_linkage_unambiguous,
                "perturbation_stable": self.signals.perturbation_stable,
                "runtime_healthy": self.signals.runtime_healthy,
                "structural_association": self.signals.structural_association,
                "unit_valid": self.signals.unit_valid,
                "visual_grounded": self.signals.visual_grounded,
            },
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


_REVIEW_GATES: Final[tuple[tuple[str, str], ...]] = (
    ("independent_agreement", "independent_agreement"),
    ("perturbation_stable", "perturbation_stable"),
    ("structural_association", "structural_association"),
    ("numeric_parse_unambiguous", "numeric_parse_unambiguous"),
    ("unit_valid", "unit_valid"),
    ("patient_linkage_unambiguous", "patient_linkage_unambiguous"),
)


def decide(signals: VerificationSignals, *, criticality: Criticality) -> DecisionRecord:
    """Apply the F1 fail-closed terminal decision policy."""

    if not signals.candidate_present:
        return DecisionRecord(
            DecisionState.ABSTAINED,
            criticality,
            ("candidate_present",),
        )
    if not signals.visual_grounded:
        return DecisionRecord(
            DecisionState.ABSTAINED,
            criticality,
            ("visual_grounded",),
        )
    if not signals.runtime_healthy:
        return DecisionRecord(
            DecisionState.ABSTAINED,
            criticality,
            ("runtime_healthy",),
        )

    failed = tuple(
        output_name
        for attribute_name, output_name in _REVIEW_GATES
        if not getattr(signals, attribute_name)
    )
    if failed:
        return DecisionRecord(DecisionState.REVIEW_REQUIRED, criticality, failed)

    return DecisionRecord(DecisionState.VERIFIED_AUTO, criticality, ())


def export_allowed(evidence: EvidenceRecord) -> bool:
    """Return whether an evidence-backed field may be exported automatically."""

    return evidence.decision.state is DecisionState.VERIFIED_AUTO
