from __future__ import annotations

import json
import math
from dataclasses import dataclass
from enum import StrEnum

from safeocr.contracts import BoundingBox, CandidateSpan, DecisionState
from safeocr.labgold import LabTemplate, TruthRegion, generate_fake_lab_record
from safeocr.ocr import PageOcrResult
from safeocr.verification import normalize_evidence_text

LABGOLD_SPLIT_SHA256 = "3aa0af90f3d41d5a0b636ded5d784119da81a193b81a907b7bb69a789cc816a5"


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

@dataclass(frozen=True, slots=True)
class LabGoldCasePlan:
    case_id: str
    role: EvaluationRole
    record_seed: int
    template: LabTemplate
    corruption_seed: int | None
    patient_id: str

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must be non-empty")
        if type(self.record_seed) is not int or self.record_seed < 0:
            raise ValueError("record_seed must be a non-negative int")
        if self.corruption_seed is not None and (
            type(self.corruption_seed) is not int or self.corruption_seed < 0
        ):
            raise ValueError("corruption_seed must be a non-negative int or None")
        if not self.patient_id.strip():
            raise ValueError("patient_id must be non-empty")


def _planned_variants(
    *,
    role: EvaluationRole,
    record_seed: int,
    template: LabTemplate,
    corruption_seed: int,
) -> tuple[LabGoldCasePlan, LabGoldCasePlan]:
    patient_id = generate_fake_lab_record(record_seed).patient_id
    prefix = f"labgold-{role.value}-{record_seed:06d}-{template.value}"
    clean = LabGoldCasePlan(
        case_id=f"{prefix}-clean",
        role=role,
        record_seed=record_seed,
        template=template,
        corruption_seed=None,
        patient_id=patient_id,
    )
    corrupted = LabGoldCasePlan(
        case_id=f"{prefix}-corrupt-{corruption_seed:06d}",
        role=role,
        record_seed=record_seed,
        template=template,
        corruption_seed=corruption_seed,
        patient_id=patient_id,
    )
    return (clean, corrupted)


def frozen_labgold_split() -> tuple[LabGoldCasePlan, ...]:
    """Return the preregistered v0.1 LabGold calibration/evaluation schedule."""

    templates = (LabTemplate.CLASSIC, LabTemplate.COMPACT, LabTemplate.GRID)
    planned: list[LabGoldCasePlan] = []

    for index, seed in enumerate(range(101, 113)):
        planned.extend(
            _planned_variants(
                role=EvaluationRole.CALIBRATION,
                record_seed=seed,
                template=templates[index % len(templates)],
                corruption_seed=5001 + index,
            )
        )

    for index, seed in enumerate(range(2001, 2025)):
        planned.extend(
            _planned_variants(
                role=EvaluationRole.EVALUATION,
                record_seed=seed,
                template=templates[index % len(templates)],
                corruption_seed=9001 + index,
            )
        )

    return validate_labgold_split(tuple(planned))


def validate_labgold_split(
    plans: tuple[LabGoldCasePlan, ...],
) -> tuple[LabGoldCasePlan, ...]:
    if not plans:
        raise ValueError("LabGold split must contain at least one planned case")
    case_ids = [item.case_id for item in plans]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("LabGold split case_id values must be unique")

    corruption_seeds = [
        item.corruption_seed for item in plans if item.corruption_seed is not None
    ]
    if len(corruption_seeds) != len(set(corruption_seeds)):
        raise ValueError("LabGold corruption seeds must be unique")

    calibration_patients = {
        item.patient_id for item in plans if item.role is EvaluationRole.CALIBRATION
    }
    evaluation_patients = {
        item.patient_id for item in plans if item.role is EvaluationRole.EVALUATION
    }
    external_patients = {
        item.patient_id for item in plans if item.role is EvaluationRole.EXTERNAL_EVALUATION
    }
    if calibration_patients & evaluation_patients:
        raise ValueError("LabGold patient identities cross calibration/evaluation roles")
    if calibration_patients & external_patients:
        raise ValueError("LabGold patient identities cross calibration/external roles")
    if evaluation_patients & external_patients:
        raise ValueError("LabGold patient identities cross evaluation/external roles")

    by_role_seed: dict[tuple[EvaluationRole, int], list[LabGoldCasePlan]] = {}
    for item in plans:
        by_role_seed.setdefault((item.role, item.record_seed), []).append(item)
    for variants in by_role_seed.values():
        if len(variants) != 2:
            raise ValueError("each LabGold record seed must have clean and corrupted variants")
        corruption_values = {item.corruption_seed for item in variants}
        if None not in corruption_values or len(corruption_values) != 2:
            raise ValueError("each LabGold seed requires one clean and one corrupted variant")
        patient_ids = {item.patient_id for item in variants}
        templates = {item.template for item in variants}
        if len(patient_ids) != 1 or len(templates) != 1:
            raise ValueError("LabGold clean/corrupted variants must share truth identity")

    return plans


def labgold_split_manifest_json(plans: tuple[LabGoldCasePlan, ...]) -> str:
    validated = validate_labgold_split(plans)
    payload = {
        "schema_version": 1,
        "split_id": "safeocr-labgold-v1-f6",
        "cases": [
            {
                "case_id": item.case_id,
                "corruption_seed": item.corruption_seed,
                "patient_id": item.patient_id,
                "record_seed": item.record_seed,
                "role": item.role.value,
                "template": item.template.value,
            }
            for item in validated
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"



def primary_ocr_prediction(
    *,
    case_id: str,
    role: EvaluationRole,
    analyte_text: str | None,
    value_text: str | None,
    unit_text: str | None,
    patient_id: str | None,
    row_id: str | None,
) -> FieldPrediction:
    required = (analyte_text, value_text, unit_text, patient_id, row_id)
    complete = all(value is not None and value.strip() for value in required)
    return FieldPrediction(
        case_id=case_id,
        method=EvaluationMethod.PRIMARY_OCR,
        role=role,
        decision=DecisionState.VERIFIED_AUTO if complete else DecisionState.ABSTAINED,
        analyte_text=analyte_text,
        value_text=value_text,
        unit_text=unit_text,
        patient_id=patient_id,
        row_id=row_id,
        fhir_mapping_correct=None,
    )


def tesseract_crop_prediction(
    truth: FieldTruth,
    *,
    role: EvaluationRole,
    read_text: str | None,
) -> FieldPrediction:
    value = None if read_text is None or not read_text.strip() else read_text
    return FieldPrediction(
        case_id=truth.case_id,
        method=EvaluationMethod.TESSERACT_CROP,
        role=role,
        decision=DecisionState.VERIFIED_AUTO if value is not None else DecisionState.ABSTAINED,
        analyte_text=truth.analyte_text if value is not None else None,
        value_text=value,
        unit_text=truth.unit_text if value is not None else None,
        patient_id=truth.patient_id if value is not None else None,
        row_id=truth.row_id if value is not None else None,
        fhir_mapping_correct=None,
    )


def naive_agreement_prediction(
    primary: FieldPrediction,
    *,
    secondary_value_text: str | None,
) -> FieldPrediction:
    if primary.method is not EvaluationMethod.PRIMARY_OCR:
        raise ValueError("naive agreement requires a primary OCR prediction")

    if primary.decision is DecisionState.ABSTAINED:
        decision = DecisionState.ABSTAINED
    elif (
        primary.value_text is not None
        and secondary_value_text is not None
        and normalize_evidence_text(primary.value_text)
        == normalize_evidence_text(secondary_value_text)
    ):
        decision = DecisionState.VERIFIED_AUTO
    else:
        decision = DecisionState.REVIEW_REQUIRED

    return FieldPrediction(
        case_id=primary.case_id,
        method=EvaluationMethod.NAIVE_AGREEMENT,
        role=primary.role,
        decision=decision,
        analyte_text=primary.analyte_text,
        value_text=primary.value_text,
        unit_text=primary.unit_text,
        patient_id=primary.patient_id,
        row_id=primary.row_id,
        fhir_mapping_correct=None,
    )



def _intersection_area(left: BoundingBox, right: BoundingBox) -> int:
    width = max(0, min(left.x2, right.x2) - max(left.x1, right.x1))
    height = max(0, min(left.y2, right.y2) - max(left.y1, right.y1))
    return width * height


def match_span_to_truth_region(
    result: PageOcrResult,
    region: TruthRegion,
    *,
    minimum_truth_overlap: float = 0.25,
) -> CandidateSpan | None:
    """Align OCR output to benchmark truth geometry without using truth text."""

    if not 0.0 < minimum_truth_overlap <= 1.0:
        raise ValueError("minimum_truth_overlap must be in (0, 1]")

    truth_area = (region.box.x2 - region.box.x1) * (region.box.y2 - region.box.y1)
    if truth_area <= 0:
        raise ValueError("truth region must have positive area")

    ranked: list[tuple[float, float, int, int, int, int, str, CandidateSpan]] = []
    for span in result.spans:
        overlap = _intersection_area(span.box, region.box) / truth_area
        if overlap < minimum_truth_overlap:
            continue
        ranked.append(
            (
                overlap,
                -1.0 if span.confidence is None else span.confidence,
                -span.box.x1,
                -span.box.y1,
                -span.box.x2,
                -span.box.y2,
                span.text,
                span,
            )
        )

    if not ranked:
        return None
    ranked.sort(reverse=True, key=lambda item: item[:-1])
    return ranked[0][-1]


@dataclass(frozen=True, slots=True)
class ParsedLabGoldRow:
    """One OCR-only LabGold table row reconstructed without truth geometry."""

    ordinal: int
    analyte_text: str
    value_text: str
    unit_text: str
    y_center: float

    def __post_init__(self) -> None:
        if self.ordinal <= 0:
            raise ValueError("ordinal must be positive")
        if not self.analyte_text.strip():
            raise ValueError("analyte_text must be non-empty")
        if not self.value_text.strip():
            raise ValueError("value_text must be non-empty")
        if not self.unit_text.strip():
            raise ValueError("unit_text must be non-empty")
        if not math.isfinite(self.y_center):
            raise ValueError("y_center must be finite")


def _span_center(span: CandidateSpan) -> tuple[float, float]:
    return (
        (span.box.x1 + span.box.x2) / 2.0,
        (span.box.y1 + span.box.y2) / 2.0,
    )


def _labgold_column_role(span: CandidateSpan) -> str | None:
    x_center, _ = _span_center(span)
    x_ratio = x_center / span.page.width_px
    if 0.03 <= x_ratio < 0.28:
        return "analyte"
    if 0.28 <= x_ratio < 0.42:
        return "value"
    if 0.42 <= x_ratio < 0.57:
        return "unit"
    return None


def _best_cluster_span(spans: list[CandidateSpan]) -> CandidateSpan:
    if not spans:
        raise ValueError("spans must be non-empty")
    return max(
        spans,
        key=lambda item: (
            -1.0 if item.confidence is None else item.confidence,
            -(item.box.x2 - item.box.x1),
            -item.box.x1,
            -item.box.y1,
            item.text,
        ),
    )


def parse_labgold_rows(
    result: PageOcrResult,
    *,
    y_tolerance_px: float | None = None,
) -> tuple[ParsedLabGoldRow, ...]:
    """Reconstruct LabGold rows from OCR coordinates only."""

    tolerance = (
        max(12.0, result.page.height_px * 0.025)
        if y_tolerance_px is None
        else y_tolerance_px
    )
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("y_tolerance_px must be finite and positive")

    headers = {
        "analyte": {"test"},
        "value": {"result"},
        "unit": {"units", "unit"},
    }
    classified: list[tuple[float, str, CandidateSpan]] = []
    for span in result.spans:
        role = _labgold_column_role(span)
        if role is None:
            continue
        text = normalize_evidence_text(span.text)
        if not text or text.casefold() in headers[role]:
            continue
        _, y_center = _span_center(span)
        classified.append((y_center, role, span))

    classified.sort(key=lambda item: (item[0], item[2].box.x1, item[2].text))
    clusters: list[list[tuple[float, str, CandidateSpan]]] = []
    for item in classified:
        if not clusters:
            clusters.append([item])
            continue
        current_center = sum(entry[0] for entry in clusters[-1]) / len(clusters[-1])
        if abs(item[0] - current_center) <= tolerance:
            clusters[-1].append(item)
        else:
            clusters.append([item])

    parsed: list[ParsedLabGoldRow] = []
    for cluster in clusters:
        by_role: dict[str, list[CandidateSpan]] = {
            "analyte": [],
            "value": [],
            "unit": [],
        }
        for _, role, span in cluster:
            by_role[role].append(span)
        if any(not by_role[role] for role in ("analyte", "value", "unit")):
            continue

        analyte = _best_cluster_span(by_role["analyte"])
        value = _best_cluster_span(by_role["value"])
        unit = _best_cluster_span(by_role["unit"])
        y_center = sum(_span_center(item)[1] for item in (analyte, value, unit)) / 3.0
        parsed.append(
            ParsedLabGoldRow(
                ordinal=len(parsed) + 1,
                analyte_text=analyte.text,
                value_text=value.text,
                unit_text=unit.text,
                y_center=y_center,
            )
        )
    return tuple(parsed)


def _truth_row_matches(
    truths: tuple[FieldTruth, ...],
    *,
    attribute: str,
    text: str,
) -> set[str]:
    matches: set[str] = set()
    for truth in truths:
        expected = getattr(truth, attribute)
        if not isinstance(expected, str):
            raise TypeError(f"{attribute} must resolve to str")
        if _same_text(text, expected):
            matches.add(truth.row_id)
    return matches


def score_labgold_associations(
    truths: tuple[FieldTruth, ...],
    rows: tuple[ParsedLabGoldRow, ...],
    *,
    method: EvaluationMethod = EvaluationMethod.PRIMARY_OCR,
    role: EvaluationRole = EvaluationRole.CALIBRATION,
) -> tuple[FieldEvaluation, ...]:
    """Score parsed rows after parsing, without truth-guided row construction."""

    if not truths:
        return ()
    if len({truth.case_id for truth in truths}) != len(truths):
        raise ValueError("truth case_id values must be unique")
    if len(rows) > len(truths):
        raise ValueError("parsed row count exceeds truth row count")

    scored: list[FieldEvaluation] = []
    for index, truth in enumerate(truths):
        if index >= len(rows):
            scored.append(
                FieldEvaluation(
                    case_id=truth.case_id,
                    method=method,
                    role=role,
                    decision=DecisionState.ABSTAINED,
                    exact_correct=False,
                    accepted=False,
                    unsafe_accepted=False,
                    patient_attribution_error=None,
                    table_association_error=None,
                    fhir_mapping_error=None,
                )
            )
            continue

        row = rows[index]
        exact_correct = (
            _same_text(row.analyte_text, truth.analyte_text)
            and _same_text(row.value_text, truth.value_text)
            and _same_text(row.unit_text, truth.unit_text)
        )
        analyte_rows = _truth_row_matches(
            truths, attribute="analyte_text", text=row.analyte_text
        )
        value_rows = _truth_row_matches(
            truths, attribute="value_text", text=row.value_text
        )
        unit_rows = _truth_row_matches(
            truths, attribute="unit_text", text=row.unit_text
        )
        association_error: bool | None
        if not analyte_rows or not value_rows or not unit_rows:
            association_error = None
        elif truth.row_id in (analyte_rows & value_rows & unit_rows):
            association_error = False
        elif len(analyte_rows) == 1 and len(value_rows) == 1:
            analyte_row = next(iter(analyte_rows))
            value_row = next(iter(value_rows))
            reciprocal_swap = False
            if analyte_row != value_row:
                for peer in rows:
                    peer_analyte = _truth_row_matches(
                        truths, attribute="analyte_text", text=peer.analyte_text
                    )
                    peer_value = _truth_row_matches(
                        truths, attribute="value_text", text=peer.value_text
                    )
                    if peer_analyte == {value_row} and peer_value == {analyte_row}:
                        reciprocal_swap = True
                        break
            association_error = True if reciprocal_swap else None
        else:
            association_error = None

        scored.append(
            FieldEvaluation(
                case_id=truth.case_id,
                method=method,
                role=role,
                decision=DecisionState.VERIFIED_AUTO,
                exact_correct=exact_correct,
                accepted=True,
                unsafe_accepted=not exact_correct,
                patient_attribution_error=None,
                table_association_error=association_error,
                fhir_mapping_error=None,
            )
        )
    return tuple(scored)
