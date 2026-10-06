from __future__ import annotations

import pytest

from safeocr.contracts import DecisionState
from safeocr.evaluation import (
    EvaluationMethod,
    EvaluationRole,
    FieldPrediction,
    FieldTruth,
    aggregate_metrics,
    evaluate_field,
    require_calibration_only,
    risk_coverage_point,
    wilson_interval,
)


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
