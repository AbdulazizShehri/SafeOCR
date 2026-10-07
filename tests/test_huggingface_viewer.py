from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.prepare_hf_viewer import (
    CANONICAL_MANIFEST_SHA256,
    project_viewer_row,
)

ROOT = Path(__file__).resolve().parents[1]


def _row(*, image_sha256: str, file_name: str = "images/sample.png") -> dict[str, object]:
    return {
        "case_id": "labgold-calibration-000001-classic-clean",
        "role": "calibration",
        "record_seed": 1,
        "corruption_seed": None,
        "template": "classic",
        "file_name": file_name,
        "image_sha256": image_sha256,
        "source_page_sha256": None,
        "synthetic_patient_id": "SYN-000001",
        "synthetic_report_id": "LAB-000001",
        "critical_field_count": 6,
        "regions": [
            {
                "role": "value",
                "row_id": "row-1",
                "text": "4.2",
                "box": {"x1": 1, "y1": 2, "x2": 3, "y2": 4},
            }
        ],
    }


def test_project_viewer_row_is_derived_from_verified_canonical_image(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset"
    images = dataset_root / "images"
    images.mkdir(parents=True)
    image_bytes = b"synthetic-png-placeholder"
    image = images / "sample.png"
    image.write_bytes(image_bytes)
    sha = hashlib.sha256(image_bytes).hexdigest()

    projected = project_viewer_row(dataset_root, _row(image_sha256=sha))

    assert projected["image"] == {"bytes": image_bytes, "path": "sample.png"}
    assert projected["case_id"] == "labgold-calibration-000001-classic-clean"
    assert projected["role"] == "calibration"
    assert projected["image_sha256"] == sha
    assert projected["critical_field_count"] == 6
    assert projected["regions_json"] == (
        '[{"box":{"x1":1,"x2":3,"y1":2,"y2":4},'
        '"role":"value","row_id":"row-1","text":"4.2"}]'
    )


def test_project_viewer_row_rejects_image_hash_mismatch(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset"
    images = dataset_root / "images"
    images.mkdir(parents=True)
    (images / "sample.png").write_bytes(b"actual")

    with pytest.raises(RuntimeError, match="image hash mismatch"):
        project_viewer_row(dataset_root, _row(image_sha256="0" * 64))


def test_project_viewer_row_rejects_path_escape(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset"
    dataset_root.mkdir()
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"outside")

    with pytest.raises(ValueError, match="escapes dataset root"):
        project_viewer_row(
            dataset_root,
            _row(
                image_sha256=hashlib.sha256(b"outside").hexdigest(),
                file_name="../outside.png",
            ),
        )


def test_hf_viewer_publication_contract_is_explicit() -> None:
    card = (ROOT / "huggingface" / "dataset" / "README.md").read_text(
        encoding="utf-8"
    )
    publishing = (ROOT / "huggingface" / "PUBLISHING.md").read_text(
        encoding="utf-8"
    )

    assert CANONICAL_MANIFEST_SHA256 == (
        "3a3fcdf1e3e045c0b6f8b334457d1e22dbd247a6a556e08235f808143abf5cec"
    )
    assert 'split: calibration' in card
    assert 'path: "viewer/calibration.parquet"' in card
    assert 'split: evaluation' in card
    assert 'path: "viewer/evaluation.parquet"' in card
    assert "24 rows" in card
    assert "48 rows" in card
    assert "audit source of truth" in card
    assert "prepare_hf_viewer.py" in publishing
