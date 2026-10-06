from __future__ import annotations

from safeocr.contracts import BoundingBox, CandidateSpan, PageAsset
from safeocr.evaluation import (
    EvaluationMethod,
    EvaluationRole,
    FieldTruth,
    ParsedLabGoldRow,
    aggregate_metrics,
    parse_labgold_rows,
    score_labgold_associations,
)
from safeocr.ocr import EngineFingerprint, PageOcrResult


def _page() -> PageAsset:
    return PageAsset(
        document_sha256="a" * 64,
        page_index=0,
        width_px=1000,
        height_px=760,
        page_sha256="b" * 64,
    )


def _span(page: PageAsset, x: int, y: int, text: str) -> CandidateSpan:
    return CandidateSpan(
        page=page,
        box=BoundingBox(x, y, x + 90, y + 24),
        text=text,
        engine_name="paddleocr",
        engine_version="3.7.0",
        confidence=0.95,
    )


def _result(spans: tuple[CandidateSpan, ...]) -> PageOcrResult:
    return PageOcrResult(
        page=_page(),
        fingerprint=EngineFingerprint(
            engine_name="paddleocr",
            engine_version="3.7.0",
            model_name="test",
            backend="test",
        ),
        spans=spans,
    )


def _truths() -> tuple[FieldTruth, ...]:
    return (
        FieldTruth(
            case_id="doc:row-01",
            patient_id="SAFE-00000001",
            document_id="doc",
            row_id="row-01",
            analyte_text="Potassium",
            value_text="3.4",
            unit_text="mmol/L",
        ),
        FieldTruth(
            case_id="doc:row-02",
            patient_id="SAFE-00000001",
            document_id="doc",
            row_id="row-02",
            analyte_text="Sodium",
            value_text="139",
            unit_text="mmol/L",
        ),
    )


def test_parse_labgold_rows_uses_ocr_geometry_and_ignores_headers() -> None:
    page = _page()
    spans = (
        _span(page, 40, 220, "Test"),
        _span(page, 330, 220, "Result"),
        _span(page, 480, 220, "Units"),
        _span(page, 40, 285, "Potassium"),
        _span(page, 330, 286, "8.4"),
        _span(page, 480, 285, "mmol/L"),
        _span(page, 40, 343, "Sodium"),
        _span(page, 330, 344, "139"),
        _span(page, 480, 343, "mmol/L"),
    )
    parsed = parse_labgold_rows(_result(spans))

    assert len(parsed) == 2
    assert parsed[0].ordinal == 1
    assert parsed[0].analyte_text == "Potassium"
    assert parsed[0].value_text == "8.4"
    assert parsed[1].analyte_text == "Sodium"


def test_association_scorer_flags_cross_row_value_without_truth_guided_parsing() -> None:
    rows = (
        ParsedLabGoldRow(
            ordinal=1,
            analyte_text="Potassium",
            value_text="139",
            unit_text="mmol/L",
            y_center=300.0,
        ),
        ParsedLabGoldRow(
            ordinal=2,
            analyte_text="Sodium",
            value_text="3.4",
            unit_text="mmol/L",
            y_center=358.0,
        ),
    )
    scored = score_labgold_associations(_truths(), rows)

    assert scored[0].table_association_error is True
    assert scored[1].table_association_error is True
    metrics = aggregate_metrics(scored)
    assert metrics.table_linked_accepted_count == 2
    assert metrics.table_association_error_rate == 1.0


def test_association_scorer_does_not_mislabel_ocr_error_as_association_error() -> None:
    rows = (
        ParsedLabGoldRow(
            ordinal=1,
            analyte_text="Potassium",
            value_text="3X4",
            unit_text="mmol/L",
            y_center=300.0,
        ),
    )
    scored = score_labgold_associations(_truths(), rows)

    assert scored[0].unsafe_accepted is True
    assert scored[0].table_association_error is None
    assert scored[1].accepted is False
    assert scored[1].table_association_error is None


def test_association_scorer_preserves_method_and_role() -> None:
    rows = (
        ParsedLabGoldRow(
            ordinal=1,
            analyte_text="Potassium",
            value_text="3.4",
            unit_text="mmol/L",
            y_center=300.0,
        ),
        ParsedLabGoldRow(
            ordinal=2,
            analyte_text="Sodium",
            value_text="139",
            unit_text="mmol/L",
            y_center=358.0,
        ),
    )
    scored = score_labgold_associations(
        _truths(),
        rows,
        method=EvaluationMethod.SAFEOCR,
        role=EvaluationRole.CALIBRATION,
    )

    assert all(item.method is EvaluationMethod.SAFEOCR for item in scored)
    assert all(item.role is EvaluationRole.CALIBRATION for item in scored)
    assert all(item.table_association_error is False for item in scored)


def test_association_scorer_rejects_spurious_extra_rows() -> None:
    rows = (
        ParsedLabGoldRow(1, "Potassium", "3.4", "mmol/L", 300.0),
        ParsedLabGoldRow(2, "Sodium", "139", "mmol/L", 358.0),
        ParsedLabGoldRow(3, "Glucose", "104", "mg/dL", 416.0),
    )
    import pytest

    with pytest.raises(ValueError, match="exceeds truth row count"):
        score_labgold_associations(_truths(), rows)
