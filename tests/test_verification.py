from __future__ import annotations

import hashlib
import hmac
import io
import json
from decimal import Decimal
from typing import Any, cast

import pytest
from PIL import Image

from safeocr.contracts import (
    BoundingBox,
    CandidateSpan,
    Criticality,
    DecisionState,
    LabFieldCandidate,
    PageAsset,
)
from safeocr.ocr import CriticalCrop, CropRead
from safeocr.verification import (
    APPROVED_PERTURBATIONS,
    FieldEvidenceInput,
    PerturbationRead,
    UnitStatus,
    UnitValidation,
    ValueKind,
    derive_verification_trace,
    make_approved_perturbations,
    normalize_evidence_text,
    parse_critical_value,
    patient_binding_hmac,
    patient_linkage_unambiguous,
    structural_association,
    validate_ucum_unit,
    visual_grounding,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
PATIENT_BINDING_KEY = bytes.fromhex("11" * 32)


def _page(*, document_sha: str = SHA_A, page_index: int = 0) -> PageAsset:
    return PageAsset(document_sha, page_index, 1000, 760, SHA_B)


def _crop_png() -> bytes:
    image = Image.new("RGB", (42, 27), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _span(
    text: str,
    box: BoundingBox,
    *,
    page: PageAsset | None = None,
) -> CandidateSpan:
    return CandidateSpan(
        page=page or _page(),
        box=box,
        text=text,
        engine_name="paddleocr",
        engine_version="3.7.0",
        confidence=0.99,
    )


def _binding(
    *,
    value_text: str = "3.4",
    unit_text: str | None = "mmol/L",
    page: PageAsset | None = None,
) -> FieldEvidenceInput:
    source_page = page or _page()
    analyte = _span("Potassium", BoundingBox(40, 285, 133, 301), page=source_page)
    value = _span(value_text, BoundingBox(330, 286, 360, 301), page=source_page)
    unit = (
        _span(unit_text, BoundingBox(480, 285, 550, 301), page=source_page)
        if unit_text is not None
        else None
    )
    spans = (analyte, value) if unit is None else (analyte, value, unit)
    field = LabFieldCandidate(
        analyte_text="Potassium",
        value_text=value_text,
        unit_text=unit_text,
        criticality=Criticality.CRITICAL,
        source_spans=spans,
    )
    crop_bytes = _crop_png()
    crop = CriticalCrop(
        source_page=source_page,
        requested_box=value.box,
        crop_box=BoundingBox(324, 280, 366, 307),
        png_bytes=crop_bytes,
        crop_sha256=hashlib.sha256(crop_bytes).hexdigest(),
    )
    return FieldEvidenceInput(
        field=field,
        analyte_span=analyte,
        value_span=value,
        unit_span=unit,
        value_crop=crop,
    )


def _unit(status: UnitStatus = UnitStatus.VALID) -> UnitValidation:
    return UnitValidation(
        status=status,
        source_text="mmol/L",
        validator_name="ucumvert",
        validator_version="0.3.2",
        error=None if status is UnitStatus.VALID else "unit issue",
    )


def _perturbations(
    binding: FieldEvidenceInput,
    text: str = "3.4",
) -> tuple[PerturbationRead, ...]:
    assert binding.value_crop is not None
    return tuple(
        PerturbationRead(
            name=image.name,
            image_sha256=image.image_sha256,
            text=text,
            runtime_healthy=True,
        )
        for image in make_approved_perturbations(binding.value_crop)
    )


def _trace(
    *,
    binding: FieldEvidenceInput | None = None,
    independent_text: str | None = "3.4",
    perturbation_text: str = "3.4",
    unit: UnitValidation | None = None,
    expected_patient_id: str | None = "SAFE-69904705",
    observed_patient_ids: tuple[str, ...] = ("SAFE-69904705",),
    runtime_errors: tuple[str, ...] = (),
):
    active_binding = binding or _binding()
    crop = active_binding.value_crop
    independent = (
        CropRead(
            text=independent_text,
            engine_name="tesseract",
            engine_version="5.4-test",
            executable="tesseract",
            crop_sha256=crop.crop_sha256,
        )
        if independent_text is not None and crop is not None
        else None
    )
    perturbations = (
        _perturbations(active_binding, perturbation_text) if crop is not None else ()
    )
    return derive_verification_trace(
        binding=active_binding,
        independent_read=independent,
        perturbation_reads=perturbations,
        unit_validation=unit or _unit(),
        expected_patient_id=expected_patient_id,
        observed_patient_ids=observed_patient_ids,
        patient_binding_key=PATIENT_BINDING_KEY,
        runtime_errors=runtime_errors,
        policy_version="f4-v1",
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  3.4  ", "3.4"),
        ("NOT   DETECTED", "NOT DETECTED"),
        ("6.B", "6.B"),
        ("3,4", "3,4"),
        ("mmol/l", "mmol/l"),
        ("Ä", "Ä"),
    ],
)
def test_normalize_evidence_text_is_formatting_only(raw: str, expected: str) -> None:
    assert normalize_evidence_text(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected_comparator", "expected_value"),
    [
        ("3.4", None, Decimal("3.4")),
        ("-2.1", None, Decimal("-2.1")),
        ("<0.01", "<", Decimal("0.01")),
        (">=200", ">=", Decimal("200")),
        ("1.2e3", None, Decimal("1.2e3")),
    ],
)
def test_numeric_parser_accepts_frozen_grammar(
    raw: str, expected_comparator: str | None, expected_value: Decimal
) -> None:
    parsed = parse_critical_value(raw)
    assert parsed is not None
    assert parsed.kind is ValueKind.NUMERIC
    assert parsed.comparator == expected_comparator
    assert parsed.numeric_value == expected_value


@pytest.mark.parametrize("raw", ["3,4", "3..4", "approx 3.4", "3.4 mg/dL", "O.5"])
def test_numeric_parser_rejects_ambiguous_forms(raw: str) -> None:
    assert parse_critical_value(raw) is None


@pytest.mark.parametrize(
    "raw",
    ["POSITIVE", "NEGATIVE", "DETECTED", "NOT DETECTED", "REACTIVE", "NONREACTIVE", "NON-REACTIVE"],
)
def test_qualitative_parser_accepts_only_frozen_tokens(raw: str) -> None:
    parsed = parse_critical_value(raw)
    assert parsed is not None
    assert parsed.kind is ValueKind.QUALITATIVE
    assert parsed.qualitative_token == raw


def test_unknown_qualitative_token_is_rejected() -> None:
    assert parse_critical_value("INDETERMINATE") is None


def test_visual_grounding_accepts_exact_bound_evidence() -> None:
    assert visual_grounding(_binding()) is True


def test_visual_grounding_rejects_crop_box_mismatch() -> None:
    binding = _binding()
    assert binding.value_crop is not None
    bad_crop = CriticalCrop(
        source_page=binding.value_crop.source_page,
        requested_box=BoundingBox(331, 286, 360, 301),
        crop_box=binding.value_crop.crop_box,
        png_bytes=b"png",
        crop_sha256=binding.value_crop.crop_sha256,
    )
    bad = FieldEvidenceInput(
        field=binding.field,
        analyte_span=binding.analyte_span,
        value_span=binding.value_span,
        unit_span=binding.unit_span,
        value_crop=bad_crop,
    )
    assert visual_grounding(bad) is False




def test_visual_grounding_rejects_field_text_not_bound_to_span_text() -> None:
    binding = _binding()
    assert binding.analyte_span is not None
    assert binding.value_span is not None
    assert binding.unit_span is not None
    field = LabFieldCandidate(
        analyte_text="Potassium",
        value_text="3.8",
        unit_text="mmol/L",
        criticality=Criticality.CRITICAL,
        source_spans=(binding.analyte_span, binding.value_span, binding.unit_span),
    )
    bad = FieldEvidenceInput(
        field=field,
        analyte_span=binding.analyte_span,
        value_span=binding.value_span,
        unit_span=binding.unit_span,
        value_crop=binding.value_crop,
    )
    assert visual_grounding(bad) is False


def test_visual_grounding_rejects_tampered_crop_hash() -> None:
    binding = _binding()
    assert binding.value_crop is not None
    bad_crop = CriticalCrop(
        source_page=binding.value_crop.source_page,
        requested_box=binding.value_crop.requested_box,
        crop_box=binding.value_crop.crop_box,
        png_bytes=binding.value_crop.png_bytes + b"tamper",
        crop_sha256=binding.value_crop.crop_sha256,
    )
    bad = FieldEvidenceInput(
        field=binding.field,
        analyte_span=binding.analyte_span,
        value_span=binding.value_span,
        unit_span=binding.unit_span,
        value_crop=bad_crop,
    )
    assert visual_grounding(bad) is False

def test_visual_grounding_requires_unit_span_when_field_has_unit() -> None:
    binding = _binding()
    bad = FieldEvidenceInput(
        field=binding.field,
        analyte_span=binding.analyte_span,
        value_span=binding.value_span,
        unit_span=None,
        value_crop=binding.value_crop,
    )
    assert visual_grounding(bad) is False


def test_structural_association_accepts_same_row_order() -> None:
    assert structural_association(_binding()) is True


def test_structural_association_rejects_wrong_column_order() -> None:
    binding = _binding()
    assert binding.analyte_span is not None
    assert binding.unit_span is not None
    bad_value = _span("3.4", BoundingBox(10, 286, 35, 301))
    field = LabFieldCandidate(
        analyte_text="Potassium",
        value_text="3.4",
        unit_text="mmol/L",
        criticality=Criticality.CRITICAL,
        source_spans=(binding.analyte_span, bad_value, binding.unit_span),
    )
    bad = FieldEvidenceInput(
        field=field,
        analyte_span=binding.analyte_span,
        value_span=bad_value,
        unit_span=binding.unit_span,
        value_crop=CriticalCrop(
            source_page=bad_value.page,
            requested_box=bad_value.box,
            crop_box=bad_value.box,
            png_bytes=b"x",
            crop_sha256=hashlib.sha256(b"x").hexdigest(),
        ),
    )
    assert structural_association(bad) is False


def test_structural_association_rejects_multi_page_evidence() -> None:
    page2 = _page(page_index=1)
    binding = _binding()
    assert binding.analyte_span is not None
    assert binding.value_span is not None
    assert binding.value_crop is not None
    unit = _span("mmol/L", BoundingBox(480, 285, 550, 301), page=page2)
    field = LabFieldCandidate(
        analyte_text="Potassium",
        value_text="3.4",
        unit_text="mmol/L",
        criticality=Criticality.CRITICAL,
        source_spans=(binding.analyte_span, binding.value_span, unit),
    )
    bad = FieldEvidenceInput(
        field=field,
        analyte_span=binding.analyte_span,
        value_span=binding.value_span,
        unit_span=unit,
        value_crop=binding.value_crop,
    )
    assert structural_association(bad) is False


def test_structural_association_rejects_overlapping_columns() -> None:
    binding = _binding()
    assert binding.analyte_span is not None
    assert binding.unit_span is not None
    crop_bytes = _crop_png()
    overlapping_value = _span("3.4", BoundingBox(120, 286, 170, 301))
    field = LabFieldCandidate(
        analyte_text="Potassium",
        value_text="3.4",
        unit_text="mmol/L",
        criticality=Criticality.CRITICAL,
        source_spans=(binding.analyte_span, overlapping_value, binding.unit_span),
    )
    bad = FieldEvidenceInput(
        field=field,
        analyte_span=binding.analyte_span,
        value_span=overlapping_value,
        unit_span=binding.unit_span,
        value_crop=CriticalCrop(
            source_page=overlapping_value.page,
            requested_box=overlapping_value.box,
            crop_box=overlapping_value.box,
            png_bytes=crop_bytes,
            crop_sha256=hashlib.sha256(crop_bytes).hexdigest(),
        ),
    )
    assert structural_association(bad) is False


def test_non_tesseract_independent_read_abstains() -> None:
    binding = _binding()
    assert binding.value_crop is not None
    trace = derive_verification_trace(
        binding=binding,
        independent_read=CropRead(
            text="3.4",
            engine_name="paddleocr",
            engine_version="3.7.0",
            executable="same-family",
            crop_sha256=binding.value_crop.crop_sha256,
        ),
        perturbation_reads=_perturbations(binding),
        unit_validation=_unit(),
        expected_patient_id="SAFE-69904705",
        observed_patient_ids=("SAFE-69904705",),
        patient_binding_key=PATIENT_BINDING_KEY,
        runtime_errors=(),
        policy_version="f4-v1",
    )
    assert trace.signals.independent_agreement is False
    assert trace.signals.runtime_healthy is False
    assert trace.evidence_record.decision.state is DecisionState.ABSTAINED


def test_patient_linkage_requires_one_exact_identifier() -> None:
    assert patient_linkage_unambiguous("SAFE-1", ("SAFE-1", "SAFE-1")) is True
    assert patient_linkage_unambiguous("SAFE-1", ("safe-1",)) is False
    assert patient_linkage_unambiguous("SAFE-1", ("SAFE-1", "SAFE-2")) is False
    assert patient_linkage_unambiguous(None, ("SAFE-1",)) is False
    assert patient_linkage_unambiguous("SAFE-1", ()) is False


def test_ucum_valid_unit_is_accepted_without_rewrite() -> None:
    result = validate_ucum_unit("mmol/L")
    assert result.status is UnitStatus.VALID
    assert result.source_text == "mmol/L"
    assert result.validator_version == "0.3.2"


def test_ucum_invalid_unit_is_rejected() -> None:
    result = validate_ucum_unit("not a unit")
    assert result.status is UnitStatus.INVALID
    assert result.source_text == "not a unit"


def test_ucum_missing_unit_is_fail_closed() -> None:
    result = validate_ucum_unit(None)
    assert result.status is UnitStatus.MISSING


def test_ucum_unexpected_failure_is_runtime_error() -> None:
    def explode(_: str) -> object:
        raise RuntimeError("boom")

    result = validate_ucum_unit("mmol/L", parser=explode, validator_version="test")
    assert result.status is UnitStatus.RUNTIME_ERROR
    assert result.error is not None


def test_approved_perturbation_images_are_deterministic() -> None:
    image = Image.new("RGB", (40, 20), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    crop = CriticalCrop(
        source_page=_page(),
        requested_box=BoundingBox(10, 10, 30, 20),
        crop_box=BoundingBox(8, 8, 32, 22),
        png_bytes=buffer.getvalue(),
        crop_sha256=hashlib.sha256(buffer.getvalue()).hexdigest(),
    )

    first = make_approved_perturbations(crop)
    second = make_approved_perturbations(crop)

    assert tuple(item.name for item in first) == APPROVED_PERTURBATIONS
    assert [item.image_sha256 for item in first] == [item.image_sha256 for item in second]






def test_independent_read_from_different_crop_cannot_agree() -> None:
    binding = _binding()
    assert binding.value_crop is not None
    trace = derive_verification_trace(
        binding=binding,
        independent_read=CropRead(
            text="3.4",
            engine_name="tesseract",
            engine_version="5.4-test",
            executable="tesseract",
            crop_sha256="e" * 64,
        ),
        perturbation_reads=_perturbations(binding),
        unit_validation=_unit(),
        expected_patient_id="SAFE-69904705",
        observed_patient_ids=("SAFE-69904705",),
        patient_binding_key=PATIENT_BINDING_KEY,
        runtime_errors=(),
        policy_version="f4-v1",
    )
    assert trace.signals.independent_agreement is False
    assert trace.signals.runtime_healthy is False
    assert trace.evidence_record.decision.state is DecisionState.ABSTAINED
    assert trace.evidence_record.decision.failed_gates == ("runtime_healthy",)

def test_tampered_perturbation_hash_prevents_stability() -> None:
    binding = _binding()
    reads = list(_perturbations(binding))
    first = reads[0]
    reads[0] = PerturbationRead(
        name=first.name,
        image_sha256="f" * 64,
        text=first.text,
        runtime_healthy=True,
    )
    trace = derive_verification_trace(
        binding=binding,
        independent_read=CropRead(
            text="3.4",
            engine_name="tesseract",
            engine_version="5.4-test",
            executable="tesseract",
            crop_sha256=cast(CriticalCrop, binding.value_crop).crop_sha256,
        ),
        perturbation_reads=tuple(reads),
        unit_validation=_unit(),
        expected_patient_id="SAFE-69904705",
        observed_patient_ids=("SAFE-69904705",),
        patient_binding_key=PATIENT_BINDING_KEY,
        runtime_errors=(),
        policy_version="f4-v1",
    )
    assert trace.signals.perturbation_stable is False
    assert trace.signals.runtime_healthy is False
    assert trace.evidence_record.decision.state is DecisionState.ABSTAINED
    assert trace.evidence_record.decision.failed_gates == ("runtime_healthy",)

def test_all_mandatory_evidence_produces_verified_auto() -> None:
    trace = _trace()
    assert trace.signals.independent_agreement is True
    assert trace.signals.perturbation_stable is True
    assert trace.signals.structural_association is True
    assert trace.signals.numeric_parse_unambiguous is True
    assert trace.signals.unit_valid is True
    assert trace.signals.patient_linkage_unambiguous is True
    assert trace.signals.runtime_healthy is True
    assert trace.evidence_record.decision.state is DecisionState.VERIFIED_AUTO


@pytest.mark.parametrize(
    ("override", "expected_gate"),
    [
        ({"independent_text": "3.8"}, "independent_agreement"),
        ({"perturbation_text": "3.8"}, "perturbation_stable"),
        ({"unit": _unit(UnitStatus.INVALID)}, "unit_valid"),
        ({"observed_patient_ids": ("SAFE-OTHER",)}, "patient_linkage_unambiguous"),
    ],
)
def test_verification_failures_route_to_review(
    override: dict[str, Any], expected_gate: str
) -> None:
    trace = _trace(**override)
    assert trace.evidence_record.decision.state is DecisionState.REVIEW_REQUIRED
    assert expected_gate in trace.evidence_record.decision.failed_gates


def test_missing_grounding_routes_to_abstain() -> None:
    binding = _binding()
    bad = FieldEvidenceInput(
        field=binding.field,
        analyte_span=binding.analyte_span,
        value_span=None,
        unit_span=binding.unit_span,
        value_crop=None,
    )
    trace = _trace(binding=bad)
    assert trace.evidence_record.decision.state is DecisionState.ABSTAINED
    assert trace.evidence_record.decision.failed_gates == ("visual_grounded",)


def test_runtime_failure_routes_to_abstain() -> None:
    trace = _trace(runtime_errors=("tesseract_timeout",))
    assert trace.evidence_record.decision.state is DecisionState.ABSTAINED
    assert trace.evidence_record.decision.failed_gates == ("runtime_healthy",)


def test_missing_independent_read_is_runtime_failure_not_agreement() -> None:
    trace = _trace(independent_text=None)
    assert trace.signals.independent_agreement is False
    assert trace.signals.runtime_healthy is False
    assert trace.evidence_record.decision.state is DecisionState.ABSTAINED


def test_verification_trace_serialization_is_deterministic() -> None:
    trace = _trace()
    assert trace.to_json() == trace.to_json()


def test_trace_serialization_does_not_expose_patient_identifier() -> None:
    trace = _trace()
    assert not hasattr(trace, "expected_patient_id")
    assert not hasattr(trace, "observed_patient_ids")
    serialized = trace.to_json()
    assert "SAFE-69904705" not in serialized
    payload = json.loads(serialized)
    assert payload["patient_linkage"] == {
        "exact_match": True,
        "expected_present": True,
        "matched_identifier_hmac_sha256": hmac.new(
            PATIENT_BINDING_KEY,
            b"safeocr.patient-id.v1\0SAFE-69904705",
            hashlib.sha256,
        ).hexdigest(),
        "observed_count": 1,
        "observed_unique_count": 1,
    }


def test_patient_linkage_digest_is_absent_when_not_exact() -> None:
    trace = _trace(observed_patient_ids=("SAFE-OTHER",))
    payload = json.loads(trace.to_json())
    assert payload["patient_linkage"]["matched_identifier_hmac_sha256"] is None


def test_patient_binding_hmac_is_deterministic_and_domain_separated() -> None:
    expected = hmac.new(
        PATIENT_BINDING_KEY,
        b"safeocr.patient-id.v1\0SAFE-69904705",
        hashlib.sha256,
    ).hexdigest()
    assert patient_binding_hmac("SAFE-69904705", PATIENT_BINDING_KEY) == expected
    assert patient_binding_hmac(" SAFE-69904705 ", PATIENT_BINDING_KEY) == expected


def test_patient_binding_hmac_rejects_short_key() -> None:
    with pytest.raises(ValueError):
        patient_binding_hmac("SAFE-69904705", b"too-short")
