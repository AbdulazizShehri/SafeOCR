from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from safeocr.contracts import DecisionState
from safeocr.verification import normalize_evidence_text


class EvaluationMethod(StrEnum):
    PRIMARY_OCR = "primary_ocr"
    TESSERACT_CROP = "tesseract_crop"
    NAIVE_AGREEMENT = "naive_agreement"
    SAFEOCR = "safeocr"


class EvaluationRole(StrEnum):
    CALIBRATION = "calibration"
    EVALUATION = "evaluation"
    EXTERNAL_EVALUATION = "external_evaluation"


@dataclass(frozen=True, slots=True)
class FieldTruth:
    case_id: str
    patient_id: str
    document_id: str
    row_id: str
    analyte_text: str
    value_text: str
    unit_text: str

    def __post_init__(self) -> None:
        for field_name in (
            "case_id",
            "patient_id",
            "document_id",
            "row_id",
            "analyte_text",
            "value_text",
            "unit_text",
        ):
            value = getattr(self, field_name)
            if not value.strip():
                raise ValueError(f"{field_name} must be non-empty")


@dataclass(frozen=True, slots=True)
class FieldPrediction:
    case_id: str
    method: EvaluationMethod
    role: EvaluationRole
    decision: DecisionState
    analyte_text: str | None
    value_text: str | None
    unit_text: str | None
    patient_id: str | None
    row_id: str | None
    fhir_mapping_correct: bool | None

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must be non-empty")
        if self.decision is DecisionState.VERIFIED_AUTO:
            required = {
                "analyte_text": self.analyte_text,
                "value_text": self.value_text,
                "unit_text": self.unit_text,
                "patient_id": self.patient_id,
                "row_id": self.row_id,
            }
            if any(value is None or not value.strip() for value in required.values()):
                raise ValueError("accepted prediction must retain all critical field bindings")


@dataclass(frozen=True, slots=True)
class FieldEvaluation:
    case_id: str
    method: EvaluationMethod
    role: EvaluationRole
    decision: DecisionState
    exact_correct: bool
    accepted: bool
    unsafe_accepted: bool
    patient_attribution_error: bool | None
    table_association_error: bool | None
    fhir_mapping_error: bool | None


@dataclass(frozen=True, slots=True)
class EvaluationMetrics:
    evaluable_count: int
    exact_correct_count: int
    critical_field_exact_accuracy: float | None
    accepted_count: int
    unsafe_accepted_count: int
    unsafe_accept_rate: float | None
    unsafe_accept_interval_95: tuple[float, float] | None
    verified_coverage: float | None
    review_count: int
    review_rate: float | None
    abstention_count: int
    abstention_rate: float | None
    patient_linked_accepted_count: int
    patient_attribution_error_count: int
    patient_attribution_error_rate: float | None
    table_linked_accepted_count: int
    table_association_error_count: int
    table_association_error_rate: float | None
    fhir_evaluated_count: int
    fhir_mapping_error_count: int
    fhir_mapping_error_rate: float | None


@dataclass(frozen=True, slots=True)
class RiskCoveragePoint:
    method: EvaluationMethod
    coverage: float | None
    unsafe_accept_rate: float | None
    unsafe_accept_interval_95: tuple[float, float] | None
    accepted_count: int
    evaluable_count: int


def _same_text(left: str | None, right: str) -> bool:
    if left is None:
        return False
    return normalize_evidence_text(left) == normalize_evidence_text(right)


def evaluate_field(truth: FieldTruth, prediction: FieldPrediction) -> FieldEvaluation:
    if truth.case_id != prediction.case_id:
        raise ValueError("truth and prediction case_id must match")

    exact_correct = (
        _same_text(prediction.analyte_text, truth.analyte_text)
        and _same_text(prediction.value_text, truth.value_text)
        and _same_text(prediction.unit_text, truth.unit_text)
        and prediction.row_id == truth.row_id
    )
    accepted = prediction.decision is DecisionState.VERIFIED_AUTO

    patient_error = None
    table_error = None
    fhir_error = None
    if accepted:
        patient_error = prediction.patient_id != truth.patient_id
        table_error = prediction.row_id != truth.row_id
        if prediction.fhir_mapping_correct is not None:
            fhir_error = not prediction.fhir_mapping_correct

    return FieldEvaluation(
        case_id=truth.case_id,
        method=prediction.method,
        role=prediction.role,
        decision=prediction.decision,
        exact_correct=exact_correct,
        accepted=accepted,
        unsafe_accepted=accepted and not exact_correct,
        patient_attribution_error=patient_error,
        table_association_error=table_error,
        fhir_mapping_error=fhir_error,
    )


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def wilson_interval(
    event_count: int,
    total_count: int,
    *,
    z: float = 1.959963984540054,
) -> tuple[float, float] | None:
    if total_count < 0 or event_count < 0 or event_count > total_count:
        raise ValueError("event_count and total_count must define a valid binomial count")
    if total_count == 0:
        return None
    if not math.isfinite(z) or z <= 0:
        raise ValueError("z must be finite and positive")

    proportion = event_count / total_count
    z2 = z * z
    denominator = 1.0 + z2 / total_count
    center = proportion + z2 / (2.0 * total_count)
    margin = z * math.sqrt(
        (proportion * (1.0 - proportion) + z2 / (4.0 * total_count))
        / total_count
    )
    low = max(0.0, (center - margin) / denominator)
    high = min(1.0, (center + margin) / denominator)
    if event_count == 0:
        low = 0.0
    if event_count == total_count:
        high = 1.0
    return (low, high)


def aggregate_metrics(results: tuple[FieldEvaluation, ...]) -> EvaluationMetrics:
    evaluable = len(results)
    exact_correct = sum(item.exact_correct for item in results)
    accepted = sum(item.accepted for item in results)
    unsafe = sum(item.unsafe_accepted for item in results)
    review = sum(item.decision is DecisionState.REVIEW_REQUIRED for item in results)
    abstain = sum(item.decision is DecisionState.ABSTAINED for item in results)

    patient_evaluable = sum(
        item.accepted and item.patient_attribution_error is not None for item in results
    )
    patient_errors = sum(item.patient_attribution_error is True for item in results)

    table_evaluable = sum(
        item.accepted and item.table_association_error is not None for item in results
    )
    table_errors = sum(item.table_association_error is True for item in results)

    fhir_evaluable = sum(item.accepted and item.fhir_mapping_error is not None for item in results)
    fhir_errors = sum(item.fhir_mapping_error is True for item in results)

    return EvaluationMetrics(
        evaluable_count=evaluable,
        exact_correct_count=exact_correct,
        critical_field_exact_accuracy=_rate(exact_correct, evaluable),
        accepted_count=accepted,
        unsafe_accepted_count=unsafe,
        unsafe_accept_rate=_rate(unsafe, accepted),
        unsafe_accept_interval_95=wilson_interval(unsafe, accepted),
        verified_coverage=_rate(accepted, evaluable),
        review_count=review,
        review_rate=_rate(review, evaluable),
        abstention_count=abstain,
        abstention_rate=_rate(abstain, evaluable),
        patient_linked_accepted_count=patient_evaluable,
        patient_attribution_error_count=patient_errors,
        patient_attribution_error_rate=_rate(patient_errors, patient_evaluable),
        table_linked_accepted_count=table_evaluable,
        table_association_error_count=table_errors,
        table_association_error_rate=_rate(table_errors, table_evaluable),
        fhir_evaluated_count=fhir_evaluable,
        fhir_mapping_error_count=fhir_errors,
        fhir_mapping_error_rate=_rate(fhir_errors, fhir_evaluable),
    )


def risk_coverage_point(
    method: EvaluationMethod,
    results: tuple[FieldEvaluation, ...],
) -> RiskCoveragePoint:
    if any(item.method is not method for item in results):
        raise ValueError("risk-coverage point must contain exactly one evaluation method")
    metrics = aggregate_metrics(results)
    return RiskCoveragePoint(
        method=method,
        coverage=metrics.verified_coverage,
        unsafe_accept_rate=metrics.unsafe_accept_rate,
        unsafe_accept_interval_95=metrics.unsafe_accept_interval_95,
        accepted_count=metrics.accepted_count,
        evaluable_count=metrics.evaluable_count,
    )


def require_calibration_only(
    predictions: tuple[FieldPrediction, ...],
) -> tuple[FieldPrediction, ...]:
    if any(item.role is not EvaluationRole.CALIBRATION for item in predictions):
        raise ValueError("calibration-only input contains held-out evaluation data")
    return predictions