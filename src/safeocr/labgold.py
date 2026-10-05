from __future__ import annotations

import hashlib
import io
import json
import math
import platform
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum
from typing import Final, TypeVar

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, features
from PIL import __version__ as PILLOW_VERSION

from safeocr.contracts import BoundingBox

T = TypeVar("T")


class LabTemplate(StrEnum):
    """Controlled SafeOCR-LabGold report layouts."""

    CLASSIC = "classic"
    COMPACT = "compact"
    GRID = "grid"


@dataclass(frozen=True, slots=True)
class SyntheticLabRow:
    row_id: str
    analyte_text: str
    value_text: str
    unit_text: str
    reference_range_text: str
    flag_text: str


@dataclass(frozen=True, slots=True)
class FakeLabRecord:
    seed: int
    patient_id: str
    patient_name: str
    report_id: str
    collected_at: str
    rows: tuple[SyntheticLabRow, ...]


@dataclass(frozen=True, slots=True)
class TruthRegion:
    role: str
    row_id: str | None
    text: str
    box: BoundingBox


@dataclass(frozen=True, slots=True)
class RenderedLabReport:
    record: FakeLabRecord
    template: LabTemplate
    width_px: int
    height_px: int
    png_bytes: bytes
    page_sha256: str
    regions: tuple[TruthRegion, ...]

    def to_manifest_json(self) -> str:
        return _manifest_json(
            record=self.record,
            template=self.template,
            width_px=self.width_px,
            height_px=self.height_px,
            page_sha256=self.page_sha256,
            regions=self.regions,
        )


@dataclass(frozen=True, slots=True)
class CorruptionProfile:
    seed: int
    blur_radius: float
    contrast_factor: float
    jpeg_quality: int


@dataclass(frozen=True, slots=True)
class CorruptedLabReport:
    record: FakeLabRecord
    template: LabTemplate
    width_px: int
    height_px: int
    png_bytes: bytes
    page_sha256: str
    source_page_sha256: str
    regions: tuple[TruthRegion, ...]
    profile: CorruptionProfile

    def to_manifest_json(self) -> str:
        payload = json.loads(
            _manifest_json(
                record=self.record,
                template=self.template,
                width_px=self.width_px,
                height_px=self.height_px,
                page_sha256=self.page_sha256,
                regions=self.regions,
            )
        )
        payload["source_page_sha256"] = self.source_page_sha256
        payload["corruption"] = {
            "blur_radius": self.profile.blur_radius,
            "contrast_factor": self.profile.contrast_factor,
            "jpeg_quality": self.profile.jpeg_quality,
            "seed": self.profile.seed,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


_ANALYTE_OPTIONS: Final[
    tuple[tuple[str, str, str, tuple[tuple[str, str], ...]], ...]
] = (
    ("Sodium", "mmol/L", "135-145", (("132", "L"), ("139", ""), ("147", "H"))),
    ("Potassium", "mmol/L", "3.5-5.1", (("3.4", "L"), ("4.2", ""), ("6.8", "H"))),
    ("Hemoglobin", "g/dL", "12.0-17.0", (("10.8", "L"), ("14.2", ""), ("17.9", "H"))),
    ("Creatinine", "mg/dL", "0.6-1.3", (("0.8", ""), ("1.1", ""), ("2.4", "H"))),
    ("Glucose", "mg/dL", "70-110", (("72", ""), ("104", ""), ("218", "H"))),
    ("CRP", "mg/L", "0.0-5.0", (("<0.5", ""), ("2.1", ""), ("18.6", "H"))),
)

_PAGE_SIZE: Final[tuple[int, int]] = (1000, 760)
_LABGOLD_SCHEMA_VERSION: Final[str] = "labgold-v1"
_TEMPLATE_VERSION: Final[str] = "1"


def _digest_int(seed: int, label: str) -> int:
    raw = hashlib.sha256(f"{seed}:{label}".encode()).digest()
    return int.from_bytes(raw[:8], byteorder="big", signed=False)


def _pick(seed: int, label: str, options: tuple[T, ...]) -> T:
    return options[_digest_int(seed, label) % len(options)]


def generate_fake_lab_record(seed: int) -> FakeLabRecord:
    """Generate deterministic, visibly synthetic laboratory truth."""

    if type(seed) is not int:
        raise ValueError("seed must be an int")

    patient_number = _digest_int(seed, "patient-id") % 100_000_000
    patient_name_number = _digest_int(seed, "patient-name") % 100_000
    report_number = _digest_int(seed, "report-id") % 100_000_000
    day_offset = _digest_int(seed, "collected-at") % 365
    collected = date(2026, 1, 1) + timedelta(days=day_offset)

    rows: list[SyntheticLabRow] = []
    for index, (analyte, unit, reference_range, value_options) in enumerate(
        _ANALYTE_OPTIONS, start=1
    ):
        value, flag = _pick(seed, f"row-{index}", value_options)
        rows.append(
            SyntheticLabRow(
                row_id=f"row-{index:02d}",
                analyte_text=analyte,
                value_text=value,
                unit_text=unit,
                reference_range_text=reference_range,
                flag_text=flag,
            )
        )

    return FakeLabRecord(
        seed=seed,
        patient_id=f"SAFE-{patient_number:08d}",
        patient_name=f"Synthetic Patient {patient_name_number:05d}",
        report_id=f"SAFE-RPT-{report_number:08d}",
        collected_at=f"{collected.isoformat()}T08:30:00Z",
        rows=tuple(rows),
    )


def _draw_truth_text(
    draw: ImageDraw.ImageDraw,
    regions: list[TruthRegion],
    *,
    xy: tuple[int, int],
    text: str,
    role: str,
    row_id: str | None,
    font: ImageFont.BaseImageFont,
) -> None:
    if not text:
        return

    raw_box = draw.textbbox(xy, text, font=font)
    box = BoundingBox(
        x1=math.floor(raw_box[0]),
        y1=math.floor(raw_box[1]),
        x2=math.ceil(raw_box[2]),
        y2=math.ceil(raw_box[3]),
    )
    draw.text(xy, text, fill="black", font=font)
    regions.append(TruthRegion(role=role, row_id=row_id, text=text, box=box))


def _draw_header(
    draw: ImageDraw.ImageDraw,
    record: FakeLabRecord,
    regions: list[TruthRegion],
    *,
    title_font: ImageFont.BaseImageFont,
    text_font: ImageFont.BaseImageFont,
    compact: bool,
) -> int:
    draw.text((40, 30), "SAFEOCR SYNTHETIC LAB REPORT", fill="black", font=title_font)
    y = 90 if not compact else 78
    line_gap = 34 if not compact else 28

    _draw_truth_text(
        draw,
        regions,
        xy=(40, y),
        text=record.patient_name,
        role="patient_name",
        row_id=None,
        font=text_font,
    )
    _draw_truth_text(
        draw,
        regions,
        xy=(420, y),
        text=record.patient_id,
        role="patient_id",
        row_id=None,
        font=text_font,
    )
    y += line_gap
    _draw_truth_text(
        draw,
        regions,
        xy=(40, y),
        text=record.report_id,
        role="report_id",
        row_id=None,
        font=text_font,
    )
    _draw_truth_text(
        draw,
        regions,
        xy=(420, y),
        text=record.collected_at,
        role="collected_at",
        row_id=None,
        font=text_font,
    )
    return y + line_gap + 20


def _render_rows(
    draw: ImageDraw.ImageDraw,
    record: FakeLabRecord,
    regions: list[TruthRegion],
    *,
    template: LabTemplate,
    start_y: int,
    font: ImageFont.BaseImageFont,
) -> None:
    if template is LabTemplate.CLASSIC:
        columns = (40, 330, 480, 620, 820)
        row_gap = 58
    elif template is LabTemplate.COMPACT:
        columns = (40, 300, 430, 555, 790)
        row_gap = 46
    else:
        columns = (55, 330, 480, 620, 815)
        row_gap = 56

    headers = ("Test", "Result", "Units", "Reference", "Flag")
    for x, header in zip(columns, headers, strict=True):
        draw.text((x, start_y), header, fill="black", font=font)

    row_y = start_y + 44
    for row in record.rows:
        if template is LabTemplate.GRID:
            draw.rectangle((35, row_y - 10, 945, row_y + 36), outline="black", width=1)
            for x in columns[1:]:
                draw.line((x - 15, row_y - 10, x - 15, row_y + 36), fill="black", width=1)

        values = (
            ("analyte", row.analyte_text),
            ("value", row.value_text),
            ("unit", row.unit_text),
            ("reference_range", row.reference_range_text),
            ("flag", row.flag_text),
        )
        for x, (role, text) in zip(columns, values, strict=True):
            _draw_truth_text(
                draw,
                regions,
                xy=(x, row_y),
                text=text,
                role=role,
                row_id=row.row_id,
                font=font,
            )
        row_y += row_gap


def render_lab_report(record: FakeLabRecord, template: LabTemplate) -> RenderedLabReport:
    """Render one controlled synthetic laboratory report and exact truth regions."""

    width, height = _PAGE_SIZE
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default(size=28 if template is not LabTemplate.COMPACT else 24)
    text_font = ImageFont.load_default(size=20 if template is not LabTemplate.COMPACT else 17)

    regions: list[TruthRegion] = []
    start_y = _draw_header(
        draw,
        record,
        regions,
        title_font=title_font,
        text_font=text_font,
        compact=template is LabTemplate.COMPACT,
    )

    if template is LabTemplate.CLASSIC:
        draw.line((40, start_y - 12, 950, start_y - 12), fill="black", width=2)
    elif template is LabTemplate.COMPACT:
        draw.rectangle((30, 20, 970, 710), outline="black", width=1)
    else:
        draw.rectangle((25, start_y - 20, 960, 690), outline="black", width=2)

    _render_rows(
        draw,
        record,
        regions,
        template=template,
        start_y=start_y,
        font=text_font,
    )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=False, compress_level=9)
    png_bytes = buffer.getvalue()
    page_sha256 = hashlib.sha256(png_bytes).hexdigest()

    return RenderedLabReport(
        record=record,
        template=template,
        width_px=width,
        height_px=height,
        png_bytes=png_bytes,
        page_sha256=page_sha256,
        regions=tuple(regions),
    )


def _corruption_profile(seed: int) -> CorruptionProfile:
    if type(seed) is not int:
        raise ValueError("seed must be an int")

    blur_radius = _pick(seed, "blur", (0.6, 0.9, 1.2))
    contrast_factor = _pick(seed, "contrast", (0.72, 0.84, 1.12))
    jpeg_quality = _pick(seed, "jpeg", (42, 55, 68))
    return CorruptionProfile(
        seed=seed,
        blur_radius=blur_radius,
        contrast_factor=contrast_factor,
        jpeg_quality=jpeg_quality,
    )


def apply_corruption(rendered: RenderedLabReport, *, seed: int) -> CorruptedLabReport:
    """Apply deterministic geometry-preserving document degradation."""

    profile = _corruption_profile(seed)
    with Image.open(io.BytesIO(rendered.png_bytes)) as opened:
        image = opened.convert("RGB")

    image = ImageEnhance.Contrast(image).enhance(profile.contrast_factor)
    image = image.filter(ImageFilter.GaussianBlur(radius=profile.blur_radius))

    jpeg_buffer = io.BytesIO()
    image.save(
        jpeg_buffer,
        format="JPEG",
        quality=profile.jpeg_quality,
        optimize=False,
        progressive=False,
    )
    jpeg_buffer.seek(0)
    with Image.open(jpeg_buffer) as jpeg_image:
        degraded = jpeg_image.convert("RGB")

    png_buffer = io.BytesIO()
    degraded.save(png_buffer, format="PNG", optimize=False, compress_level=9)
    png_bytes = png_buffer.getvalue()

    return CorruptedLabReport(
        record=rendered.record,
        template=rendered.template,
        width_px=rendered.width_px,
        height_px=rendered.height_px,
        png_bytes=png_bytes,
        page_sha256=hashlib.sha256(png_bytes).hexdigest(),
        source_page_sha256=rendered.page_sha256,
        regions=rendered.regions,
        profile=profile,
    )




def _feature_version(name: str) -> str:
    value = features.version(name)
    return value if value is not None else "unavailable"


def _renderer_fingerprint() -> dict[str, str]:
    return {
        "freetype2_version": _feature_version("freetype2"),
        "jpeg_version": _feature_version("jpg"),
        "pillow_version": PILLOW_VERSION,
        "platform": f"{sys.platform}:{platform.machine()}",
        "python_version": platform.python_version(),
        "zlib_version": _feature_version("zlib"),
    }

def _manifest_json(
    *,
    record: FakeLabRecord,
    template: LabTemplate,
    width_px: int,
    height_px: int,
    page_sha256: str,
    regions: tuple[TruthRegion, ...],
) -> str:
    payload = {
        "height_px": height_px,
        "renderer": _renderer_fingerprint(),
        "schema_version": _LABGOLD_SCHEMA_VERSION,
        "template_version": _TEMPLATE_VERSION,
        "page_sha256": page_sha256,
        "record": {
            "collected_at": record.collected_at,
            "patient_id": record.patient_id,
            "patient_name": record.patient_name,
            "report_id": record.report_id,
            "rows": [
                {
                    "analyte_text": row.analyte_text,
                    "flag_text": row.flag_text,
                    "reference_range_text": row.reference_range_text,
                    "row_id": row.row_id,
                    "unit_text": row.unit_text,
                    "value_text": row.value_text,
                }
                for row in record.rows
            ],
            "seed": record.seed,
        },
        "regions": [
            {
                "box": {
                    "x1": region.box.x1,
                    "x2": region.box.x2,
                    "y1": region.box.y1,
                    "y2": region.box.y2,
                },
                "role": region.role,
                "row_id": region.row_id,
                "text": region.text,
            }
            for region in regions
        ],
        "template": template.value,
        "width_px": width_px,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
