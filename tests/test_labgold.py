from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from safeocr.labgold import (
    LabTemplate,
    apply_corruption,
    generate_fake_lab_record,
    render_lab_report,
)


def test_same_seed_produces_equal_typed_truth() -> None:
    assert generate_fake_lab_record(42) == generate_fake_lab_record(42)


def test_generated_identity_is_visibly_synthetic() -> None:
    record = generate_fake_lab_record(7)

    assert record.patient_id.startswith("SAFE-")
    assert record.patient_name.startswith("Synthetic Patient ")
    assert record.report_id.startswith("SAFE-RPT-")


def test_all_templates_render_valid_pngs() -> None:
    record = generate_fake_lab_record(11)

    for template in LabTemplate:
        rendered = render_lab_report(record, template)
        image = Image.open(io.BytesIO(rendered.png_bytes))

        assert image.format == "PNG"
        assert image.size == (rendered.width_px, rendered.height_px)
        assert rendered.template is template


def test_same_record_and_template_render_identically() -> None:
    record = generate_fake_lab_record(19)

    for template in LabTemplate:
        first = render_lab_report(record, template)
        second = render_lab_report(record, template)

        assert first.png_bytes == second.png_bytes
        assert first.page_sha256 == second.page_sha256
        assert first.to_manifest_json() == second.to_manifest_json()


def test_templates_produce_distinct_page_bytes() -> None:
    record = generate_fake_lab_record(23)
    hashes = {render_lab_report(record, template).page_sha256 for template in LabTemplate}

    assert len(hashes) == len(LabTemplate)


def test_every_lab_row_has_required_truth_regions() -> None:
    record = generate_fake_lab_record(29)

    for template in LabTemplate:
        rendered = render_lab_report(record, template)
        for row in record.rows:
            roles = {region.role for region in rendered.regions if region.row_id == row.row_id}
            assert {"analyte", "value", "unit", "reference_range"} <= roles


def test_truth_regions_are_non_empty_and_inside_page() -> None:
    record = generate_fake_lab_record(31)

    for template in LabTemplate:
        rendered = render_lab_report(record, template)
        assert rendered.regions
        for region in rendered.regions:
            assert region.text.strip()
            assert 0 <= region.box.x1 < region.box.x2 <= rendered.width_px
            assert 0 <= region.box.y1 < region.box.y2 <= rendered.height_px


def test_identity_header_regions_are_annotated() -> None:
    record = generate_fake_lab_record(37)

    for template in LabTemplate:
        rendered = render_lab_report(record, template)
        roles = {region.role for region in rendered.regions if region.row_id is None}
        assert {"patient_id", "patient_name", "report_id"} <= roles


def test_manifest_serialization_is_deterministic() -> None:
    rendered = render_lab_report(generate_fake_lab_record(41), LabTemplate.CLASSIC)

    first = rendered.to_manifest_json()
    second = rendered.to_manifest_json()
    payload = json.loads(first)

    assert first == second
    assert payload["schema_version"] == "labgold-v1"
    assert payload["template"] == "classic"
    assert payload["template_version"] == "1"
    assert payload["renderer"]["pillow_version"] == "12.3.0"
    assert payload["renderer"]["freetype2_version"]
    assert payload["renderer"]["jpeg_version"]
    assert payload["renderer"]["zlib_version"]
    assert payload["renderer"]["python_version"]
    assert payload["renderer"]["platform"]
    assert payload["record"]["patient_id"].startswith("SAFE-")
    assert len(payload["regions"]) == len(rendered.regions)


def test_corruption_is_seeded_and_preserves_truth_geometry() -> None:
    rendered = render_lab_report(generate_fake_lab_record(43), LabTemplate.GRID)

    first = apply_corruption(rendered, seed=1001)
    second = apply_corruption(rendered, seed=1001)

    assert first.png_bytes == second.png_bytes
    assert first.profile == second.profile
    assert first.png_bytes != rendered.png_bytes
    assert first.width_px == rendered.width_px
    assert first.height_px == rendered.height_px
    assert first.regions == rendered.regions


def test_corruption_manifest_is_deterministic() -> None:
    rendered = render_lab_report(generate_fake_lab_record(47), LabTemplate.COMPACT)
    corrupted = apply_corruption(rendered, seed=2002)

    assert corrupted.to_manifest_json() == corrupted.to_manifest_json()
    payload = json.loads(corrupted.to_manifest_json())
    assert payload["corruption"]["seed"] == 2002
    assert payload["source_page_sha256"] == rendered.page_sha256


@pytest.mark.parametrize("template", list(LabTemplate))
def test_render_is_deterministic_across_fresh_processes(template: LabTemplate) -> None:
    local_hash = render_lab_report(generate_fake_lab_record(53), template).page_sha256
    script = (
        "from safeocr.labgold import LabTemplate, generate_fake_lab_record, "
        "render_lab_report; "
        f"print(render_lab_report(generate_fake_lab_record(53), "
        f"LabTemplate({template.value!r})).page_sha256)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout.strip() == local_hash


GOLDEN_PATH = Path(__file__).parents[1] / "benchmarks" / "labgold" / "golden-v1.json"


def test_canonical_golden_hashes_detect_renderer_drift() -> None:
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    record = generate_fake_lab_record(golden["record_seed"])
    rendered = {template: render_lab_report(record, template) for template in LabTemplate}
    current_renderer = json.loads(
        rendered[LabTemplate.CLASSIC].to_manifest_json()
    )["renderer"]

    canonical = golden["renderer"]
    current_python = ".".join(current_renderer["python_version"].split(".")[:2])
    canonical_python = ".".join(canonical["python_version"].split(".")[:2])
    if (
        current_renderer["platform"] != canonical["platform"]
        or current_python != canonical_python
    ):
        pytest.skip("golden is bound to the canonical platform and Python minor")

    assert current_renderer == canonical, (
        "renderer drift detected on the canonical runtime; review before regenerating golden"
    )
    assert {
        template.value: report.page_sha256 for template, report in rendered.items()
    } == golden["template_hashes"]

    corrupted = apply_corruption(
        rendered[LabTemplate.GRID], seed=golden["corruption_seed"]
    )
    assert corrupted.page_sha256 == golden["corrupted_grid_sha256"]
    corrupted_manifest = json.loads(corrupted.to_manifest_json())
    assert corrupted_manifest["corruption"] == golden["corruption_profile"]
