from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
from pathlib import Path
from typing import Any, cast

from PIL import Image
from setup_fhir_validator import (
    DEFAULT_DESTINATION,
    VALIDATOR_SHA256,
    install_validator,
)

from safeocr.contracts import (
    BoundingBox,
    CandidateSpan,
    Criticality,
    LabFieldCandidate,
    PageAsset,
)
from safeocr.fhir import FhirExportContext, export_verified_lab_field
from safeocr.fhir_validator import (
    FhirValidationError,
    FhirValidatorConfig,
    validate_fhir_r4_file,
)
from safeocr.ocr import CriticalCrop, CropRead
from safeocr.verification import (
    FieldEvidenceInput,
    PerturbationRead,
    UnitStatus,
    UnitValidation,
    derive_verification_trace,
    make_approved_perturbations,
)

_SMOKE_PATIENT_BINDING_KEY = bytes.fromhex("55" * 32)


def _resolve_java(explicit: str | None) -> str:
    if explicit:
        path = Path(explicit)
        if path.is_file():
            return str(path)
        raise RuntimeError(f"Java executable not found: {path}")

    on_path = shutil.which("java")
    if on_path:
        return on_path

    program_files = Path(r"C:\Program Files\Microsoft")
    candidates = sorted(
        program_files.glob("jdk-17*/bin/java.exe"),
        reverse=True,
    )
    if candidates:
        return str(candidates[0])
    raise RuntimeError("Java 17+ executable not found")


def _crop_png() -> bytes:
    image = Image.new("RGB", (44, 28), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _verified_trace():
    document_sha = hashlib.sha256(b"safeocr-f5-source-document").hexdigest()
    page_sha = hashlib.sha256(b"safeocr-f5-source-page").hexdigest()
    page = PageAsset(document_sha, 0, 1000, 760, page_sha)
    analyte = CandidateSpan(
        page=page,
        box=BoundingBox(40, 285, 133, 309),
        text="Potassium",
        engine_name="paddleocr",
        engine_version="3.7.0",
        confidence=0.99,
    )
    value = CandidateSpan(
        page=page,
        box=BoundingBox(330, 286, 366, 313),
        text="3.4",
        engine_name="paddleocr",
        engine_version="3.7.0",
        confidence=0.99,
    )
    unit = CandidateSpan(
        page=page,
        box=BoundingBox(480, 285, 555, 311),
        text="mmol/L",
        engine_name="paddleocr",
        engine_version="3.7.0",
        confidence=0.99,
    )
    field = LabFieldCandidate(
        analyte_text="Potassium",
        value_text="3.4",
        unit_text="mmol/L",
        criticality=Criticality.CRITICAL,
        source_spans=(analyte, value, unit),
    )
    crop_bytes = _crop_png()
    crop = CriticalCrop(
        source_page=page,
        requested_box=value.box,
        crop_box=BoundingBox(324, 280, 372, 319),
        png_bytes=crop_bytes,
        crop_sha256=hashlib.sha256(crop_bytes).hexdigest(),
    )
    binding = FieldEvidenceInput(
        field=field,
        analyte_span=analyte,
        value_span=value,
        unit_span=unit,
        value_crop=crop,
    )
    independent = CropRead(
        text="3.4",
        engine_name="tesseract",
        engine_version="5.4-test",
        executable="tesseract",
        crop_sha256=crop.crop_sha256,
    )
    perturbations = tuple(
        PerturbationRead(
            name=image.name,
            image_sha256=image.image_sha256,
            text="3.4",
            runtime_healthy=True,
        )
        for image in make_approved_perturbations(crop)
    )
    return derive_verification_trace(
        binding=binding,
        independent_read=independent,
        perturbation_reads=perturbations,
        unit_validation=UnitValidation(
            status=UnitStatus.VALID,
            source_text="mmol/L",
            validator_name="ucumvert",
            validator_version="0.3.2",
            error=None,
        ),
        expected_patient_id="SAFE-F5-0001",
        observed_patient_ids=("SAFE-F5-0001",),
        patient_binding_key=_SMOKE_PATIENT_BINDING_KEY,
        runtime_errors=(),
        policy_version="f4-v1",
    )


def run_smoke(
    *,
    java_executable: str,
    validator_jar: Path,
    workspace: Path,
) -> dict[str, object]:
    workspace.mkdir(parents=True, exist_ok=True)
    trace = _verified_trace()
    config = FhirValidatorConfig(
        java_executable=java_executable,
        validator_jar=validator_jar,
        expected_jar_sha256=VALIDATOR_SHA256,
        fhir_version="4.0.1",
        timeout_seconds=180.0,
    )
    artifact = export_verified_lab_field(
        trace,
        FhirExportContext(
            patient_identifier_system="urn:safeocr:synthetic-patient",
            patient_identifier_value="SAFE-F5-0001",
            patient_binding_key=_SMOKE_PATIENT_BINDING_KEY,
            source_content_type="image/png",
            recorded_at="2026-10-06T00:00:00Z",
        ),
        validator_config=config,
        validation_workspace=workspace,
    )
    bundle_path = artifact.validated_path
    valid_result = artifact.validation

    invalid_payload = cast(dict[str, Any], json.loads(artifact.canonical_json))
    entries = cast(list[dict[str, Any]], invalid_payload["entry"])
    observation = next(
        cast(dict[str, Any], entry["resource"])
        for entry in entries
        if cast(dict[str, Any], entry["resource"])["resourceType"] == "Observation"
    )
    observation["status"] = "definitely-not-valid"
    invalid_path = workspace / "safeocr-f5-invalid-bundle.json"
    invalid_path.write_text(
        json.dumps(invalid_payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    invalid_rejected = False
    invalid_error = ""
    try:
        validate_fhir_r4_file(invalid_path, config)
    except FhirValidationError as exc:
        invalid_rejected = True
        invalid_error = str(exc)

    if not invalid_rejected:
        raise RuntimeError("deliberately invalid FHIR bundle was not rejected")

    return {
        "schema_version": 1,
        "fhir_version": "4.0.1",
        "bundle_sha256": artifact.bundle_sha256,
        "evidence_sha256": artifact.evidence_sha256,
        "validator": {
            "version": valid_result.validator_version,
            "jar_sha256": valid_result.jar_sha256,
            "errors": valid_result.error_count,
            "warnings": valid_result.warning_count,
            "notes": valid_result.note_count,
            "terminology_mode": "n/a",
        },
        "valid_bundle": {
            "passed": True,
            "path": str(bundle_path),
        },
        "invalid_control": {
            "rejected": invalid_rejected,
            "error": invalid_error,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SafeOCR F5 FHIR R4 smoke")
    parser.add_argument("--java", default=None)
    parser.add_argument("--validator", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(".jev") / "f5-fhir-runtime",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    validator = install_validator(args.validator)
    payload = run_smoke(
        java_executable=_resolve_java(args.java),
        validator_jar=validator,
        workspace=args.workspace,
    )
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")


if __name__ == "__main__":
    main()
