from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import subprocess
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Protocol, cast

from safeocr.contracts import (
    CandidateSpan,
    Criticality,
    DecisionState,
    LabFieldCandidate,
    PageAsset,
)
from safeocr.labgold import LabTemplate, generate_fake_lab_record, render_lab_report
from safeocr.ocr import (
    CriticalCrop,
    CropRead,
    EngineFingerprint,
    PageOcrResult,
    extract_critical_crop,
    normalize_paddle_result,
    read_tesseract_crop,
)
from safeocr.verification import (
    FieldEvidenceInput,
    PerturbationRead,
    VerificationTrace,
    derive_verification_trace,
    make_approved_perturbations,
    structural_association,
    validate_ucum_unit,
)

_SMOKE_PATIENT_BINDING_KEY = bytes.fromhex("42" * 32)


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
        engine="onnxruntime",
        device="cpu",
    )


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


def _unique_span(result: PageOcrResult, text: str) -> CandidateSpan:
    matches = [span for span in result.spans if span.text == text]
    if len(matches) != 1:
        raise RuntimeError(f"expected one OCR span for {text!r}, got {len(matches)}")
    return matches[0]


def _select_unit_span(
    result: PageOcrResult,
    *,
    analyte_span: CandidateSpan,
    value_span: CandidateSpan,
    field_unit: str,
    value_crop: CriticalCrop,
) -> tuple[LabFieldCandidate, FieldEvidenceInput]:
    candidates = [span for span in result.spans if span.text == field_unit]
    valid: list[tuple[LabFieldCandidate, FieldEvidenceInput]] = []
    for unit_span in candidates:
        field = LabFieldCandidate(
            analyte_text=analyte_span.text,
            value_text=value_span.text,
            unit_text=unit_span.text,
            criticality=Criticality.CRITICAL,
            source_spans=(analyte_span, value_span, unit_span),
        )
        binding = FieldEvidenceInput(
            field=field,
            analyte_span=analyte_span,
            value_span=value_span,
            unit_span=unit_span,
            value_crop=value_crop,
        )
        if structural_association(binding):
            valid.append((field, binding))
    if len(valid) != 1:
        raise RuntimeError(
            f"expected one structurally valid unit span for {field_unit!r}, got {len(valid)}"
        )
    return valid[0]


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


def _trace_payload(trace: VerificationTrace) -> dict[str, object]:
    return cast(dict[str, object], json.loads(trace.to_json()))


def run_smoke(*, tesseract: Path) -> dict[str, object]:
    record = generate_fake_lab_record(53)
    rendered = render_lab_report(record, LabTemplate.CLASSIC)
    page_sha = hashlib.sha256(rendered.png_bytes).hexdigest()
    page = PageAsset(
        document_sha256=page_sha,
        page_index=0,
        width_px=rendered.width_px,
        height_px=rendered.height_px,
        page_sha256=page_sha,
    )

    with tempfile.TemporaryDirectory(prefix="safeocr-f4-") as tmp:
        image_path = Path(tmp) / "labgold.png"
        image_path.write_bytes(rendered.png_bytes)
        pipeline = _build_paddle_pipeline()
        paddle_results = list(pipeline.predict(str(image_path)))

    if len(paddle_results) != 1:
        raise RuntimeError(f"expected one PaddleOCR result, got {len(paddle_results)}")

    normalized = normalize_paddle_result(
        page,
        paddle_results[0].json,
        EngineFingerprint(
            engine_name="paddleocr",
            engine_version=importlib.metadata.version("paddleocr"),
            model_name="PP-OCRv6_small_det+PP-OCRv6_small_rec",
            backend="onnxruntime-cpu",
        ),
    )

    analyte_span = _unique_span(normalized, "Potassium")
    value_span = _unique_span(normalized, "3.4")
    patient_id_span = _unique_span(normalized, record.patient_id)
    value_crop = extract_critical_crop(
        rendered.png_bytes,
        page,
        value_span.box,
        padding_px=6,
    )
    field, binding = _select_unit_span(
        normalized,
        analyte_span=analyte_span,
        value_span=value_span,
        field_unit="mmol/L",
        value_crop=value_crop,
    )

    tesseract_version = _tesseract_version(tesseract)
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
    unit_validation = validate_ucum_unit(field.unit_text)

    clean = derive_verification_trace(
        binding=binding,
        independent_read=independent,
        perturbation_reads=perturbations,
        unit_validation=unit_validation,
        expected_patient_id=record.patient_id,
        observed_patient_ids=(patient_id_span.text,),
        patient_binding_key=_SMOKE_PATIENT_BINDING_KEY,
        runtime_errors=(),
        policy_version="f4-v1",
    )
    if clean.evidence_record.decision.state is not DecisionState.VERIFIED_AUTO:
        raise RuntimeError(
            "clean F4 evidence did not reach VERIFIED_AUTO: "
            f"{clean.evidence_record.decision.to_json()}"
        )

    disagreement = derive_verification_trace(
        binding=binding,
        independent_read=CropRead(
            text="3.8",
            engine_name="tesseract",
            engine_version=tesseract_version,
            executable=str(tesseract),
            crop_sha256=value_crop.crop_sha256,
        ),
        perturbation_reads=perturbations,
        unit_validation=unit_validation,
        expected_patient_id=record.patient_id,
        observed_patient_ids=(patient_id_span.text,),
        patient_binding_key=_SMOKE_PATIENT_BINDING_KEY,
        runtime_errors=(),
        policy_version="f4-v1",
    )
    if disagreement.evidence_record.decision.state is DecisionState.VERIFIED_AUTO:
        raise RuntimeError("independent disagreement incorrectly reached VERIFIED_AUTO")

    return {
        "schema_version": 1,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "packages": {
            "paddleocr": importlib.metadata.version("paddleocr"),
            "onnxruntime": importlib.metadata.version("onnxruntime"),
            "ucumvert": importlib.metadata.version("ucumvert"),
        },
        "labgold": {
            "seed": record.seed,
            "template": LabTemplate.CLASSIC.value,
            "patient_id": record.patient_id,
            "page_sha256": page.page_sha256,
        },
        "field": {
            "analyte": field.analyte_text,
            "primary_value": field.value_text,
            "unit": field.unit_text,
            "independent_value": independent.text,
            "value_crop_sha256": value_crop.crop_sha256,
        },
        "perturbations": [
            {
                "name": item.name,
                "image_sha256": item.image_sha256,
                "text": item.text,
                "runtime_healthy": item.runtime_healthy,
            }
            for item in perturbations
        ],
        "unit_validation": {
            "status": unit_validation.status.value,
            "source_text": unit_validation.source_text,
            "validator_version": unit_validation.validator_version,
        },
        "patient_binding": {
            "scheme": "HMAC-SHA256",
            "key_scope": "synthetic-smoke-only",
            "matched_identifier_hmac_sha256": (
                clean.patient_linkage.matched_identifier_hmac_sha256
            ),
        },
        "clean": {
            "decision": clean.evidence_record.decision.state.value,
            "signals": json.loads(clean.evidence_record.to_json())["signals"],
            "trace": _trace_payload(clean),
        },
        "disagreement_control": {
            "secondary_value": "3.8",
            "decision": disagreement.evidence_record.decision.state.value,
            "failed_gates": list(disagreement.evidence_record.decision.failed_gates),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SafeOCR F4 verification smoke")
    parser.add_argument("--tesseract", default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    payload = run_smoke(tesseract=_resolve_tesseract(args.tesseract))
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")


if __name__ == "__main__":
    main()
