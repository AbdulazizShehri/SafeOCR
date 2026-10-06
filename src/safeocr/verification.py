from __future__ import annotations

import hashlib
import hmac
import importlib
import importlib.metadata
import io
import json
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from itertools import pairwise
from typing import Final, cast

from PIL import Image, ImageEnhance

from safeocr.contracts import (
    BoundingBox,
    CandidateSpan,
    EvidenceRecord,
    LabFieldCandidate,
    VerificationSignals,
    decide,
)
from safeocr.ocr import CriticalCrop, CropRead

_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-fA-F]{64}$")
_NUMERIC_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<comparator><=|>=|<|>)?\s*"
    r"(?P<number>[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?)$"
)
_QUALITATIVE_TOKENS: Final[frozenset[str]] = frozenset(
    {
        "POSITIVE",
        "NEGATIVE",
        "DETECTED",
        "NOT DETECTED",
        "REACTIVE",
        "NONREACTIVE",
        "NON-REACTIVE",
    }
)

APPROVED_PERTURBATIONS: Final[tuple[str, ...]] = (
    "brightness_095",
    "brightness_105",
    "contrast_105",
    "scale_110",
)


class ValueKind(StrEnum):
    NUMERIC = "NUMERIC"
    QUALITATIVE = "QUALITATIVE"


class UnitStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    MISSING = "MISSING"
    RUNTIME_ERROR = "RUNTIME_ERROR"


@dataclass(frozen=True, slots=True)
class ParsedCriticalValue:
    kind: ValueKind
    normalized_text: str
    comparator: str | None = None
    numeric_value: Decimal | None = None
    qualitative_token: str | None = None


@dataclass(frozen=True, slots=True)
class FieldEvidenceInput:
    field: LabFieldCandidate
    analyte_span: CandidateSpan | None
    value_span: CandidateSpan | None
    unit_span: CandidateSpan | None
    value_crop: CriticalCrop | None


@dataclass(frozen=True, slots=True)
class PerturbationImage:
    name: str
    png_bytes: bytes
    image_sha256: str

    def __post_init__(self) -> None:
        if self.name not in APPROVED_PERTURBATIONS:
            raise ValueError("unsupported perturbation name")
        if not self.png_bytes:
            raise ValueError("perturbation image bytes must be non-empty")
        if not _SHA256_RE.fullmatch(self.image_sha256):
            raise ValueError("image_sha256 must be a 64-character hexadecimal SHA-256")
        if hashlib.sha256(self.png_bytes).hexdigest() != self.image_sha256.lower():
            raise ValueError("perturbation image hash does not match image bytes")


@dataclass(frozen=True, slots=True)
class PerturbationRead:
    name: str
    image_sha256: str
    text: str | None
    runtime_healthy: bool

    def __post_init__(self) -> None:
        if self.name not in APPROVED_PERTURBATIONS:
            raise ValueError("unsupported perturbation name")
        if not _SHA256_RE.fullmatch(self.image_sha256):
            raise ValueError("image_sha256 must be a 64-character hexadecimal SHA-256")
        if type(self.runtime_healthy) is not bool:
            raise ValueError("runtime_healthy must be a bool")


@dataclass(frozen=True, slots=True)
class UnitValidation:
    status: UnitStatus
    source_text: str | None
    validator_name: str
    validator_version: str
    error: str | None

    def __post_init__(self) -> None:
        if not self.validator_name.strip():
            raise ValueError("validator_name must be non-empty")
        if not self.validator_version.strip():
            raise ValueError("validator_version must be non-empty")
        if self.status is UnitStatus.VALID and (
            self.source_text is None or not self.source_text.strip()
        ):
            raise ValueError("VALID unit evidence requires source_text")
        if self.status in {UnitStatus.INVALID, UnitStatus.RUNTIME_ERROR} and not self.error:
            raise ValueError(f"{self.status.value} unit evidence requires an error")


@dataclass(frozen=True, slots=True)
class PatientLinkageEvidence:
    expected_present: bool
    observed_count: int
    observed_unique_count: int
    exact_match: bool
    matched_identifier_hmac_sha256: str | None

    def __post_init__(self) -> None:
        if type(self.expected_present) is not bool:
            raise ValueError("expected_present must be a bool")
        if type(self.exact_match) is not bool:
            raise ValueError("exact_match must be a bool")
        if self.observed_count < 0 or self.observed_unique_count < 0:
            raise ValueError("patient-linkage counts must be non-negative")
        if self.observed_unique_count > self.observed_count:
            raise ValueError("observed_unique_count cannot exceed observed_count")
        if self.exact_match:
            if self.matched_identifier_hmac_sha256 is None:
                raise ValueError("exact patient linkage requires an HMAC binding tag")
            if not _SHA256_RE.fullmatch(self.matched_identifier_hmac_sha256):
                raise ValueError("matched_identifier_hmac_sha256 must be SHA-256 hex")
        elif self.matched_identifier_hmac_sha256 is not None:
            raise ValueError("non-matching patient linkage cannot retain an HMAC binding tag")


@dataclass(frozen=True, slots=True)
class VerificationTrace:
    binding: FieldEvidenceInput
    independent_read: CropRead | None
    perturbation_reads: tuple[PerturbationRead, ...]
    unit_validation: UnitValidation
    patient_linkage: PatientLinkageEvidence
    runtime_errors: tuple[str, ...]
    parsed_value: ParsedCriticalValue | None
    signals: VerificationSignals
    evidence_record: EvidenceRecord

    def to_json(self) -> str:
        independent = (
            None
            if self.independent_read is None
            else {
                "crop_sha256": self.independent_read.crop_sha256,
                "engine_name": self.independent_read.engine_name,
                "engine_version": self.independent_read.engine_version,
                "executable": self.independent_read.executable,
                "text": self.independent_read.text,
            }
        )
        parsed = (
            None
            if self.parsed_value is None
            else {
                "comparator": self.parsed_value.comparator,
                "kind": self.parsed_value.kind.value,
                "normalized_text": self.parsed_value.normalized_text,
                "numeric_value": (
                    None
                    if self.parsed_value.numeric_value is None
                    else str(self.parsed_value.numeric_value)
                ),
                "qualitative_token": self.parsed_value.qualitative_token,
            }
        )
        payload = {
            "evidence_record": json.loads(self.evidence_record.to_json()),
            "independent_read": independent,
            "patient_linkage": {
                "exact_match": self.patient_linkage.exact_match,
                "expected_present": self.patient_linkage.expected_present,
                "matched_identifier_hmac_sha256": (
                    self.patient_linkage.matched_identifier_hmac_sha256
                ),
                "observed_count": self.patient_linkage.observed_count,
                "observed_unique_count": self.patient_linkage.observed_unique_count,
            },
            "parsed_value": parsed,
            "perturbation_reads": [
                {
                    "image_sha256": item.image_sha256,
                    "name": item.name,
                    "runtime_healthy": item.runtime_healthy,
                    "text": item.text,
                }
                for item in self.perturbation_reads
            ],
            "runtime_errors": list(self.runtime_errors),
            "unit_validation": {
                "error": self.unit_validation.error,
                "source_text": self.unit_validation.source_text,
                "status": self.unit_validation.status.value,
                "validator_name": self.unit_validation.validator_name,
                "validator_version": self.unit_validation.validator_version,
            },
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def normalize_evidence_text(text: str) -> str:
    """Apply formatting-only normalization without changing clinical characters."""

    return " ".join(unicodedata.normalize("NFC", text).strip().split())


def parse_critical_value(text: str) -> ParsedCriticalValue | None:
    """Parse an explicitly supported critical laboratory value form."""

    normalized = normalize_evidence_text(text)
    numeric_match = _NUMERIC_RE.fullmatch(normalized)
    if numeric_match is not None:
        number = numeric_match.group("number")
        try:
            numeric_value = Decimal(number)
        except InvalidOperation:
            return None
        return ParsedCriticalValue(
            kind=ValueKind.NUMERIC,
            normalized_text=normalized,
            comparator=numeric_match.group("comparator"),
            numeric_value=numeric_value,
        )

    token = normalized.upper()
    if token in _QUALITATIVE_TOKENS:
        return ParsedCriticalValue(
            kind=ValueKind.QUALITATIVE,
            normalized_text=normalized,
            qualitative_token=token,
        )
    return None


def _span_is_member(span: CandidateSpan | None, field: LabFieldCandidate) -> bool:
    return span is not None and span in field.source_spans


def visual_grounding(binding: FieldEvidenceInput) -> bool:
    """Check exact span/crop binding without inferring missing evidence."""

    if not _span_is_member(binding.analyte_span, binding.field):
        return False
    if not _span_is_member(binding.value_span, binding.field):
        return False
    if binding.value_span is None or binding.value_crop is None:
        return False
    if binding.field.unit_text is not None and not _span_is_member(
        binding.unit_span, binding.field
    ):
        return False

    if normalize_evidence_text(binding.field.analyte_text) != normalize_evidence_text(
        cast(CandidateSpan, binding.analyte_span).text
    ):
        return False
    if normalize_evidence_text(binding.field.value_text) != normalize_evidence_text(
        binding.value_span.text
    ):
        return False
    if binding.field.unit_text is not None:
        if binding.unit_span is None:
            return False
        if normalize_evidence_text(binding.field.unit_text) != normalize_evidence_text(
            binding.unit_span.text
        ):
            return False

    if (
        hashlib.sha256(binding.value_crop.png_bytes).hexdigest()
        != binding.value_crop.crop_sha256.lower()
    ):
        return False

    required_spans = [binding.analyte_span, binding.value_span]
    if binding.field.unit_text is not None:
        required_spans.append(binding.unit_span)
    if any(span is None for span in required_spans):
        return False

    pages = {cast(CandidateSpan, span).page for span in required_spans}
    if len(pages) != 1:
        return False
    if binding.value_crop.source_page != binding.value_span.page:
        return False
    return binding.value_crop.requested_box == binding.value_span.box


def _vertical_overlap_ratio(left: BoundingBox, right: BoundingBox) -> float:
    intersection = max(0, min(left.y2, right.y2) - max(left.y1, right.y1))
    shorter = min(left.y2 - left.y1, right.y2 - right.y1)
    return intersection / shorter



def structural_association(binding: FieldEvidenceInput) -> bool:
    """Verify conservative same-page row association for one lab field."""

    if binding.analyte_span is None or binding.value_span is None:
        return False
    spans = [binding.analyte_span, binding.value_span]
    if binding.field.unit_text is not None:
        if binding.unit_span is None:
            return False
        spans.append(binding.unit_span)

    if len({span.page for span in spans}) != 1:
        return False
    if not all(span in binding.field.source_spans for span in spans):
        return False

    for left, right in pairwise(spans):
        if _vertical_overlap_ratio(left.box, right.box) < 0.5:
            return False
        if left.box.x2 > right.box.x1:
            return False
    return True


def _independent_provenance_valid(
    read: CropRead | None,
    source_crop: CriticalCrop | None,
) -> bool:
    return (
        read is not None
        and source_crop is not None
        and read.engine_name == "tesseract"
        and read.crop_sha256.lower() == source_crop.crop_sha256.lower()
    )


def _perturbation_provenance_valid(
    reads: tuple[PerturbationRead, ...],
    source_crop: CriticalCrop | None,
) -> bool:
    if source_crop is None or len(reads) != len(APPROVED_PERTURBATIONS):
        return False
    names = tuple(item.name for item in reads)
    if len(set(names)) != len(names) or set(names) != set(APPROVED_PERTURBATIONS):
        return False
    expected_hashes = {
        item.name: item.image_sha256 for item in make_approved_perturbations(source_crop)
    }
    return all(
        item.image_sha256.lower() == expected_hashes[item.name].lower()
        for item in reads
    )


def independent_agreement(
    primary_text: str,
    read: CropRead | None,
    *,
    expected_crop_sha256: str | None,
) -> bool:
    if read is None or expected_crop_sha256 is None:
        return False
    if read.engine_name != "tesseract":
        return False
    if read.crop_sha256.lower() != expected_crop_sha256.lower():
        return False
    normalized_secondary = normalize_evidence_text(read.text)
    if not normalized_secondary:
        return False
    return normalize_evidence_text(primary_text) == normalized_secondary


def perturbation_stable(
    primary_text: str,
    reads: tuple[PerturbationRead, ...],
    *,
    source_crop: CriticalCrop | None,
) -> bool:
    if not _perturbation_provenance_valid(reads, source_crop):
        return False

    primary = normalize_evidence_text(primary_text)
    for item in reads:
        if not item.runtime_healthy or item.text is None:
            return False
        normalized = normalize_evidence_text(item.text)
        if not normalized or normalized != primary:
            return False
    return True


def _encode_png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=False, compress_level=9)
    return buffer.getvalue()


def _perturbation(name: str, image: Image.Image) -> PerturbationImage:
    png_bytes = _encode_png(image)
    return PerturbationImage(
        name=name,
        png_bytes=png_bytes,
        image_sha256=hashlib.sha256(png_bytes).hexdigest(),
    )


def make_approved_perturbations(crop: CriticalCrop) -> tuple[PerturbationImage, ...]:
    """Create the frozen mild F4 perturbation set deterministically."""

    with Image.open(io.BytesIO(crop.png_bytes)) as opened:
        image = opened.convert("RGB")

    scaled_size = (
        max(1, round(image.width * 1.10)),
        max(1, round(image.height * 1.10)),
    )
    return (
        _perturbation("brightness_095", ImageEnhance.Brightness(image).enhance(0.95)),
        _perturbation("brightness_105", ImageEnhance.Brightness(image).enhance(1.05)),
        _perturbation("contrast_105", ImageEnhance.Contrast(image).enhance(1.05)),
        _perturbation("scale_110", image.resize(scaled_size, Image.Resampling.LANCZOS)),
    )


def _load_ucum() -> tuple[Callable[[str], object], type[Exception], str]:
    module = importlib.import_module("ucumvert")
    parser = cast(Callable[[str], object], module.parse_ucum)
    invalid_error = cast(type[Exception], module.InvalidUcumError)
    version = importlib.metadata.version("ucumvert")
    return parser, invalid_error, version


def validate_ucum_unit(
    source_text: str | None,
    *,
    parser: Callable[[str], object] | None = None,
    validator_version: str | None = None,
) -> UnitValidation:
    """Validate the exact case-sensitive UCUM source code without rewriting it."""

    if source_text is None or not normalize_evidence_text(source_text):
        return UnitValidation(
            status=UnitStatus.MISSING,
            source_text=source_text,
            validator_name="ucumvert",
            validator_version=validator_version or importlib.metadata.version("ucumvert"),
            error=None,
        )

    normalized = normalize_evidence_text(source_text)
    if parser is None:
        active_parser, invalid_error, resolved_version = _load_ucum()
    else:
        active_parser = parser
        invalid_error = None
        resolved_version = validator_version or "injected"

    try:
        active_parser(normalized)
    except Exception as exc:  # adapter boundary: distinguish invalid input from runtime failure
        if invalid_error is not None and isinstance(exc, invalid_error):
            return UnitValidation(
                status=UnitStatus.INVALID,
                source_text=normalized,
                validator_name="ucumvert",
                validator_version=resolved_version,
                error=str(exc) or type(exc).__name__,
            )
        return UnitValidation(
            status=UnitStatus.RUNTIME_ERROR,
            source_text=normalized,
            validator_name="ucumvert",
            validator_version=resolved_version,
            error=f"{type(exc).__name__}: {exc}",
        )

    return UnitValidation(
        status=UnitStatus.VALID,
        source_text=normalized,
        validator_name="ucumvert",
        validator_version=resolved_version,
        error=None,
    )


_PATIENT_BINDING_DOMAIN: Final[bytes] = b"safeocr.patient-id.v1\0"


def _require_patient_binding_key(key: bytes) -> bytes:
    if key.__class__ is not bytes:
        raise ValueError("patient_binding_key must be bytes")
    if len(key) < 32:
        raise ValueError("patient_binding_key must be at least 32 bytes")
    return key


def patient_binding_hmac(identifier: str, key: bytes) -> str:
    """Return a keyed, domain-separated binding tag for a normalized identifier."""

    active_key = _require_patient_binding_key(key)
    normalized = normalize_evidence_text(identifier)
    if not normalized:
        raise ValueError("patient identifier must be non-empty")
    message = _PATIENT_BINDING_DOMAIN + normalized.encode("utf-8")
    return hmac.new(active_key, message, hashlib.sha256).hexdigest()


def patient_binding_matches(identifier: str, key: bytes, expected_tag: str) -> bool:
    """Verify a caller-supplied identifier against an F4 binding tag."""

    if not _SHA256_RE.fullmatch(expected_tag):
        return False
    candidate = patient_binding_hmac(identifier, key)
    return hmac.compare_digest(candidate, expected_tag.lower())


def _patient_linkage_evidence(
    expected_id: str | None,
    observed_ids: tuple[str, ...],
    *,
    patient_binding_key: bytes,
) -> PatientLinkageEvidence:
    expected = (
        "" if expected_id is None else normalize_evidence_text(expected_id)
    )
    normalized_observed = tuple(
        normalize_evidence_text(value)
        for value in observed_ids
        if normalize_evidence_text(value)
    )
    unique_observed = set(normalized_observed)
    exact_match = (
        bool(expected)
        and len(unique_observed) == 1
        and next(iter(unique_observed)) == expected
    )
    _require_patient_binding_key(patient_binding_key)
    matched_tag = (
        patient_binding_hmac(expected, patient_binding_key) if exact_match else None
    )
    return PatientLinkageEvidence(
        expected_present=bool(expected),
        observed_count=len(normalized_observed),
        observed_unique_count=len(unique_observed),
        exact_match=exact_match,
        matched_identifier_hmac_sha256=matched_tag,
    )


def patient_linkage_unambiguous(
    expected_id: str | None,
    observed_ids: tuple[str, ...],
) -> bool:
    expected = "" if expected_id is None else normalize_evidence_text(expected_id)
    normalized_observed = tuple(
        normalize_evidence_text(value)
        for value in observed_ids
        if normalize_evidence_text(value)
    )
    unique_observed = set(normalized_observed)
    return (
        bool(expected)
        and len(unique_observed) == 1
        and next(iter(unique_observed)) == expected
    )


def _unit_matches_field(field: LabFieldCandidate, unit: UnitValidation) -> bool:
    if field.unit_text is None or unit.source_text is None:
        return False
    return (
        unit.status is UnitStatus.VALID
        and normalize_evidence_text(field.unit_text)
        == normalize_evidence_text(unit.source_text)
    )


def derive_verification_trace(
    *,
    binding: FieldEvidenceInput,
    independent_read: CropRead | None,
    perturbation_reads: tuple[PerturbationRead, ...],
    unit_validation: UnitValidation,
    expected_patient_id: str | None,
    observed_patient_ids: tuple[str, ...],
    patient_binding_key: bytes,
    runtime_errors: tuple[str, ...],
    policy_version: str,
) -> VerificationTrace:
    """Derive fail-closed F4 signals and the canonical F1 EvidenceRecord."""

    parsed = parse_critical_value(binding.field.value_text)
    perturbation_ok = perturbation_stable(
        binding.field.value_text,
        perturbation_reads,
        source_crop=binding.value_crop,
    )
    independent_provenance_ok = _independent_provenance_valid(
        independent_read, binding.value_crop
    )
    perturbation_provenance_ok = _perturbation_provenance_valid(
        perturbation_reads, binding.value_crop
    )
    runtime_healthy = (
        independent_provenance_ok
        and perturbation_provenance_ok
        and not runtime_errors
        and all(item.runtime_healthy for item in perturbation_reads)
        and unit_validation.status is not UnitStatus.RUNTIME_ERROR
    )
    patient_linkage = _patient_linkage_evidence(
        expected_patient_id,
        observed_patient_ids,
        patient_binding_key=patient_binding_key,
    )
    signals = VerificationSignals(
        candidate_present=bool(normalize_evidence_text(binding.field.value_text)),
        visual_grounded=visual_grounding(binding),
        independent_agreement=independent_agreement(
            binding.field.value_text,
            independent_read,
            expected_crop_sha256=(
                None if binding.value_crop is None else binding.value_crop.crop_sha256
            ),
        ),
        perturbation_stable=perturbation_ok,
        structural_association=structural_association(binding),
        numeric_parse_unambiguous=parsed is not None,
        unit_valid=_unit_matches_field(binding.field, unit_validation),
        patient_linkage_unambiguous=patient_linkage.exact_match,
        runtime_healthy=runtime_healthy,
    )
    decision = decide(signals, criticality=binding.field.criticality)
    record = EvidenceRecord(
        field=binding.field,
        signals=signals,
        decision=decision,
        policy_version=policy_version,
    )
    return VerificationTrace(
        binding=binding,
        independent_read=independent_read,
        perturbation_reads=perturbation_reads,
        unit_validation=unit_validation,
        patient_linkage=patient_linkage,
        runtime_errors=runtime_errors,
        parsed_value=parsed,
        signals=signals,
        evidence_record=record,
    )
