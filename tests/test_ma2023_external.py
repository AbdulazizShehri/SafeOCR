from __future__ import annotations

import json
import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

from safeocr.ma2023 import laboratory_rows, load_ma2023_annotations

_ROOT = Path(__file__).resolve().parents[1]
_RUNNER = _ROOT / "scripts" / "run_ma2023_external_ocr.py"
_SCORER = _ROOT / "scripts" / "score_ma2023_external_verifier.py"
_PROTOCOL = _ROOT / "paper" / "MA2023_EXTERNAL_COMPONENT_PROTOCOL.md"


def test_runner_has_no_annotation_access() -> None:
    source = _RUNNER.read_text(encoding="utf-8")
    lowered = source.lower()
    assert "labels_src" not in lowered
    assert "annotation_source_opened" in source
    assert '"annotation_source_opened": False' in source
    assert '"tuning_performed": False' in source


def test_scorer_requires_clean_ocr_attestation_before_labels() -> None:
    source = _SCORER.read_text(encoding="utf-8")
    attestation = source.index('metadata.get("annotation_source_opened")')
    assert attestation < source.rindex("load_ma2023_annotations")
    assert 'metadata.get("working_tree_dirty")' in source
    assert 'metadata.get("tuning_performed")' in source
    assert "Ma2023 scoring requires a clean exact-head working tree" in source


def test_scorer_normalizes_jpeg_source_to_png_before_crop() -> None:
    source = _SCORER.read_text(encoding="utf-8")
    assert 'opened.convert("RGB").save(buffer, format="PNG")' in source
    assert "image_bytes = _source_png_bytes(image_path)" in source
    assert "result = _rebind_to_source_png(result, image_bytes)" in source
    assert "page_sha256=hashlib.sha256(png_bytes).hexdigest()" in source


def test_protocol_preserves_component_only_claim_boundary() -> None:
    text = _PROTOCOL.read_text(encoding="utf-8")
    assert "FROZEN BEFORE VERIFIER OUTCOME INSPECTION" in text
    assert "oracle-localised verifier component evaluation" in text
    assert "not an end-to-end extraction evaluation" in text
    assert "does not estimate full VERIFIED_AUTO coverage" in text


def test_resume_requires_exact_matching_run_state(tmp_path: Path) -> None:
    namespace = runpy.run_path(str(_RUNNER))
    prepare_resume_state = cast(
        Callable[..., set[str]],
        namespace["_prepare_resume_state"],
    )
    output = tmp_path / "ocr"
    expected = {
        "schema_version": 1,
        "dataset": "Ma2023-public-laboratory-reports",
        "git_head": "a" * 40,
    }
    assert prepare_resume_state(output, expected_state=expected) == set()
    (output / "example.json").write_text("{}\n", encoding="utf-8")

    assert prepare_resume_state(output, expected_state=expected) == {"example"}

    changed = dict(expected)
    changed["git_head"] = "b" * 40
    with pytest.raises(RuntimeError, match="exact run state"):
        prepare_resume_state(output, expected_state=changed)


def test_annotation_loader_and_rows(tmp_path: Path) -> None:
    payload: list[dict[str, object]] = []
    for index in range(238):
        payload.append(
            {
                "filename": f"scan_{index}.jpg",
                "annotations": [
                    {
                        "class": "text",
                        "table_no": "2",
                        "cell_row": "2",
                        "cell_line": "2",
                        "text": "Glucose",
                        "x": 10,
                        "y": 20,
                        "width": 50,
                        "height": 10,
                    },
                    {
                        "class": "text",
                        "table_no": "2",
                        "cell_row": "2",
                        "cell_line": "3",
                        "text": "90",
                        "x": 80,
                        "y": 20,
                        "width": 20,
                        "height": 10,
                    },
                ],
            }
        )
    path = tmp_path / "labels.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    documents = load_ma2023_annotations(path)
    assert len(documents) == 238
    rows = laboratory_rows(documents[0])
    assert len(rows) == 1
    assert rows[0][2].text == "Glucose"
    assert rows[0][3].text == "90"
