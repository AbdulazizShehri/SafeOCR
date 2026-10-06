from __future__ import annotations

import base64
import hashlib
import html
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from PIL import Image

from safeocr.contracts import BoundingBox, DecisionState


@dataclass(frozen=True, slots=True)
class EvidenceReportField:
    field_id: str
    analyte_text: str
    value_text: str
    unit_text: str | None
    criticality: str
    state: DecisionState
    failed_gates: tuple[str, ...]
    policy_version: str
    page_sha256: str
    source_box: BoundingBox
    crop_png_bytes: bytes
    evidence_record: dict[str, object]

    def __post_init__(self) -> None:
        if not self.field_id.strip():
            raise ValueError("field_id must be non-empty")
        if not self.analyte_text.strip() or not self.value_text.strip():
            raise ValueError("report field text must be non-empty")
        if self.unit_text is not None and not self.unit_text.strip():
            raise ValueError("unit_text must be non-empty when present")
        if len(self.page_sha256) != 64:
            raise ValueError("page_sha256 must be a SHA-256 hex digest")
        if not self.crop_png_bytes:
            raise ValueError("crop_png_bytes must be non-empty")


def _mapping(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return cast(dict[str, object], value)


def _string(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _optional_string(value: object, *, name: str) -> str | None:
    if value is None:
        return None
    return _string(value, name=name)


def _integer(value: object, *, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    return value


def _crop_source(
    page_png_bytes: bytes,
    *,
    page_sha256: str,
    box: BoundingBox,
    padding_px: int = 8,
) -> bytes:
    if hashlib.sha256(page_png_bytes).hexdigest() != page_sha256:
        raise ValueError("source page bytes do not match evidence page_sha256")

    with Image.open(io.BytesIO(page_png_bytes)) as image:
        image.load()
        left = max(0, box.x1 - padding_px)
        top = max(0, box.y1 - padding_px)
        right = min(image.width, box.x2 + padding_px)
        bottom = min(image.height, box.y2 + padding_px)
        crop = image.crop((left, top, right, bottom)).convert("RGB")
        output = io.BytesIO()
        crop.save(output, format="PNG")
    return output.getvalue()


def field_from_trace_json(
    trace: dict[str, object],
    *,
    page_png_bytes: bytes,
) -> EvidenceReportField:
    evidence = _mapping(trace.get("evidence_record"), name="evidence_record")
    decision = _mapping(evidence.get("decision"), name="decision")
    field = _mapping(evidence.get("field"), name="field")
    spans_raw = field.get("source_spans")
    if not isinstance(spans_raw, list) or not spans_raw:
        raise ValueError("report field requires at least one source span")

    boxes: list[BoundingBox] = []
    page_sha256: str | None = None
    for raw_span in cast(list[object], spans_raw):
        span = _mapping(raw_span, name="source_span")
        box_raw = _mapping(span.get("box"), name="source_span.box")
        page_raw = _mapping(span.get("page"), name="source_span.page")
        current_sha = _string(page_raw.get("page_sha256"), name="page_sha256")
        if page_sha256 is None:
            page_sha256 = current_sha
        elif current_sha != page_sha256:
            raise ValueError("one report field cannot span multiple source pages")
        boxes.append(
            BoundingBox(
                _integer(box_raw.get("x1"), name="x1"),
                _integer(box_raw.get("y1"), name="y1"),
                _integer(box_raw.get("x2"), name="x2"),
                _integer(box_raw.get("y2"), name="y2"),
            )
        )

    assert page_sha256 is not None
    union = BoundingBox(
        min(item.x1 for item in boxes),
        min(item.y1 for item in boxes),
        max(item.x2 for item in boxes),
        max(item.y2 for item in boxes),
    )
    crop = _crop_source(
        page_png_bytes,
        page_sha256=page_sha256,
        box=union,
    )

    failed_raw = decision.get("failed_gates")
    if not isinstance(failed_raw, list):
        raise ValueError("decision.failed_gates must be a list")
    failed_gates = tuple(
        _string(item, name="failed_gate") for item in cast(list[object], failed_raw)
    )
    state = DecisionState(_string(decision.get("state"), name="decision.state"))
    field_id_source = json.dumps(
        {
            "page_sha256": page_sha256,
            "box": [union.x1, union.y1, union.x2, union.y2],
            "analyte": field.get("analyte_text"),
            "value": field.get("value_text"),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    field_id = hashlib.sha256(field_id_source).hexdigest()[:24]

    return EvidenceReportField(
        field_id=field_id,
        analyte_text=_string(field.get("analyte_text"), name="analyte_text"),
        value_text=_string(field.get("value_text"), name="value_text"),
        unit_text=_optional_string(field.get("unit_text"), name="unit_text"),
        criticality=_string(decision.get("criticality"), name="criticality"),
        state=state,
        failed_gates=failed_gates,
        policy_version=_string(evidence.get("policy_version"), name="policy_version"),
        page_sha256=page_sha256,
        source_box=union,
        crop_png_bytes=crop,
        evidence_record=evidence,
    )


def explanation(field: EvidenceReportField) -> str:
    if field.state is DecisionState.VERIFIED_AUTO:
        return "Verified automatically because all required verification gates passed."
    gates = ", ".join(field.failed_gates) if field.failed_gates else "unspecified gate"
    if field.state is DecisionState.REVIEW_REQUIRED:
        return f"Review required because verification gate(s) failed: {gates}."
    return f"Abstained because verification gate(s) failed: {gates}."


def report_json(fields: tuple[EvidenceReportField, ...]) -> str:
    ordered = sorted(
        fields,
        key=lambda item: (item.field_id, item.state.value, item.failed_gates),
    )
    payload = {
        "schema_version": 1,
        "field_count": len(ordered),
        "fields": [
            {
                "field_id": item.field_id,
                "analyte_text": item.analyte_text,
                "value_text": item.value_text,
                "unit_text": item.unit_text,
                "criticality": item.criticality,
                "state": item.state.value,
                "failed_gates": list(item.failed_gates),
                "explanation": explanation(item),
                "policy_version": item.policy_version,
                "page_sha256": item.page_sha256,
                "source_box": {
                    "x1": item.source_box.x1,
                    "y1": item.source_box.y1,
                    "x2": item.source_box.x2,
                    "y2": item.source_box.y2,
                },
                "crop_sha256": hashlib.sha256(item.crop_png_bytes).hexdigest(),
                "evidence_record": item.evidence_record,
            }
            for item in ordered
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_static_html(fields: tuple[EvidenceReportField, ...], *, title: str) -> str:
    ordered = sorted(
        fields,
        key=lambda item: (item.field_id, item.state.value, item.failed_gates),
    )
    cards: list[str] = []
    for item in ordered:
        crop_b64 = base64.b64encode(item.crop_png_bytes).decode("ascii")
        unit = "" if item.unit_text is None else f" {html.escape(item.unit_text)}"
        failed = (
            "None"
            if not item.failed_gates
            else ", ".join(html.escape(gate) for gate in item.failed_gates)
        )
        cards.append(
            "<article class=\"field\">"
            f"<h2>{html.escape(item.analyte_text)}</h2>"
            f"<p class=\"value\">{html.escape(item.value_text)}{unit}</p>"
            f"<p><strong>Decision:</strong> {html.escape(item.state.value)}</p>"
            f"<p><strong>Why:</strong> {html.escape(explanation(item))}</p>"
            f"<p><strong>Failed gates:</strong> {failed}</p>"
            f"<p><strong>Policy:</strong> {html.escape(item.policy_version)}</p>"
            f"<img alt=\"Source crop for {html.escape(item.analyte_text)}\" "
            f"src=\"data:image/png;base64,{crop_b64}\">"
            f"<details><summary>Evidence identity</summary>"
            f"<code>{html.escape(item.page_sha256)} / {html.escape(item.field_id)}</code>"
            "</details></article>"
        )

    body = "".join(cards) if cards else "<p>No critical fields.</p>"
    safe_title = html.escape(title)
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<title>{safe_title}</title>"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<style>"
        "body{font-family:system-ui,sans-serif;max-width:960px;margin:2rem auto;"
        "padding:0 1rem;line-height:1.45}header{border-bottom:1px solid #aaa;"
        "margin-bottom:1.5rem}.field{border:1px solid #bbb;border-radius:10px;"
        "padding:1rem;margin:1rem 0}.value{font-size:1.4rem;font-weight:700}"
        "img{max-width:100%;height:auto;border:1px solid #ddd}"
        "code{overflow-wrap:anywhere}</style></head><body>"
        f"<header><h1>{safe_title}</h1>"
        "<p>Static evidence report. No clinical-use claim.</p></header>"
        f"{body}</body></html>\n"
    )


def write_report(
    fields: tuple[EvidenceReportField, ...],
    *,
    html_path: Path,
    json_path: Path,
    title: str,
) -> None:
    html_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render_static_html(fields, title=title), encoding="utf-8", newline="\n")
    json_path.write_text(report_json(fields), encoding="utf-8", newline="\n")
