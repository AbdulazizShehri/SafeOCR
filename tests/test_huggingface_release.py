from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.prepare_hf_labgold import prepare

ROOT = Path(__file__).resolve().parents[1]


def test_static_space_declares_safe_public_boundary() -> None:
    readme = (ROOT / "huggingface" / "space" / "README.md").read_text(
        encoding="utf-8"
    )
    html = (ROOT / "huggingface" / "space" / "index.html").read_text(
        encoding="utf-8"
    )

    assert "sdk: static" in readme
    assert "synthetic verification-policy explorer" in readme
    assert "does not accept patient documents" in readme
    assert "does **not** demonstrate that SafeOCR is safer" in readme
    assert "0/288" in readme
    assert "0/209" in readme

    for signal in (
        "candidate_present",
        "visual_grounded",
        "independent_agreement",
        "perturbation_stable",
        "structural_association",
        "numeric_parse_unambiguous",
        "unit_valid",
        "patient_linkage_unambiguous",
        "runtime_healthy",
    ):
        assert signal in html

    assert "VERIFIED_AUTO" in html
    assert "REVIEW_REQUIRED" in html
    assert "ABSTAINED" in html
    assert "does not run PaddleOCR or Tesseract" in html
    assert "no patient uploads" in html


def test_hf_labgold_export_is_deterministic_and_complete(tmp_path: Path) -> None:
    split = ROOT / "docs" / "evidence" / "F6_LABGOLD_SPLIT.json"
    card = ROOT / "huggingface" / "dataset" / "README.md"
    output = tmp_path / "SafeOCR-LabGold"

    prepare(split_path=split, output=output, card_path=card)

    info = json.loads((output / "dataset_info.json").read_text(encoding="utf-8"))
    assert info == {
        "calibration_documents": 24,
        "case_count": 72,
        "critical_fields_per_document": 6,
        "evaluation_documents": 48,
        "manifest_sha256": info["manifest_sha256"],
        "metadata_sha256": info["metadata_sha256"],
        "viewer_metadata_sha256": info["viewer_metadata_sha256"],
        "readme_sha256": info["readme_sha256"],
        "schema_version": 1,
    }

    manifest_bytes = (output / "manifest.jsonl").read_bytes()
    metadata_bytes = (output / "metadata.jsonl").read_bytes()
    viewer_metadata_bytes = (output / "images" / "metadata.jsonl").read_bytes()
    assert metadata_bytes == manifest_bytes
    assert hashlib.sha256(manifest_bytes).hexdigest() == info["manifest_sha256"]
    assert hashlib.sha256(metadata_bytes).hexdigest() == info["metadata_sha256"]
    assert (
        hashlib.sha256(viewer_metadata_bytes).hexdigest()
        == info["viewer_metadata_sha256"]
    )

    readme_bytes = (output / "README.md").read_bytes()
    assert readme_bytes == card.read_bytes()
    assert hashlib.sha256(readme_bytes).hexdigest() == info["readme_sha256"]

    rows = [
        json.loads(line)
        for line in manifest_bytes.decode("utf-8").splitlines()
        if line
    ]
    viewer_rows = [
        json.loads(line)
        for line in viewer_metadata_bytes.decode("utf-8").splitlines()
        if line
    ]
    assert len(rows) == 72
    assert len(viewer_rows) == len(rows)
    assert sum(row["role"] == "calibration" for row in rows) == 24
    assert sum(row["role"] == "evaluation" for row in rows) == 48
    assert all(row["critical_field_count"] == 6 for row in rows)

    for canonical, viewer in zip(rows, viewer_rows, strict=True):
        assert viewer["file_name"] == Path(canonical["file_name"]).name
        restored = dict(viewer)
        restored["file_name"] = canonical["file_name"]
        assert restored == canonical

    images = sorted((output / "images").glob("*.png"))
    assert len(images) == 72

    by_name = {path.name: path for path in images}
    for row in rows:
        filename = Path(row["file_name"]).name
        image = by_name[filename]
        assert hashlib.sha256(image.read_bytes()).hexdigest() == row["image_sha256"]

    with pytest.raises(FileExistsError, match="output directory must be empty"):
        prepare(split_path=split, output=output, card_path=card)


def test_hf_dataset_card_preserves_frozen_result_boundary() -> None:
    card = (ROOT / "huggingface" / "dataset" / "README.md").read_text(
        encoding="utf-8"
    )
    assert "48-document / 288-critical-field final evaluation split" in card
    assert "0/288 observed errors" in card
    assert "209/288 fields" in card
    assert "0/209 observed errors" in card
    assert "does **not** establish a safety benefit from gating" in card
    assert "3a3fcdf1e3e045c0b6f8b334457d1e22dbd247a6a556e08235f808143abf5cec" in card
    assert "JPEG round-trip" in card
    assert "win32:AMD64" in card
    assert "External datasets used in the paper are not redistributed here." in card
