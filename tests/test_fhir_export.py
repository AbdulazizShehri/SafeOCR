# pyright: reportPrivateUsage=false
from __future__ import annotations

import hashlib
import io
import json
from dataclasses import replace
from pathlib import Path
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
from safeocr.fhir import (
    FhirExportArtifact,
    FhirExportContext,
    FhirExportError,
    _build_fhir_candidate,
    export_verified_lab_field,
)
from safeocr.fhir_validator import (
    OFFICIAL_VALIDATOR_SHA256,
    OFFICIAL_VALIDATOR_VERSION,
    FhirValidationError,
    FhirValidationResult,
    FhirValidatorConfig,
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

PATIENT_KEY = bytes.fromhex("22" * 32)
DOCUMENT_SHA = "d" * 64
PAGE_SHA = "e" * 64


def _crop_png() -> bytes:
    image = Image.new("RGB", (44, 28), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _trace(
    *,
    value_text: str = "3.4",
    unit_text: str = "mmol/L",
    independent_text: str | None = None,
    runtime_errors: tuple[str, ...] = (),
):
    page = PageAsset(DOCUMENT_SHA, 0, 1000, 760, PAGE_SHA)
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
        text=value_text,
        engine_name="paddleocr",
        engine_version="3.7.0",
        confidence=0.99,
    )
    unit = CandidateSpan(
        page=page,
        box=BoundingBox(480, 285, 555, 311),
        text=unit_text,
        engine_name="paddleocr",
        engine_version="3.7.0",
        confidence=0.99,
    )
    field = LabFieldCandidate(
        analyte_text="Potassium",
        value_text=value_text,
        unit_text=unit_text,
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
    secondary = value_text if independent_text is None else independent_text
    independent = CropRead(
        text=secondary,
        engine_name="tesseract",
        engine_version="5.4-test",
        executable="tesseract",
        crop_sha256=crop.crop_sha256,
    )
    perturbations = tuple(
        PerturbationRead(
            name=image.name,
            image_sha256=image.image_sha256,
            text=value_text,
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
            source_text=unit_text,
            validator_name="ucumvert",
            validator_version="0.3.2",
            error=None,
        ),
        expected_patient_id="SAFE-69904705",
        observed_patient_ids=("SAFE-69904705",),
        patient_binding_key=PATIENT_KEY,
        runtime_errors=runtime_errors,
        policy_version="f4-v1",
    )


def _context(
    *,
    patient_identifier_value: str = "SAFE-69904705",
    patient_binding_key: bytes = PATIENT_KEY,
    patient_identifier_system: str = "urn:safeocr:synthetic-patient",
    source_content_type: str = "image/png",
    recorded_at: str = "2026-10-06T00:00:00Z",
) -> FhirExportContext:
    return FhirExportContext(
        patient_identifier_system=patient_identifier_system,
        patient_identifier_value=patient_identifier_value,
        patient_binding_key=patient_binding_key,
        source_content_type=source_content_type,
        recorded_at=recorded_at,
    )


def _bundle(artifact: FhirExportArtifact) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(artifact.canonical_json))


def _resources(artifact: FhirExportArtifact) -> dict[str, Any]:
    bundle = _bundle(artifact)
    entries = cast(list[dict[str, Any]], bundle["entry"])
    return {
        cast(dict[str, Any], entry["resource"])["resourceType"]: cast(
            dict[str, Any], entry["resource"]
        )
        for entry in entries
    }


def test_review_required_evidence_cannot_export() -> None:
    trace = _trace(independent_text="3.8")
    assert trace.evidence_record.decision.state is DecisionState.REVIEW_REQUIRED

    with pytest.raises(FhirExportError):
        _build_fhir_candidate(trace, _context())


def test_abstained_evidence_cannot_export() -> None:
    trace = _trace(runtime_errors=("verifier_failure",))
    assert trace.evidence_record.decision.state is DecisionState.ABSTAINED

    with pytest.raises(FhirExportError):
        _build_fhir_candidate(trace, _context())


def test_inconsistent_trace_cannot_export() -> None:
    trace = _trace()
    inconsistent = replace(
        trace,
        signals=replace(trace.signals, unit_valid=False),
    )

    with pytest.raises(FhirExportError):
        _build_fhir_candidate(inconsistent, _context())


def test_patient_hmac_mismatch_cannot_export() -> None:
    with pytest.raises(FhirExportError):
        _build_fhir_candidate(
            _trace(),
            _context(patient_identifier_value="SAFE-OTHER"),
        )


def test_weak_patient_binding_key_cannot_export() -> None:
    with pytest.raises(FhirExportError):
        _build_fhir_candidate(
            _trace(),
            _context(patient_binding_key=b"short"),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("patient_identifier_system", "not a uri"),
        ("source_content_type", "image"),
        ("recorded_at", "2026-10-06 00:00:00"),
    ],
)
def test_invalid_export_context_fails_closed(field: str, value: object) -> None:
    context = _context()
    bad = replace(context, **{field: value})

    with pytest.raises(FhirExportError):
        _build_fhir_candidate(_trace(), bad)


def test_qualitative_value_is_not_exported_in_v01() -> None:
    trace = _trace(value_text="NEGATIVE", unit_text="1")
    assert trace.evidence_record.decision.state is DecisionState.VERIFIED_AUTO

    with pytest.raises(FhirExportError):
        _build_fhir_candidate(trace, _context())


def test_lossy_decimal_conversion_is_rejected() -> None:
    trace = _trace(value_text="0.12345678901234567890123456789")
    assert trace.evidence_record.decision.state is DecisionState.VERIFIED_AUTO

    with pytest.raises(FhirExportError):
        _build_fhir_candidate(trace, _context())


def test_fhir_mapping_preserves_verified_source_semantics() -> None:
    artifact = _build_fhir_candidate(_trace(), _context())
    resources = _resources(artifact)

    document = resources["DocumentReference"]
    assert document["status"] == "current"
    assert document["masterIdentifier"] == {
        "system": "urn:safeocr:document-sha256",
        "value": DOCUMENT_SHA,
    }
    attachment = document["content"][0]["attachment"]
    assert attachment["contentType"] == "image/png"
    assert "hash" not in attachment
    assert "url" not in attachment
    assert "data" not in attachment

    observation = resources["Observation"]
    assert observation["status"] == "unknown"
    assert observation["code"] == {"text": "Potassium"}
    assert observation["valueQuantity"] == {
        "value": 3.4,
        "unit": "mmol/L",
        "system": "http://unitsofmeasure.org",
        "code": "mmol/L",
    }
    assert "coding" not in observation["code"]

    diagnostic = resources["DiagnosticReport"]
    assert diagnostic["status"] == "unknown"
    assert diagnostic["code"] == {"text": "Laboratory report"}

    provenance = resources["Provenance"]
    assert provenance["recorded"] == "2026-10-06T00:00:00Z"
    assert provenance["activity"]["coding"][0] == {
        "system": "http://terminology.hl7.org/CodeSystem/v3-DataOperation",
        "code": "CREATE",
        "display": "create",
    }


def test_comparator_is_preserved_in_quantity() -> None:
    artifact = _build_fhir_candidate(_trace(value_text="<0.01"), _context())
    observation = _resources(artifact)["Observation"]
    assert observation["valueQuantity"]["value"] == 0.01
    assert observation["valueQuantity"]["comparator"] == "<"


def test_patient_subject_is_hmac_bound_and_key_is_not_serialized() -> None:
    artifact = _build_fhir_candidate(_trace(), _context())
    serialized = artifact.canonical_json
    resources = _resources(artifact)

    subject = resources["Observation"]["subject"]
    assert subject == {
        "identifier": {
            "system": "urn:safeocr:synthetic-patient",
            "value": "SAFE-69904705",
        }
    }
    assert PATIENT_KEY.hex() not in serialized


def test_provenance_links_resources_source_and_evidence() -> None:
    artifact = _build_fhir_candidate(_trace(), _context())
    bundle = _bundle(artifact)
    resources = _resources(artifact)
    entries = cast(list[dict[str, Any]], bundle["entry"])
    by_type = {
        cast(dict[str, Any], entry["resource"])["resourceType"]: entry
        for entry in entries
    }

    observation_url = by_type["Observation"]["fullUrl"]
    report_url = by_type["DiagnosticReport"]["fullUrl"]
    document_url = by_type["DocumentReference"]["fullUrl"]

    assert resources["Observation"]["derivedFrom"] == [{"reference": document_url}]
    assert resources["DiagnosticReport"]["result"] == [{"reference": observation_url}]
    assert resources["Provenance"]["target"] == [
        {"reference": observation_url},
        {"reference": report_url},
    ]
    assert resources["Provenance"]["entity"][0] == {
        "role": "source",
        "what": {"reference": document_url},
    }
    assert resources["Provenance"]["entity"][1] == {
        "role": "source",
        "what": {
            "identifier": {
                "system": "urn:safeocr:evidence-sha256",
                "value": artifact.evidence_sha256,
            }
        },
    }


def test_export_context_changes_resource_identity() -> None:
    trace = _trace()
    first = _build_fhir_candidate(trace, _context())
    second = _build_fhir_candidate(
        trace,
        _context(recorded_at="2026-10-06T00:00:01Z"),
    )

    first_bundle = _bundle(first)
    second_bundle = _bundle(second)
    assert first_bundle["id"] != second_bundle["id"]

    first_entries = cast(list[dict[str, Any]], first_bundle["entry"])
    second_entries = cast(list[dict[str, Any]], second_bundle["entry"])
    assert [entry["fullUrl"] for entry in first_entries] != [
        entry["fullUrl"] for entry in second_entries
    ]
    assert first.bundle_sha256 != second.bundle_sha256




def _release_workspace(name: str) -> Path:
    workspace = Path(".jev") / "test-fhir-release" / name
    workspace.mkdir(parents=True, exist_ok=True)
    for item in workspace.glob("*"):
        if item.is_file():
            item.unlink()
    return workspace


def _validator_config(workspace: Path) -> FhirValidatorConfig:
    jar = workspace / "validator_cli.jar"
    jar.write_bytes(b"validator")
    return FhirValidatorConfig(
        java_executable="java",
        validator_jar=jar,
        expected_jar_sha256=OFFICIAL_VALIDATOR_SHA256,
        fhir_version="4.0.1",
        timeout_seconds=30.0,
    )


def _validation_success(config: FhirValidatorConfig) -> FhirValidationResult:
    return FhirValidationResult(
        validator_version=OFFICIAL_VALIDATOR_VERSION,
        fhir_version="4.0.1",
        jar_sha256=OFFICIAL_VALIDATOR_SHA256,
        error_count=0,
        warning_count=0,
        note_count=0,
        stdout="",
        stderr="",
    )


def test_public_export_returns_only_after_validator_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _release_workspace("success")
    config = _validator_config(workspace)
    seen: list[Path] = []
    visible_release_files: list[list[Path]] = []

    def fake_validate(path: Path, active: FhirValidatorConfig) -> FhirValidationResult:
        seen.append(path)
        visible_release_files.append(list(workspace.glob("*.json")))
        assert active == config
        assert path.is_file()
        return _validation_success(config)

    monkeypatch.setattr("safeocr.fhir.validate_fhir_r4_file", fake_validate)
    release = export_verified_lab_field(
        _trace(),
        _context(),
        validator_config=config,
        validation_workspace=workspace,
    )

    assert len(seen) == 1
    assert seen[0].parent.name == ".staging"
    assert seen[0] != release.validated_path
    assert visible_release_files == [[]]
    assert release.validated_path.parent == workspace
    assert release.validated_path.is_file()
    assert release.validated_path.read_text(encoding="utf-8") == release.canonical_json
    assert release.validation.error_count == 0


def test_validator_failure_blocks_release_and_removes_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _release_workspace("failure")
    config = _validator_config(workspace)

    def fail_validate(_: Path, __: FhirValidatorConfig) -> FhirValidationResult:
        raise FhirValidationError("blocked")

    monkeypatch.setattr("safeocr.fhir.validate_fhir_r4_file", fail_validate)

    with pytest.raises(FhirValidationError):
        export_verified_lab_field(
            _trace(),
            _context(),
            validator_config=config,
            validation_workspace=workspace,
        )

    assert list(workspace.rglob("*.json")) == []




def test_unexpected_validator_exception_removes_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _release_workspace("unexpected-failure")
    config = _validator_config(workspace)

    def explode(_: Path, __: FhirValidatorConfig) -> FhirValidationResult:
        raise RuntimeError("unexpected validator crash")

    monkeypatch.setattr("safeocr.fhir.validate_fhir_r4_file", explode)

    with pytest.raises(RuntimeError, match="unexpected validator crash"):
        export_verified_lab_field(
            _trace(),
            _context(),
            validator_config=config,
            validation_workspace=workspace,
        )

    assert list(workspace.rglob("*.json")) == []

def test_post_validation_hash_change_blocks_release(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _release_workspace("tamper")
    config = _validator_config(workspace)

    def tamper(path: Path, _: FhirValidatorConfig) -> FhirValidationResult:
        path.write_text('{"tampered":true}', encoding="utf-8")
        return _validation_success(config)

    monkeypatch.setattr("safeocr.fhir.validate_fhir_r4_file", tamper)

    with pytest.raises(FhirExportError):
        export_verified_lab_field(
            _trace(),
            _context(),
            validator_config=config,
            validation_workspace=workspace,
        )

    assert list(workspace.rglob("*.json")) == []

def test_export_is_deterministic() -> None:
    first = _build_fhir_candidate(_trace(), _context())
    second = _build_fhir_candidate(_trace(), _context())

    assert first.canonical_json == second.canonical_json
    assert first.bundle_sha256 == second.bundle_sha256
    assert first.evidence_sha256 == second.evidence_sha256
    assert hashlib.sha256(first.canonical_json.encode()).hexdigest() == first.bundle_sha256


def test_public_export_rejects_nonofficial_validator_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _release_workspace("nonofficial-config")
    jar = workspace / "validator_cli.jar"
    jar.write_bytes(b"different-validator")
    config = FhirValidatorConfig(
        java_executable="java",
        validator_jar=jar,
        expected_jar_sha256=hashlib.sha256(jar.read_bytes()).hexdigest(),
        fhir_version="4.0.1",
        timeout_seconds=30.0,
    )

    def fake_validate(
        _path: Path,
        _active: FhirValidatorConfig,
    ) -> FhirValidationResult:
        return _validation_success(config)

    monkeypatch.setattr(
        "safeocr.fhir.validate_fhir_r4_file",
        fake_validate,
    )

    with pytest.raises(FhirExportError, match="official pinned FHIR validator"):
        export_verified_lab_field(
            _trace(),
            _context(),
            validator_config=config,
            validation_workspace=workspace,
        )


@pytest.mark.parametrize(
    ("validator_version", "fhir_version", "jar_sha256", "error_count"),
    [
        ("0.0.0", "4.0.1", OFFICIAL_VALIDATOR_SHA256, 0),
        (OFFICIAL_VALIDATOR_VERSION, "5.0.0", OFFICIAL_VALIDATOR_SHA256, 0),
        (OFFICIAL_VALIDATOR_VERSION, "4.0.1", "0" * 64, 0),
        (OFFICIAL_VALIDATOR_VERSION, "4.0.1", OFFICIAL_VALIDATOR_SHA256, 1),
    ],
)
def test_public_export_rejects_inconsistent_validator_result(
    monkeypatch: pytest.MonkeyPatch,
    validator_version: str,
    fhir_version: str,
    jar_sha256: str,
    error_count: int,
) -> None:
    workspace = _release_workspace(
        f"bad-validator-result-{validator_version}-{fhir_version}-{error_count}"
        .replace(".", "_")
    )
    config = _validator_config(workspace)

    def fake_validate(_path: Path, _active: FhirValidatorConfig) -> FhirValidationResult:
        return FhirValidationResult(
            validator_version=validator_version,
            fhir_version=fhir_version,
            jar_sha256=jar_sha256,
            error_count=error_count,
            warning_count=0,
            note_count=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr("safeocr.fhir.validate_fhir_r4_file", fake_validate)

    with pytest.raises(FhirExportError, match="validator result"):
        export_verified_lab_field(
            _trace(),
            _context(),
            validator_config=config,
            validation_workspace=workspace,
        )

    assert list(workspace.rglob("*.json")) == []
