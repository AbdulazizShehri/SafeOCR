from __future__ import annotations

import hashlib

import pytest

from safeocr.contracts import BoundingBox, CandidateSpan, DecisionState, PageAsset
from safeocr.evaluation import (
    EvaluationMethod,
    EvaluationRole,
    FieldPrediction,
    FieldTruth,
    LabGoldCasePlan,
    aggregate_metrics,
    evaluate_field,
    frozen_labgold_split,
    labgold_split_manifest_json,
    match_span_to_truth_region,
    naive_agreement_prediction,
    primary_ocr_prediction,
    require_calibration_only,
    risk_coverage_point,
    tesseract_crop_prediction,
    validate_labgold_split,
    wilson_interval,
)
from safeocr.labgold import TruthRegion
from safeocr.ocr import EngineFingerprint, PageOcrResult


def _truth(case_id: str = "c1") -> FieldTruth:
    return FieldTruth(
        case_id=case_id,
        patient_id="SAFE-00000001",
        document_id="doc-1",
        row_id="row-01",
        analyte_text="Potassium",
        value_text="3.4",
        unit_text="mmol/L",
    )


def _prediction(
    *,
    case_id: str = "c1",
    method: EvaluationMethod = EvaluationMethod.SAFEOCR,
    decision: DecisionState = DecisionState.VERIFIED_AUTO,
    analyte_text: str = "Potassium",
    value_text: str = "3.4",
    unit_text: str = "mmol/L",
    patient_id: str = "SAFE-00000001",
    row_id: str = "row-01",
    fhir_mapping_correct: bool | None = True,
) -> FieldPrediction:
    return FieldPrediction(
        case_id=case_id,
        method=method,
        role=EvaluationRole.EVALUATION,
        decision=decision,
        analyte_text=analyte_text,
        value_text=value_text,
        unit_text=unit_text,
        patient_id=patient_id,
        row_id=row_id,
        fhir_mapping_correct=fhir_mapping_correct,
    )


def test_exact_field_evaluation_is_fail_closed() -> None:
    exact = evaluate_field(_truth(), _prediction())
    assert exact.exact_correct is True
    assert exact.accepted is True
    assert exact.unsafe_accepted is False

    wrong = evaluate_field(_truth(), _prediction(value_text="8.4"))
    assert wrong.exact_correct is False
    assert wrong.accepted is True
    assert wrong.unsafe_accepted is True


def test_review_and_abstain_are_not_counted_as_accepted() -> None:
    review = evaluate_field(
        _truth(),
        _prediction(decision=DecisionState.REVIEW_REQUIRED, fhir_mapping_correct=None),
    )
    abstain = evaluate_field(
        _truth("c2"),
        _prediction(
            case_id="c2",
            decision=DecisionState.ABSTAINED,
            fhir_mapping_correct=None,
        ),
    )

    metrics = aggregate_metrics((review, abstain))
    assert metrics.evaluable_count == 2
    assert metrics.accepted_count == 0
    assert metrics.unsafe_accept_rate is None
    assert metrics.verified_coverage == 0.0
    assert metrics.review_rate == 0.5
    assert metrics.abstention_rate == 0.5


def test_headline_metrics_count_accepted_errors_with_correct_denominators() -> None:
    rows = (
        evaluate_field(_truth("c1"), _prediction(case_id="c1")),
        evaluate_field(_truth("c2"), _prediction(case_id="c2", value_text="9.9")),
        evaluate_field(
            _truth("c3"),
            _prediction(
                case_id="c3",
                decision=DecisionState.REVIEW_REQUIRED,
                fhir_mapping_correct=None,
            ),
        ),
        evaluate_field(
            _truth("c4"),
            _prediction(
                case_id="c4",
                decision=DecisionState.ABSTAINED,
                fhir_mapping_correct=None,
            ),
        ),
    )
    metrics = aggregate_metrics(rows)

    assert metrics.evaluable_count == 4
    assert metrics.exact_correct_count == 3
    assert metrics.critical_field_exact_accuracy == 0.75
    assert metrics.accepted_count == 2
    assert metrics.unsafe_accepted_count == 1
    assert metrics.unsafe_accept_rate == 0.5
    assert metrics.verified_coverage == 0.5
    assert metrics.review_rate == 0.25
    assert metrics.abstention_rate == 0.25


def test_patient_table_and_fhir_error_rates_use_accepted_denominators() -> None:
    bad = evaluate_field(
        _truth(),
        _prediction(
            patient_id="SAFE-WRONG",
            row_id="row-02",
            fhir_mapping_correct=False,
        ),
    )
    metrics = aggregate_metrics((bad,))
    assert metrics.patient_attribution_error_rate == 1.0
    assert metrics.table_association_error_rate == 1.0
    assert metrics.fhir_mapping_error_rate == 1.0


def test_wilson_interval_is_bounded_and_zero_events_do_not_mean_zero_risk() -> None:
    interval = wilson_interval(0, 100)
    assert interval is not None
    low, high = interval
    assert low == 0.0
    assert 0.0 < high < 0.05

    interval2 = wilson_interval(50, 100)
    assert interval2 is not None
    low2, high2 = interval2
    assert 0.39 < low2 < 0.41
    assert 0.59 < high2 < 0.61

    assert wilson_interval(0, 0) is None


def test_risk_coverage_point_retains_interval() -> None:
    results = (
        evaluate_field(_truth("c1"), _prediction(case_id="c1")),
        evaluate_field(_truth("c2"), _prediction(case_id="c2", value_text="9.9")),
    )
    point = risk_coverage_point(EvaluationMethod.SAFEOCR, results)
    assert point.coverage == 1.0
    assert point.unsafe_accept_rate == 0.5
    assert point.unsafe_accept_interval_95 is not None


def test_final_evaluation_data_cannot_be_used_for_calibration() -> None:
    final_prediction = _prediction()
    with pytest.raises(ValueError, match="calibration-only"):
        require_calibration_only((final_prediction,))

    calibration = FieldPrediction(
        case_id="cal-1",
        method=EvaluationMethod.SAFEOCR,
        role=EvaluationRole.CALIBRATION,
        decision=DecisionState.REVIEW_REQUIRED,
        analyte_text="Potassium",
        value_text="3.4",
        unit_text="mmol/L",
        patient_id="SAFE-CAL",
        row_id="row-01",
        fhir_mapping_correct=None,
    )
    assert require_calibration_only((calibration,)) == (calibration,)


def test_prediction_rejects_missing_values_for_verified_auto() -> None:
    with pytest.raises(ValueError, match="accepted prediction"):
        FieldPrediction(
            case_id="c1",
            method=EvaluationMethod.SAFEOCR,
            role=EvaluationRole.EVALUATION,
            decision=DecisionState.VERIFIED_AUTO,
            analyte_text=None,
            value_text=None,
            unit_text=None,
            patient_id=None,
            row_id=None,
            fhir_mapping_correct=None,
        )


def test_frozen_labgold_split_is_deterministic_and_role_disjoint() -> None:
    first = frozen_labgold_split()
    second = frozen_labgold_split()
    assert first == second

    calibration = tuple(item for item in first if item.role is EvaluationRole.CALIBRATION)
    evaluation = tuple(item for item in first if item.role is EvaluationRole.EVALUATION)

    assert len(calibration) == 24
    assert len(evaluation) == 48
    assert {item.patient_id for item in calibration}.isdisjoint(
        {item.patient_id for item in evaluation}
    )
    assert {item.case_id for item in calibration}.isdisjoint(
        {item.case_id for item in evaluation}
    )
    assert {item.corruption_seed for item in first if item.corruption_seed is not None}
    assert len(
        {item.corruption_seed for item in first if item.corruption_seed is not None}
    ) == 36
    assert validate_labgold_split(first) == first


def test_each_frozen_seed_has_clean_and_corrupted_variant() -> None:
    split = frozen_labgold_split()
    by_seed: dict[tuple[EvaluationRole, int], set[int | None]] = {}
    for item in split:
        by_seed.setdefault((item.role, item.record_seed), set()).add(item.corruption_seed)

    assert all(len(variants) == 2 for variants in by_seed.values())
    assert all(None in variants for variants in by_seed.values())


def test_labgold_split_manifest_is_canonical_and_stable() -> None:
    first = labgold_split_manifest_json(frozen_labgold_split())
    second = labgold_split_manifest_json(frozen_labgold_split())
    assert first == second
    assert first.endswith("\n")
    assert '"schema_version":1' in first


def test_split_validation_rejects_patient_role_leakage() -> None:
    split = list(frozen_labgold_split())
    calibration = next(item for item in split if item.role is EvaluationRole.CALIBRATION)
    evaluation_index = next(
        index for index, item in enumerate(split) if item.role is EvaluationRole.EVALUATION
    )
    evaluation = split[evaluation_index]
    split[evaluation_index] = LabGoldCasePlan(
        case_id=evaluation.case_id,
        role=evaluation.role,
        record_seed=evaluation.record_seed,
        template=evaluation.template,
        corruption_seed=evaluation.corruption_seed,
        patient_id=calibration.patient_id,
    )

    with pytest.raises(ValueError, match="patient identities cross"):
        validate_labgold_split(tuple(split))




def test_frozen_labgold_manifest_hash_is_preregistered() -> None:
    manifest = labgold_split_manifest_json(frozen_labgold_split())
    assert hashlib.sha256(manifest.encode("utf-8")).hexdigest() == (
        "3aa0af90f3d41d5a0b636ded5d784119da81a193b81a907b7bb69a789cc816a5"
    )



def test_primary_ocr_baseline_accepts_complete_and_abstains_incomplete() -> None:
    complete = primary_ocr_prediction(
        case_id="c1",
        role=EvaluationRole.EVALUATION,
        analyte_text="Potassium",
        value_text="3.4",
        unit_text="mmol/L",
        patient_id="SAFE-00000001",
        row_id="row-01",
    )
    assert complete.decision is DecisionState.VERIFIED_AUTO

    incomplete = primary_ocr_prediction(
        case_id="c2",
        role=EvaluationRole.EVALUATION,
        analyte_text="Potassium",
        value_text=None,
        unit_text="mmol/L",
        patient_id="SAFE-00000001",
        row_id="row-01",
    )
    assert incomplete.decision is DecisionState.ABSTAINED


def test_tesseract_crop_baseline_is_oracle_crop_value_read_only() -> None:
    prediction = tesseract_crop_prediction(
        _truth(),
        role=EvaluationRole.EVALUATION,
        read_text="8.4",
    )
    result = evaluate_field(_truth(), prediction)
    assert prediction.method is EvaluationMethod.TESSERACT_CROP
    assert result.accepted is True
    assert result.unsafe_accepted is True


def test_naive_agreement_accepts_exact_value_match_and_reviews_disagreement() -> None:
    primary = primary_ocr_prediction(
        case_id="c1",
        role=EvaluationRole.EVALUATION,
        analyte_text="Potassium",
        value_text="3.4",
        unit_text="mmol/L",
        patient_id="SAFE-00000001",
        row_id="row-01",
    )
    accepted = naive_agreement_prediction(primary, secondary_value_text="3.4")
    review = naive_agreement_prediction(primary, secondary_value_text="3.8")

    assert accepted.decision is DecisionState.VERIFIED_AUTO
    assert review.decision is DecisionState.REVIEW_REQUIRED


def test_naive_agreement_rejects_non_primary_input() -> None:
    tesseract = tesseract_crop_prediction(
        _truth(),
        role=EvaluationRole.EVALUATION,
        read_text="3.4",
    )
    with pytest.raises(ValueError, match="primary OCR"):
        naive_agreement_prediction(tesseract, secondary_value_text="3.4")



def test_truth_region_matching_uses_geometry_not_truth_text() -> None:
    page = PageAsset(
        document_sha256="a" * 64,
        page_index=0,
        width_px=100,
        height_px=100,
        page_sha256="b" * 64,
    )
    fingerprint = EngineFingerprint(
        engine_name="paddleocr",
        engine_version="3.7.0",
        model_name="test",
        backend="test",
    )
    wrong_text_best_geometry = CandidateSpan(
        page=page,
        box=BoundingBox(10, 10, 30, 30),
        text="8.4",
        engine_name=fingerprint.engine_name,
        engine_version=fingerprint.engine_version,
        confidence=0.9,
    )
    truth_text_poor_geometry = CandidateSpan(
        page=page,
        box=BoundingBox(25, 25, 45, 45),
        text="3.4",
        engine_name=fingerprint.engine_name,
        engine_version=fingerprint.engine_version,
        confidence=0.99,
    )
    result = PageOcrResult(
        page=page,
        fingerprint=fingerprint,
        spans=(wrong_text_best_geometry, truth_text_poor_geometry),
    )
    region = TruthRegion(
        role="value",
        row_id="row-01",
        text="3.4",
        box=BoundingBox(10, 10, 30, 30),
    )

    matched = match_span_to_truth_region(result, region)
    assert matched == wrong_text_best_geometry
