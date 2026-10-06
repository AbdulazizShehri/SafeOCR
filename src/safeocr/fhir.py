from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import NoReturn, TypeAlias, cast
from urllib.parse import quote, urlparse

from safeocr.contracts import DecisionState, decide, export_allowed
from safeocr.fhir_validator import (
    OFFICIAL_FHIR_VERSION,
    OFFICIAL_VALIDATOR_SHA256,
    OFFICIAL_VALIDATOR_VERSION,
    FhirValidationResult,
    FhirValidatorConfig,
    validate_fhir_r4_file,
)
from safeocr.verification import (
    UnitStatus,
    ValueKind,
    VerificationTrace,
    normalize_evidence_text,
    patient_binding_matches,
)

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MIME_RE = re.compile(r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+$")
_UTC_INSTANT_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
_FHIR_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "urn:safeocr:fhir:r4:v1")


class FhirExportError(ValueError):
    """Raised when verified evidence cannot be exported safely to FHIR R4."""


@dataclass(frozen=True, slots=True)
class FhirExportContext:
    """Caller-owned context required for a patient-linked FHIR export."""

    patient_identifier_system: str
    patient_identifier_value: str
    patient_binding_key: bytes
    source_content_type: str
    recorded_at: str


@dataclass(frozen=True, slots=True)
class FhirExportArtifact:
    """Immutable deterministic FHIR export artifact."""

    canonical_json: str
    evidence_sha256: str
    bundle_sha256: str

    def as_bundle(self) -> JsonObject:
        parsed = json.loads(self.canonical_json)
        if not isinstance(parsed, dict):
            raise FhirExportError("canonical FHIR artifact is not a JSON object")
        return cast(JsonObject, parsed)


@dataclass(frozen=True, slots=True)
class ValidatedFhirExportArtifact:
    """FHIR export released only after successful official validation."""

    candidate: FhirExportArtifact
    validation: FhirValidationResult
    validated_path: Path

    @property
    def canonical_json(self) -> str:
        return self.candidate.canonical_json

    @property
    def evidence_sha256(self) -> str:
        return self.candidate.evidence_sha256

    @property
    def bundle_sha256(self) -> str:
        return self.candidate.bundle_sha256

    def as_bundle(self) -> JsonObject:
        return self.candidate.as_bundle()


def _fail(message: str) -> NoReturn:
    raise FhirExportError(message)


def _validate_identifier_system(value: str) -> str:
    if not value or value != value.strip() or any(char.isspace() for char in value):
        _fail("patient identifier system must be a non-empty absolute URI")
    parsed = urlparse(value)
    if not parsed.scheme:
        _fail("patient identifier system must be an absolute URI")
    return value


def _validate_content_type(value: str) -> str:
    if not _MIME_RE.fullmatch(value):
        _fail("source_content_type must be a simple MIME type")
    return value


def _validate_recorded_at(value: str) -> str:
    if not _UTC_INSTANT_RE.fullmatch(value):
        _fail("recorded_at must be an explicit UTC FHIR instant ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise FhirExportError("recorded_at is not a valid calendar instant") from exc
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        _fail("recorded_at must be UTC")
    return value


def _validate_context(context: FhirExportContext) -> tuple[str, str, str]:
    system = _validate_identifier_system(context.patient_identifier_system)
    patient_value = normalize_evidence_text(context.patient_identifier_value)
    if not patient_value:
        _fail("patient_identifier_value must be non-empty")
    content_type = _validate_content_type(context.source_content_type)
    _validate_recorded_at(context.recorded_at)
    return system, patient_value, content_type


def _trace_document_sha256(trace: VerificationTrace) -> str:
    field = trace.binding.field
    if trace.evidence_record.field != field:
        _fail("verification trace field does not match its evidence record")
    if trace.evidence_record.signals != trace.signals:
        _fail("verification trace signals do not match its evidence record")

    expected_decision = decide(trace.signals, criticality=field.criticality)
    if trace.evidence_record.decision != expected_decision:
        _fail("verification trace decision is inconsistent with its signals")
    if not export_allowed(trace.evidence_record):
        _fail("only VERIFIED_AUTO evidence may be exported")
    if trace.evidence_record.decision.state is not DecisionState.VERIFIED_AUTO:
        _fail("terminal decision must be VERIFIED_AUTO")
    if trace.runtime_errors:
        _fail("verification trace contains runtime errors")
    if not trace.patient_linkage.exact_match:
        _fail("patient linkage is not exact")

    tag = trace.patient_linkage.matched_identifier_hmac_sha256
    if tag is None or not _SHA256_RE.fullmatch(tag):
        _fail("verification trace lacks a valid patient binding tag")

    if trace.parsed_value is None:
        _fail("verification trace lacks a parsed critical value")
    if trace.parsed_value.kind is not ValueKind.NUMERIC:
        _fail("FHIR v0.1 exports numeric laboratory values only")
    if trace.parsed_value.numeric_value is None:
        _fail("numeric verification trace lacks a Decimal value")
    if trace.parsed_value.normalized_text != normalize_evidence_text(field.value_text):
        _fail("parsed value does not correspond to the verified field text")

    if trace.unit_validation.status is not UnitStatus.VALID:
        _fail("FHIR export requires a VALID UCUM unit")
    if field.unit_text is None or trace.unit_validation.source_text is None:
        _fail("FHIR export requires explicit source unit text")
    if normalize_evidence_text(field.unit_text) != normalize_evidence_text(
        trace.unit_validation.source_text
    ):
        _fail("verified unit evidence does not match the field unit")

    document_hashes = {span.page.document_sha256 for span in field.source_spans}
    if len(document_hashes) != 1:
        _fail("FHIR export requires one unambiguous source document")
    document_sha256 = next(iter(document_hashes))
    if not _SHA256_RE.fullmatch(document_sha256):
        _fail("source document SHA-256 is malformed")

    if trace.binding.value_crop is None:
        _fail("FHIR export requires a bound critical crop")
    if trace.binding.value_crop.source_page.document_sha256 != document_sha256:
        _fail("critical crop document identity does not match field evidence")

    return document_sha256


def _decimal_to_json_number(value: Decimal) -> int | float:
    if not value.is_finite():
        _fail("FHIR Quantity value must be finite")
    integral = value.to_integral_value()
    if value == integral:
        return int(integral)

    candidate = float(value)
    if not math.isfinite(candidate) or Decimal(str(candidate)) != value:
        _fail("FHIR Quantity conversion would lose Decimal precision")
    return candidate


def _export_identity_sha256(
    *,
    evidence_sha256: str,
    patient_identifier_system: str,
    patient_binding_tag: str,
    source_content_type: str,
    recorded_at: str,
) -> str:
    payload: JsonObject = {
        "evidence_sha256": evidence_sha256,
        "patient_binding_hmac_sha256": patient_binding_tag,
        "patient_identifier_system": patient_identifier_system,
        "recorded_at": recorded_at,
        "source_content_type": source_content_type,
    }
    canonical = _canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _resource_id(export_identity_sha256: str, role: str) -> str:
    return str(uuid.uuid5(_FHIR_NAMESPACE, f"{export_identity_sha256}:{role}"))


def _full_url(resource_id: str) -> str:
    return f"urn:uuid:{resource_id}"


def _canonical_json(payload: JsonObject) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _build_fhir_candidate(
    trace: VerificationTrace,
    context: FhirExportContext,
) -> FhirExportArtifact:
    """Build an unreleased candidate bundle from fail-closed verified evidence."""

    patient_system, patient_value, content_type = _validate_context(context)
    document_sha256 = _trace_document_sha256(trace)

    tag = trace.patient_linkage.matched_identifier_hmac_sha256
    if tag is None:
        _fail("verification trace lacks a patient binding tag")
    try:
        patient_matches = patient_binding_matches(
            patient_value,
            context.patient_binding_key,
            tag,
        )
    except ValueError as exc:
        raise FhirExportError("invalid patient binding key") from exc
    if not patient_matches:
        _fail("caller patient identifier does not match verified F4 identity")

    parsed = trace.parsed_value
    if parsed is None or parsed.numeric_value is None:
        _fail("verified trace lost its numeric value after consistency checks")
    field = trace.binding.field
    if field.unit_text is None:
        _fail("verified trace lost its source unit after consistency checks")

    evidence_json = trace.to_json()
    evidence_sha256 = hashlib.sha256(evidence_json.encode("utf-8")).hexdigest()

    export_identity_sha256 = _export_identity_sha256(
        evidence_sha256=evidence_sha256,
        patient_identifier_system=patient_system,
        patient_binding_tag=tag,
        source_content_type=content_type,
        recorded_at=context.recorded_at,
    )

    document_id = _resource_id(export_identity_sha256, "document-reference")
    observation_id = _resource_id(export_identity_sha256, "observation")
    report_id = _resource_id(export_identity_sha256, "diagnostic-report")
    provenance_id = _resource_id(export_identity_sha256, "provenance")
    bundle_id = _resource_id(export_identity_sha256, "bundle")

    document_url = _full_url(document_id)
    observation_url = _full_url(observation_id)
    report_url = _full_url(report_id)
    provenance_url = _full_url(provenance_id)

    subject: JsonObject = {
        "identifier": {
            "system": patient_system,
            "value": patient_value,
        }
    }

    document: JsonObject = {
        "resourceType": "DocumentReference",
        "id": document_id,
        "masterIdentifier": {
            "system": "urn:safeocr:document-sha256",
            "value": document_sha256,
        },
        "status": "current",
        "subject": subject,
        "content": [
            {
                "attachment": {
                    "contentType": content_type,
                    "title": "SafeOCR source laboratory document",
                }
            }
        ],
    }

    quantity: JsonObject = {
        "value": _decimal_to_json_number(parsed.numeric_value),
        "unit": field.unit_text,
        "system": "http://unitsofmeasure.org",
        "code": field.unit_text,
    }
    if parsed.comparator is not None:
        quantity["comparator"] = parsed.comparator

    observation: JsonObject = {
        "resourceType": "Observation",
        "id": observation_id,
        "identifier": [
            {
                "system": "urn:safeocr:evidence-sha256",
                "value": evidence_sha256,
            }
        ],
        "status": "unknown",
        "code": {"text": field.analyte_text},
        "subject": subject,
        "derivedFrom": [{"reference": document_url}],
        "valueQuantity": quantity,
    }

    diagnostic_report: JsonObject = {
        "resourceType": "DiagnosticReport",
        "id": report_id,
        "identifier": [
            {
                "system": "urn:safeocr:evidence-sha256",
                "value": evidence_sha256,
            }
        ],
        "status": "unknown",
        "code": {"text": "Laboratory report"},
        "subject": subject,
        "result": [{"reference": observation_url}],
    }

    policy_version = quote(trace.evidence_record.policy_version, safe="")
    provenance: JsonObject = {
        "resourceType": "Provenance",
        "id": provenance_id,
        "target": [
            {"reference": observation_url},
            {"reference": report_url},
        ],
        "recorded": context.recorded_at,
        "policy": [f"urn:safeocr:policy:{policy_version}"],
        "activity": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-DataOperation",
                    "code": "CREATE",
                    "display": "create",
                }
            ]
        },
        "agent": [
            {
                "who": {
                    "identifier": {
                        "system": "urn:safeocr:software",
                        "value": "safeocr-health",
                    }
                }
            }
        ],
        "entity": [
            {
                "role": "source",
                "what": {"reference": document_url},
            },
            {
                "role": "source",
                "what": {
                    "identifier": {
                        "system": "urn:safeocr:evidence-sha256",
                        "value": evidence_sha256,
                    }
                },
            },
        ],
    }

    bundle: JsonObject = {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "collection",
        "entry": [
            {"fullUrl": document_url, "resource": document},
            {"fullUrl": observation_url, "resource": observation},
            {"fullUrl": report_url, "resource": diagnostic_report},
            {"fullUrl": provenance_url, "resource": provenance},
        ],
    }
    canonical_json = _canonical_json(bundle)
    bundle_sha256 = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return FhirExportArtifact(
        canonical_json=canonical_json,
        evidence_sha256=evidence_sha256,
        bundle_sha256=bundle_sha256,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_official_validator_config(config: FhirValidatorConfig) -> None:
    if config.expected_jar_sha256 != OFFICIAL_VALIDATOR_SHA256:
        raise FhirExportError(
            "public export requires the official pinned FHIR validator JAR"
        )
    if config.fhir_version != OFFICIAL_FHIR_VERSION:
        raise FhirExportError(
            "public export requires the frozen FHIR R4 4.0.1 validator mode"
        )


def _require_official_validator_result(result: FhirValidationResult) -> None:
    if (
        result.validator_version != OFFICIAL_VALIDATOR_VERSION
        or result.fhir_version != OFFICIAL_FHIR_VERSION
        or result.jar_sha256 != OFFICIAL_VALIDATOR_SHA256
        or result.error_count != 0
    ):
        raise FhirExportError(
            "validator result does not match the frozen SafeOCR F5 validator policy"
        )


def export_verified_lab_field(
    trace: VerificationTrace,
    context: FhirExportContext,
    *,
    validator_config: FhirValidatorConfig,
    validation_workspace: Path,
) -> ValidatedFhirExportArtifact:
    """Release a FHIR artifact only after the pinned validator succeeds."""

    _require_official_validator_config(validator_config)
    candidate = _build_fhir_candidate(trace, context)
    validation_workspace.mkdir(parents=True, exist_ok=True)
    staging_dir = validation_workspace / ".staging"
    staging_dir.mkdir(parents=True, exist_ok=True)

    validated_path = validation_workspace / f"{candidate.bundle_sha256}.json"
    staging_path = staging_dir / f"{candidate.bundle_sha256}.json"
    partial_path = staging_dir / f"{candidate.bundle_sha256}.json.part"

    partial_path.unlink(missing_ok=True)
    staging_path.unlink(missing_ok=True)
    staged = False
    published = False
    released = False

    try:
        partial_path.write_text(candidate.canonical_json, encoding="utf-8")
        if _sha256_file(partial_path) != candidate.bundle_sha256:
            raise FhirExportError("candidate file hash mismatch before validation")
        partial_path.replace(staging_path)
        staged = True

        validation = validate_fhir_r4_file(staging_path, validator_config)
        _require_official_validator_result(validation)

        if _sha256_file(staging_path) != candidate.bundle_sha256:
            raise FhirExportError("validated FHIR staging file changed during validation")

        staging_path.replace(validated_path)
        staged = False
        published = True

        if _sha256_file(validated_path) != candidate.bundle_sha256:
            raise FhirExportError("published FHIR file hash mismatch after promotion")

        result = ValidatedFhirExportArtifact(
            candidate=candidate,
            validation=validation,
            validated_path=validated_path,
        )
        released = True
        return result
    finally:
        partial_path.unlink(missing_ok=True)
        if staged:
            staging_path.unlink(missing_ok=True)
        if published and not released:
            validated_path.unlink(missing_ok=True)
