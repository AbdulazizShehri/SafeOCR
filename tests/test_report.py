from __future__ import annotations

import hashlib
import io
import json

import pytest
from PIL import Image

from safeocr.contracts import BoundingBox, DecisionState
from safeocr.report import (
    EvidenceReportField,
    explanation,
    field_from_trace_json,
    render_static_html,
    report_json,
)


def _page_png() -> bytes:
    image = Image.new("RGB", (200, 120), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _trace(*, state: str = "VERIFIED_AUTO", failed: list[str] | None = None) -> dict[str, object]:
    page = _page_png()
    page_sha = hashlib.sha256(page).hexdigest()
    return {
        "evidence_record": {
            "decision": {
                "criticality": "CRITICAL",
                "failed_gates": [] if failed is None else failed,
                "state": state,
            },
            "field": {
                "analyte_text": "Potassium <unsafe>",
                "value_text": "3.4",
                "unit_text": "mmol/L",
                "source_spans": [
                    {
                        "box": {"x1": 20, "y1": 30, "x2": 90, "y2": 50},
                        "confidence": 0.99,
                        "engine_name": "paddleocr",
                        "engine_version": "3.7.0",
                        "page": {
                            "document_sha256": page_sha,
                            "height_px": 120,
                            "page_index": 0,
                            "page_sha256": page_sha,
                            "width_px": 200,
                        },
                        "text": "Potassium <unsafe>",
                    },
                    {
                        "box": {"x1": 100, "y1": 30, "x2": 130, "y2": 50},
                        "confidence": 0.99,
                        "engine_name": "paddleocr",
                        "engine_version": "3.7.0",
                        "page": {
                            "document_sha256": page_sha,
                            "height_px": 120,
                            "page_index": 0,
                            "page_sha256": page_sha,
                            "width_px": 200,
                        },
                        "text": "3.4",
                    },
                ],
            },
            "policy_version": "f4-v1",
            "signals": {},
        }
    }


def test_field_from_trace_json_binds_source_crop_to_page_hash() -> None:
    page = _page_png()
    field = field_from_trace_json(_trace(), page_png_bytes=page)

    assert field.state is DecisionState.VERIFIED_AUTO
    assert field.source_box.x1 == 20
    assert field.source_box.x2 == 130
    assert field.crop_png_bytes.startswith(b"\x89PNG")


def test_field_from_trace_json_rejects_wrong_page_bytes() -> None:
    wrong = Image.new("RGB", (200, 120), "black")
    buffer = io.BytesIO()
    wrong.save(buffer, format="PNG")

    with pytest.raises(ValueError, match="do not match evidence page_sha256"):
        field_from_trace_json(_trace(), page_png_bytes=buffer.getvalue())


@pytest.mark.parametrize(
    ("state", "failed", "expected"),
    [
        ("VERIFIED_AUTO", [], "all required verification gates passed"),
        ("REVIEW_REQUIRED", ["independent_agreement"], "Review required because"),
        ("ABSTAINED", ["visual_grounded"], "Abstained because"),
    ],
)
def test_explanation_is_state_specific(
    state: str,
    failed: list[str],
    expected: str,
) -> None:
    page = _page_png()
    field = field_from_trace_json(_trace(state=state, failed=failed), page_png_bytes=page)
    assert expected in explanation(field)


def test_report_json_is_deterministic_and_machine_readable() -> None:
    page = _page_png()
    first = field_from_trace_json(_trace(), page_png_bytes=page)
    second = field_from_trace_json(
        _trace(state="REVIEW_REQUIRED", failed=["independent_agreement"]),
        page_png_bytes=page,
    )
    one = report_json((first, second))
    two = report_json((second, first))

    assert one == two
    payload = json.loads(one)
    assert payload["field_count"] == 2
    assert all("crop_sha256" in item for item in payload["fields"])
    assert all("evidence_record" in item for item in payload["fields"])


def test_static_html_embeds_crop_and_escapes_untrusted_ocr_text() -> None:
    page = _page_png()
    field = field_from_trace_json(_trace(), page_png_bytes=page)
    rendered = render_static_html((field,), title="SafeOCR <evidence>")

    assert "data:image/png;base64," in rendered
    assert "Potassium &lt;unsafe&gt;" in rendered
    assert "<unsafe>" not in rendered
    assert "SafeOCR &lt;evidence&gt;" in rendered


def test_empty_report_is_valid_static_html() -> None:
    rendered = render_static_html((), title="SafeOCR")
    assert "<!doctype html>" in rendered
    assert "No critical fields." in rendered


def test_evidence_report_field_rejects_empty_crop() -> None:
    with pytest.raises(ValueError, match="crop_png_bytes"):
        EvidenceReportField(
            field_id="field-1",
            analyte_text="Potassium",
            value_text="3.4",
            unit_text="mmol/L",
            criticality="CRITICAL",
            state=DecisionState.VERIFIED_AUTO,
            failed_gates=(),
            policy_version="f4-v1",
            page_sha256="a" * 64,
            source_box=BoundingBox(0, 0, 10, 10),
            crop_png_bytes=b"",
            evidence_record={},
        )
