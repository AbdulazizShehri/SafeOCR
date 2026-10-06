from __future__ import annotations

import json
from pathlib import Path

import pytest

from safeocr.clinocr import (
    CLINOCR_EXPECTED_DOCUMENTS,
    CLINOCR_EXPECTED_EVALUATION,
    CLINOCR_EXPECTED_EXEMPLARS,
    CLINOCR_UPSTREAM_COMMIT,
    ClinOcrRole,
    external_evaluation_records,
    frozen_safety_track_manifest,
    load_lookup_json,
    record_from_lookup,
    require_no_external_tuning,
    safety_track_manifest_json,
    validate_lookup,
)


def _exemplar(doc_id: str = "normal-template1-sample1") -> dict[str, object]:
    return {
        "doc_id": doc_id,
        "role": "train",
        "subset": "normal",
        "image_path": f"scans/normal/{doc_id}.png",
        "ground_truth_path": f"ground_truth/normal/{doc_id}.txt",
    }


def _evaluation(
    doc_id: str = "normal-template1-sample2",
    *,
    homo_id: str = "normal-template1-sample1",
    hetero_id: str = "normal-template2-sample1",
) -> dict[str, object]:
    return {
        "doc_id": doc_id,
        "role": "test",
        "subset": "normal",
        "image_path": f"scans/normal/{doc_id}.png",
        "ground_truth_path": f"ground_truth/normal/{doc_id}.txt",
        "homo_id": homo_id,
        "hetero_id": hetero_id,
    }


def test_frozen_safety_track_manifest_is_external_eval_only() -> None:
    manifest = frozen_safety_track_manifest()
    assert manifest.upstream_commit == CLINOCR_UPSTREAM_COMMIT
    assert manifest.evaluation_role is ClinOcrRole.EVALUATION
    assert manifest.threshold_tuning_allowed is False
    assert manifest.zero_shot_only is True
    assert "table_value_associations" in manifest.headline_fields


def test_manifest_json_freezes_published_counts() -> None:
    payload = json.loads(safety_track_manifest_json())
    assert payload["expected_documents"] == CLINOCR_EXPECTED_DOCUMENTS == 384
    assert payload["expected_exemplars"] == CLINOCR_EXPECTED_EXEMPLARS == 56
    assert payload["expected_evaluation_documents"] == CLINOCR_EXPECTED_EVALUATION == 328
    assert payload["threshold_tuning_allowed"] is False


def test_record_from_lookup_accepts_published_role_names() -> None:
    exemplar = record_from_lookup(_exemplar())
    evaluation = record_from_lookup(_evaluation())

    assert exemplar.role is ClinOcrRole.EXEMPLAR
    assert evaluation.role is ClinOcrRole.EVALUATION
    assert evaluation.homo_id == "normal-template1-sample1"


def test_record_can_infer_subset_from_image_path() -> None:
    raw = _exemplar()
    raw.pop("subset")
    record = record_from_lookup(raw)
    assert record.subset == "normal"


def test_evaluation_record_requires_two_exemplar_ids() -> None:
    raw = _evaluation()
    raw["homo_id"] = None
    with pytest.raises(ValueError, match="one-shot exemplar ids"):
        record_from_lookup(raw)


def test_validate_lookup_rejects_test_to_test_demonstrations() -> None:
    records = (
        record_from_lookup(_exemplar("normal-template1-sample1")),
        record_from_lookup(_exemplar("normal-template2-sample1")),
        record_from_lookup(_evaluation()),
        record_from_lookup(
            _evaluation(
                "normal-template2-sample2",
                homo_id="normal-template1-sample2",
                hetero_id="normal-template1-sample1",
            )
        ),
    )
    with pytest.raises(ValueError, match="resolve only to exemplar"):
        validate_lookup(records, strict_counts=False)


def test_external_evaluation_records_preserve_locked_test_role() -> None:
    records = (
        record_from_lookup(_exemplar("normal-template1-sample1")),
        record_from_lookup(_exemplar("normal-template2-sample1")),
        record_from_lookup(_evaluation()),
    )
    selected = external_evaluation_records(records)
    assert len(selected) == 1
    assert selected[0].role is ClinOcrRole.EVALUATION


def test_external_test_records_cannot_enter_tuning_path() -> None:
    records = (
        record_from_lookup(_exemplar("normal-template1-sample1")),
        record_from_lookup(_exemplar("normal-template2-sample1")),
        record_from_lookup(_evaluation()),
    )
    with pytest.raises(ValueError, match="cannot be used for calibration or tuning"):
        require_no_external_tuning(records)

    exemplars = tuple(item for item in records if item.role is ClinOcrRole.EXEMPLAR)
    assert require_no_external_tuning(exemplars) == exemplars


def test_load_lookup_json_supports_record_list() -> None:
    payload = [
        _exemplar("normal-template1-sample1"),
        _exemplar("normal-template2-sample1"),
        _evaluation(),
    ]
    path = Path(".jev") / "clinocr-lookup-test.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        records = load_lookup_json(path)
    finally:
        path.unlink(missing_ok=True)
    assert len(records) == 3
    validate_lookup(records, strict_counts=False)


def test_load_lookup_json_supports_upstream_nested_oneshot_schema() -> None:
    payload = [
        {
            "doc_id": "normal_t1_s2",
            "subset": "normal",
            "template": 1,
            "sample": 2,
            "image": "scans/normal/template_1_sample_2_normal.jpg",
            "ground_truth": "ground_truth/normal/template_1_sample_2_normal.txt",
            "homo_oneshot": {
                "doc_id": "normal_t1_s1",
                "subset": "normal",
                "template": 1,
                "sample": 1,
                "image": "scans/normal/template_1_sample_1_normal.jpg",
                "ground_truth": "ground_truth/normal/template_1_sample_1_normal.txt",
            },
            "hetero_oneshot": {
                "doc_id": "normal_t2_s1",
                "subset": "normal",
                "template": 2,
                "sample": 1,
                "image": "scans/normal/template_2_sample_1_normal.jpg",
                "ground_truth": "ground_truth/normal/template_2_sample_1_normal.txt",
            },
        }
    ]
    path = Path(".jev") / "clinocr-upstream-lookup-test.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        records = load_lookup_json(path)
    finally:
        path.unlink(missing_ok=True)

    assert len(records) == 3
    exemplars = tuple(item for item in records if item.role is ClinOcrRole.EXEMPLAR)
    evaluation = tuple(item for item in records if item.role is ClinOcrRole.EVALUATION)
    assert {item.doc_id for item in exemplars} == {"normal_t1_s1", "normal_t2_s1"}
    assert evaluation[0].homo_id == "normal_t1_s1"
    assert evaluation[0].hetero_id == "normal_t2_s1"
