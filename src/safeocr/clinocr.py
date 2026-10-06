from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

CLINOCR_UPSTREAM_REPOSITORY = "https://github.com/ClinOCR-Bench/ClinOCR-Bench"
CLINOCR_UPSTREAM_COMMIT = "3b720a951bb7eec4a4f4fb34a636e7335a19981e"
CLINOCR_EXPECTED_DOCUMENTS = 384
CLINOCR_EXPECTED_EXEMPLARS = 56
CLINOCR_EXPECTED_EVALUATION = 328

CLINOCR_SUBSETS = (
    "normal",
    "handwriting",
    "poor",
    "rotated",
    "tables",
    "mixed",
)


class ClinOcrRole(StrEnum):
    EXEMPLAR = "train"
    EVALUATION = "test"


@dataclass(frozen=True, slots=True)
class ClinOcrRecord:
    doc_id: str
    subset: str
    role: ClinOcrRole
    image_path: str
    ground_truth_path: str
    homo_id: str | None = None
    hetero_id: str | None = None

    def __post_init__(self) -> None:
        if not self.doc_id.strip():
            raise ValueError("doc_id must be non-empty")
        if self.subset not in CLINOCR_SUBSETS:
            raise ValueError(f"unsupported ClinOCR-Bench subset: {self.subset}")
        for name in ("image_path", "ground_truth_path"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if self.role is ClinOcrRole.EVALUATION and (
            not self.homo_id or not self.hetero_id
        ):
            raise ValueError("evaluation records require both one-shot exemplar ids")


@dataclass(frozen=True, slots=True)
class SafetyTrackManifest:
    name: str
    version: str
    upstream_commit: str
    evaluation_role: ClinOcrRole
    threshold_tuning_allowed: bool
    zero_shot_only: bool
    subsets: tuple[str, ...]
    headline_fields: tuple[str, ...]
    exclusions: tuple[str, ...]


def frozen_safety_track_manifest() -> SafetyTrackManifest:
    return SafetyTrackManifest(
        name="SafeOCR ClinOCR-Bench Safety Track",
        version="f6-v1",
        upstream_commit=CLINOCR_UPSTREAM_COMMIT,
        evaluation_role=ClinOcrRole.EVALUATION,
        threshold_tuning_allowed=False,
        zero_shot_only=True,
        subsets=CLINOCR_SUBSETS,
        headline_fields=(
            "critical_numeric_tokens",
            "patient_identity_tokens",
            "table_value_associations",
        ),
        exclusions=(
            "no threshold selection from ClinOCR-Bench evaluation outcomes",
            "no one-shot exemplar prompting in the SafeOCR v0.1 OCR pipeline",
            "no clinical correctness claim from transcript-only ground truth",
        ),
    )


def safety_track_manifest_json() -> str:
    manifest = frozen_safety_track_manifest()
    payload = {
        "name": manifest.name,
        "version": manifest.version,
        "upstream_repository": CLINOCR_UPSTREAM_REPOSITORY,
        "upstream_commit": manifest.upstream_commit,
        "expected_documents": CLINOCR_EXPECTED_DOCUMENTS,
        "expected_exemplars": CLINOCR_EXPECTED_EXEMPLARS,
        "expected_evaluation_documents": CLINOCR_EXPECTED_EVALUATION,
        "evaluation_role": manifest.evaluation_role.value,
        "threshold_tuning_allowed": manifest.threshold_tuning_allowed,
        "zero_shot_only": manifest.zero_shot_only,
        "subsets": list(manifest.subsets),
        "headline_fields": list(manifest.headline_fields),
        "exclusions": list(manifest.exclusions),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _as_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("optional string must be non-empty when present")
    return value


def _role_from_raw(raw: dict[str, Any]) -> ClinOcrRole:
    value = raw.get("role")
    if value in {"train", "exemplar"}:
        return ClinOcrRole.EXEMPLAR
    if value in {"test", "eval", "evaluation"}:
        return ClinOcrRole.EVALUATION
    raise ValueError(f"unsupported ClinOCR-Bench role: {value!r}")


def _subset_from_raw(raw: dict[str, Any], image_path: str) -> str:
    subset = raw.get("subset")
    if isinstance(subset, str) and subset in CLINOCR_SUBSETS:
        return subset
    normalized = image_path.replace("\\", "/")
    for candidate in CLINOCR_SUBSETS:
        if f"/{candidate}/" in f"/{normalized}":
            return candidate
    raise ValueError("cannot infer ClinOCR-Bench subset")


def record_from_lookup(raw: dict[str, Any]) -> ClinOcrRecord:
    image_path = _as_string(
        raw.get("image_path", raw.get("image")),
        field="image_path",
    )
    truth_path = _as_string(
        raw.get("ground_truth_path", raw.get("ground_truth")),
        field="ground_truth_path",
    )
    role = _role_from_raw(raw)
    return ClinOcrRecord(
        doc_id=_as_string(raw.get("doc_id"), field="doc_id"),
        subset=_subset_from_raw(raw, image_path),
        role=role,
        image_path=image_path,
        ground_truth_path=truth_path,
        homo_id=_optional_string(raw.get("homo_id")) if role is ClinOcrRole.EVALUATION else None,
        hetero_id=(
            _optional_string(raw.get("hetero_id"))
            if role is ClinOcrRole.EVALUATION
            else None
        ),
    )


def load_lookup_json(path: Path) -> tuple[ClinOcrRecord, ...]:
    parsed = cast(object, json.loads(path.read_text(encoding="utf-8")))
    values: list[object]
    if isinstance(parsed, list):
        values = cast(list[object], parsed)
    elif isinstance(parsed, dict):
        mapping = cast(dict[str, object], parsed)
        container = mapping.get("records")
        if container is None:
            container = mapping.get("documents")
        if not isinstance(container, list):
            raise ValueError("ClinOCR-Bench lookup object must contain records/documents")
        values = cast(list[object], container)
    else:
        raise ValueError("ClinOCR-Bench lookup must contain a list of records")

    if values and isinstance(values[0], dict):
        first = cast(dict[str, Any], values[0])
        if "homo_oneshot" in first or "hetero_oneshot" in first:
            return _records_from_upstream_lookup(values)

    records: list[ClinOcrRecord] = []
    for item in values:
        if not isinstance(item, dict):
            raise ValueError("each ClinOCR-Bench lookup record must be an object")
        records.append(record_from_lookup(cast(dict[str, Any], item)))
    return tuple(records)


def validate_lookup(records: tuple[ClinOcrRecord, ...], *, strict_counts: bool) -> None:
    ids = [item.doc_id for item in records]
    if len(ids) != len(set(ids)):
        raise ValueError("ClinOCR-Bench doc_id values must be unique")

    exemplars = {item.doc_id for item in records if item.role is ClinOcrRole.EXEMPLAR}
    evaluation = tuple(item for item in records if item.role is ClinOcrRole.EVALUATION)

    for item in evaluation:
        if item.homo_id not in exemplars or item.hetero_id not in exemplars:
            raise ValueError("evaluation one-shot ids must resolve only to exemplar records")

    if strict_counts:
        if len(records) != CLINOCR_EXPECTED_DOCUMENTS:
            raise ValueError("unexpected ClinOCR-Bench total document count")
        if len(exemplars) != CLINOCR_EXPECTED_EXEMPLARS:
            raise ValueError("unexpected ClinOCR-Bench exemplar count")
        if len(evaluation) != CLINOCR_EXPECTED_EVALUATION:
            raise ValueError("unexpected ClinOCR-Bench evaluation count")


def external_evaluation_records(
    records: tuple[ClinOcrRecord, ...],
) -> tuple[ClinOcrRecord, ...]:
    validate_lookup(records, strict_counts=False)
    return tuple(item for item in records if item.role is ClinOcrRole.EVALUATION)


def require_no_external_tuning(records: tuple[ClinOcrRecord, ...]) -> tuple[ClinOcrRecord, ...]:
    if any(item.role is ClinOcrRole.EVALUATION for item in records):
        raise ValueError(
            "external evaluation records are locked and cannot be used for calibration or tuning"
        )
    return records

def _record_from_upstream_exemplar(raw: dict[str, Any]) -> ClinOcrRecord:
    image_path = _as_string(raw.get("image"), field="image")
    return ClinOcrRecord(
        doc_id=_as_string(raw.get("doc_id"), field="doc_id"),
        subset=_subset_from_raw(raw, image_path),
        role=ClinOcrRole.EXEMPLAR,
        image_path=image_path,
        ground_truth_path=_as_string(raw.get("ground_truth"), field="ground_truth"),
    )


def _records_from_upstream_lookup(values: list[object]) -> tuple[ClinOcrRecord, ...]:
    exemplars: dict[str, ClinOcrRecord] = {}
    evaluation: list[ClinOcrRecord] = []

    for item in values:
        if not isinstance(item, dict):
            raise ValueError("each ClinOCR-Bench lookup record must be an object")
        raw = cast(dict[str, Any], item)
        homo_raw = raw.get("homo_oneshot")
        hetero_raw = raw.get("hetero_oneshot")
        if not isinstance(homo_raw, dict) or not isinstance(hetero_raw, dict):
            raise ValueError("upstream lookup evaluation record requires two one-shot objects")

        homo = _record_from_upstream_exemplar(cast(dict[str, Any], homo_raw))
        hetero = _record_from_upstream_exemplar(cast(dict[str, Any], hetero_raw))
        exemplars[homo.doc_id] = homo
        exemplars[hetero.doc_id] = hetero

        image_path = _as_string(raw.get("image"), field="image")
        evaluation.append(
            ClinOcrRecord(
                doc_id=_as_string(raw.get("doc_id"), field="doc_id"),
                subset=_subset_from_raw(raw, image_path),
                role=ClinOcrRole.EVALUATION,
                image_path=image_path,
                ground_truth_path=_as_string(
                    raw.get("ground_truth"),
                    field="ground_truth",
                ),
                homo_id=homo.doc_id,
                hetero_id=hetero.doc_id,
            )
        )

    return tuple(exemplars[key] for key in sorted(exemplars)) + tuple(evaluation)
