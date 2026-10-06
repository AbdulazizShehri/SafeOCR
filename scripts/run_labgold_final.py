from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import subprocess
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Protocol, cast

from safeocr.contracts import Criticality, DecisionState, LabFieldCandidate, PageAsset
from safeocr.evaluation import (
    LABGOLD_SPLIT_SHA256,
    EvaluationMethod,
    EvaluationRole,
    FieldEvaluation,
    FieldPrediction,
    FieldTruth,
    aggregate_metrics,
    evaluate_field,
    frozen_labgold_split,
    match_span_to_truth_region,
    naive_agreement_prediction,
    parse_labgold_rows,
    primary_ocr_prediction,
    score_labgold_associations,
    tesseract_crop_prediction,
)
from safeocr.labgold import (
    CorruptedLabReport,
    RenderedLabReport,
    TruthRegion,
    apply_corruption,
    generate_fake_lab_record,
    render_lab_report,
)
from safeocr.ocr import (
    CriticalCrop,
    EngineFingerprint,
    PageOcrResult,
    extract_critical_crop,
    normalize_paddle_result,
    read_tesseract_crop,
)
from safeocr.verification import (
    FieldEvidenceInput,
    PerturbationRead,
    derive_verification_trace,
    make_approved_perturbations,
    validate_ucum_unit,
)

_FINAL_BINDING_KEY = bytes.fromhex("65" * 32)


class _PaddleResult(Protocol):
    json: Mapping[str, object]


class _PaddlePipeline(Protocol):
    def predict(self, input: str) -> Iterable[_PaddleResult]: ...


class _PaddleFactory(Protocol):
    def __call__(self, **kwargs: object) -> _PaddlePipeline: ...


def _build_paddle_pipeline() -> _PaddlePipeline:
    module = importlib.import_module("paddleocr")
    factory = cast(_PaddleFactory, module.PaddleOCR)
    return factory(
        text_detection_model_name="PP-OCRv6_small_det",
        text_recognition_model_name="PP-OCRv6_small_rec",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        text_recognition_batch_size=1,
        engine="onnxruntime",
        device="cpu",
    )


def _resolve_tesseract(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend(
        [
            Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
            Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("Tesseract executable not found; pass --tesseract explicitly")


def _tesseract_version(executable: Path) -> str:
    completed = subprocess.run(
        [str(executable), "--version"],
        check=True,
        capture_output=True,
        text=True,
        shell=False,
        timeout=10,
    )
    return completed.stdout.splitlines()[0].strip()


def _read_perturbations(
    crop: CriticalCrop,
    *,
    tesseract: Path,
    tesseract_version: str,
) -> tuple[PerturbationRead, ...]:
    reads: list[PerturbationRead] = []
    for image in make_approved_perturbations(crop):
        variant_crop = CriticalCrop(
            source_page=crop.source_page,
            requested_box=crop.requested_box,
            crop_box=crop.crop_box,
            png_bytes=image.png_bytes,
            crop_sha256=image.image_sha256,
        )
        read = read_tesseract_crop(
            variant_crop,
            executable=str(tesseract),
            engine_version=tesseract_version,
            timeout_seconds=10.0,
        )
        reads.append(
            PerturbationRead(
                name=image.name,
                image_sha256=image.image_sha256,
                text=read.text,
                runtime_healthy=True,
            )
        )
    return tuple(reads)


def _region(
    regions: tuple[TruthRegion, ...],
    *,
    role: str,
    row_id: str | None,
) -> TruthRegion:
    matches = [item for item in regions if item.role == role and item.row_id == row_id]
    if len(matches) != 1:
        raise RuntimeError(f"expected one truth region for role={role!r} row_id={row_id!r}")
    return matches[0]


def _normalize_page(
    png_bytes: bytes,
    *,
    width_px: int,
    height_px: int,
    pipeline: _PaddlePipeline,
) -> PageOcrResult:
    page_sha = hashlib.sha256(png_bytes).hexdigest()
    page = PageAsset(
        document_sha256=page_sha,
        page_index=0,
        width_px=width_px,
        height_px=height_px,
        page_sha256=page_sha,
    )
    with tempfile.TemporaryDirectory(prefix="safeocr-f6-cal-") as tmp:
        image_path = Path(tmp) / "labgold.png"
        image_path.write_bytes(png_bytes)
        results = list(pipeline.predict(str(image_path)))
    if len(results) != 1:
        raise RuntimeError(f"expected one PaddleOCR result, got {len(results)}")
    return normalize_paddle_result(
        page,
        results[0].json,
        EngineFingerprint(
            engine_name="paddleocr",
            engine_version=importlib.metadata.version("paddleocr"),
            model_name="PP-OCRv6_small_det+PP-OCRv6_small_rec",
            backend="onnxruntime-cpu",
        ),
    )


def _safeocr_prediction(
    *,
    truth: FieldTruth,
    result: PageOcrResult,
    png_bytes: bytes,
    regions: tuple[TruthRegion, ...],
    tesseract: Path,
    tesseract_version: str,
) -> FieldPrediction:
    analyte_region = _region(regions, role="analyte", row_id=truth.row_id)
    value_region = _region(regions, role="value", row_id=truth.row_id)
    unit_region = _region(regions, role="unit", row_id=truth.row_id)
    patient_region = _region(regions, role="patient_id", row_id=None)

    analyte = match_span_to_truth_region(result, analyte_region)
    value = match_span_to_truth_region(result, value_region)
    unit = match_span_to_truth_region(result, unit_region)
    patient = match_span_to_truth_region(result, patient_region)
    if analyte is None or value is None or unit is None or patient is None:
        return FieldPrediction(
            case_id=truth.case_id,
            method=EvaluationMethod.SAFEOCR,
            role=EvaluationRole.EVALUATION,
            decision=DecisionState.ABSTAINED,
            analyte_text=None if analyte is None else analyte.text,
            value_text=None if value is None else value.text,
            unit_text=None if unit is None else unit.text,
            patient_id=None if patient is None else patient.text,
            row_id=None,
            fhir_mapping_correct=None,
        )

    value_crop = extract_critical_crop(
        png_bytes,
        result.page,
        value.box,
        padding_px=6,
    )
    field = LabFieldCandidate(
        analyte_text=analyte.text,
        value_text=value.text,
        unit_text=unit.text,
        criticality=Criticality.CRITICAL,
        source_spans=(analyte, value, unit),
    )
    binding = FieldEvidenceInput(
        field=field,
        analyte_span=analyte,
        value_span=value,
        unit_span=unit,
        value_crop=value_crop,
    )
    independent = read_tesseract_crop(
        value_crop,
        executable=str(tesseract),
        engine_version=tesseract_version,
        timeout_seconds=10.0,
    )
    perturbations = _read_perturbations(
        value_crop,
        tesseract=tesseract,
        tesseract_version=tesseract_version,
    )
    trace = derive_verification_trace(
        binding=binding,
        independent_read=independent,
        perturbation_reads=perturbations,
        unit_validation=validate_ucum_unit(field.unit_text),
        expected_patient_id=truth.patient_id,
        observed_patient_ids=(patient.text,),
        patient_binding_key=_FINAL_BINDING_KEY,
        runtime_errors=(),
        policy_version="f4-v1",
    )
    return FieldPrediction(
        case_id=truth.case_id,
        method=EvaluationMethod.SAFEOCR,
        role=EvaluationRole.EVALUATION,
        decision=trace.evidence_record.decision.state,
        analyte_text=field.analyte_text,
        value_text=field.value_text,
        unit_text=field.unit_text,
        patient_id=patient.text,
        row_id=truth.row_id,
        fhir_mapping_correct=None,
    )


def _evaluate_document(
    *,
    case_id: str,
    report: RenderedLabReport | CorruptedLabReport,
    pipeline: _PaddlePipeline,
    tesseract: Path,
    tesseract_version: str,
) -> tuple[dict[EvaluationMethod, list[FieldEvaluation]], tuple[FieldEvaluation, ...]]:
    result = _normalize_page(
        report.png_bytes,
        width_px=report.width_px,
        height_px=report.height_px,
        pipeline=pipeline,
    )
    patient_region = _region(report.regions, role="patient_id", row_id=None)
    patient_span = match_span_to_truth_region(result, patient_region)

    buckets: dict[EvaluationMethod, list[FieldEvaluation]] = {
        method: [] for method in EvaluationMethod
    }
    truths: list[FieldTruth] = []
    for row in report.record.rows:
        field_case_id = f"{case_id}:{row.row_id}"
        truth = FieldTruth(
            case_id=field_case_id,
            patient_id=report.record.patient_id,
            document_id=report.page_sha256,
            row_id=row.row_id,
            analyte_text=row.analyte_text,
            value_text=row.value_text,
            unit_text=row.unit_text,
        )
        truths.append(truth)
        analyte = match_span_to_truth_region(
            result,
            _region(report.regions, role="analyte", row_id=row.row_id),
        )
        value_region = _region(report.regions, role="value", row_id=row.row_id)
        value = match_span_to_truth_region(result, value_region)
        unit = match_span_to_truth_region(
            result,
            _region(report.regions, role="unit", row_id=row.row_id),
        )

        primary = primary_ocr_prediction(
            case_id=field_case_id,
            role=EvaluationRole.EVALUATION,
            analyte_text=None if analyte is None else analyte.text,
            value_text=None if value is None else value.text,
            unit_text=None if unit is None else unit.text,
            patient_id=None if patient_span is None else patient_span.text,
            row_id=(
                row.row_id
                if analyte is not None and value is not None and unit is not None
                else None
            ),
        )
        buckets[EvaluationMethod.PRIMARY_OCR].append(evaluate_field(truth, primary))

        truth_crop = extract_critical_crop(
            report.png_bytes,
            result.page,
            value_region.box,
            padding_px=6,
        )
        crop_read = read_tesseract_crop(
            truth_crop,
            executable=str(tesseract),
            engine_version=tesseract_version,
            timeout_seconds=10.0,
        )
        tesseract_prediction = tesseract_crop_prediction(
            truth,
            role=EvaluationRole.EVALUATION,
            read_text=crop_read.text,
        )
        buckets[EvaluationMethod.TESSERACT_CROP].append(
            evaluate_field(truth, tesseract_prediction)
        )

        naive = naive_agreement_prediction(
            primary,
            secondary_value_text=crop_read.text,
        )
        buckets[EvaluationMethod.NAIVE_AGREEMENT].append(evaluate_field(truth, naive))

        safeocr = _safeocr_prediction(
            truth=truth,
            result=result,
            png_bytes=report.png_bytes,
            regions=report.regions,
            tesseract=tesseract,
            tesseract_version=tesseract_version,
        )
        buckets[EvaluationMethod.SAFEOCR].append(evaluate_field(truth, safeocr))

    parsed_rows = parse_labgold_rows(result)
    association_results = score_labgold_associations(
        tuple(truths),
        parsed_rows,
        method=EvaluationMethod.PRIMARY_OCR,
        role=EvaluationRole.EVALUATION,
    )
    return buckets, association_results


def _git_state() -> dict[str, object]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        shell=False,
        timeout=10,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
        shell=False,
        timeout=10,
    ).stdout
    return {"head": head, "working_tree_dirty": bool(status.strip())}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the single primary SafeOCR LabGold final evaluation"
    )
    parser.add_argument("--tesseract", default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs") / "evidence" / "F6_FINAL_EVALUATION.json",
    )
    args = parser.parse_args()
    plans = tuple(
        item
        for item in frozen_labgold_split()
        if item.role is EvaluationRole.EVALUATION
    )
    if len(plans) != 48:
        raise RuntimeError("frozen split must contain exactly 48 final-evaluation cases")

    if args.output.exists():
        raise RuntimeError("final evaluation evidence already exists; refusing rerun")

    git_at_start = _git_state()
    if git_at_start["working_tree_dirty"]:
        raise RuntimeError("final evaluation requires a clean exact-head working tree")

    pipeline = _build_paddle_pipeline()
    tesseract = _resolve_tesseract(args.tesseract)
    tesseract_version = _tesseract_version(tesseract)
    buckets: dict[EvaluationMethod, list[FieldEvaluation]] = {
        method: [] for method in EvaluationMethod
    }
    association_results: list[FieldEvaluation] = []

    for plan in plans:
        rendered = render_lab_report(
            generate_fake_lab_record(plan.record_seed),
            plan.template,
        )
        report: RenderedLabReport | CorruptedLabReport
        if plan.corruption_seed is None:
            report = rendered
        else:
            report = apply_corruption(rendered, seed=plan.corruption_seed)

        current, association = _evaluate_document(
            case_id=plan.case_id,
            report=report,
            pipeline=pipeline,
            tesseract=tesseract,
            tesseract_version=tesseract_version,
        )
        for method, results in current.items():
            buckets[method].extend(results)
        association_results.extend(association)

    payload = {
        "schema_version": 1,
        "run_kind": "primary_v0_1_final_evaluation",
        "role": EvaluationRole.EVALUATION.value,
        "split_sha256": LABGOLD_SPLIT_SHA256,
        "case_ids": [item.case_id for item in plans],
        "git": git_at_start,
        "document_cases": len(plans),
        "field_cases": sum(len(value) for value in buckets.values()) // len(buckets),
        "methods": {
            method.value: asdict(aggregate_metrics(tuple(results)))
            for method, results in buckets.items()
        },
        "association_scoring": {
            "mode": "ocr_geometry_only",
            "truth_geometry_used_for_parsing": False,
            "primary_ocr": asdict(aggregate_metrics(tuple(association_results))),
        },
        "runtime": {
            "paddleocr": importlib.metadata.version("paddleocr"),
            "tesseract": tesseract_version,
        },
        "alignment_mode": "truth_geometry_scoring",
        "limitations": [
            (
                "Legacy per-field method metrics still use truth geometry for score "
                "alignment; association_scoring parses rows from OCR geometry only."
            ),
            (
                "Patient attribution remains outside the OCR-only association scorer; "
                "table association is reported separately under association_scoring."
            ),
            (
                "The Tesseract crop baseline inherits benchmark field identity, so its "
                "exact-accuracy value measures crop-read correctness rather than full extraction."
            ),
        ],
    }
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")


if __name__ == "__main__":
    main()
