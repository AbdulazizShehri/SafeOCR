from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from safeocr.contracts import BoundingBox


@dataclass(frozen=True, slots=True)
class Ma2023Region:
    table_no: int
    row_no: int
    column_no: int
    text: str
    box: BoundingBox


@dataclass(frozen=True, slots=True)
class Ma2023Document:
    filename: str
    regions: tuple[Ma2023Region, ...]


def _number(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    return float(value)


def _positive_box(raw: dict[str, object]) -> BoundingBox:
    x = _number(raw["x"], field="x")
    y = _number(raw["y"], field="y")
    width = _number(raw["width"], field="width")
    height = _number(raw["height"], field="height")
    x1 = max(0, math.floor(x))
    y1 = max(0, math.floor(y))
    x2 = max(x1 + 1, math.ceil(x + width))
    y2 = max(y1 + 1, math.ceil(y + height))
    return BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)


def load_ma2023_annotations(path: Path) -> tuple[Ma2023Document, ...]:
    raw_object: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_object, list):
        raise ValueError("Ma2023 annotations must be a JSON list")
    raw = cast(list[object], raw_object)

    documents: list[Ma2023Document] = []
    for raw_item in raw:
        if not isinstance(raw_item, dict):
            raise ValueError("Ma2023 document entries must be objects")
        item = cast(dict[str, object], raw_item)
        filename = item.get("filename")
        raw_annotations = item.get("annotations")
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Ma2023 filename must be non-empty")
        if not isinstance(raw_annotations, list):
            raise ValueError("Ma2023 annotations must be a list")
        annotations = cast(list[object], raw_annotations)

        regions: list[Ma2023Region] = []
        for raw_annotation in annotations:
            if not isinstance(raw_annotation, dict):
                raise ValueError("Ma2023 annotation entries must be objects")
            annotation = cast(dict[str, object], raw_annotation)
            if annotation.get("class") != "text":
                continue
            text = annotation.get("text")
            if not isinstance(text, str):
                raise ValueError("Ma2023 annotation text must be a string")
            regions.append(
                Ma2023Region(
                    table_no=int(str(annotation["table_no"])),
                    row_no=int(str(annotation["cell_row"])),
                    column_no=int(str(annotation["cell_line"])),
                    text=text.strip(),
                    box=_positive_box(annotation),
                )
            )
        documents.append(Ma2023Document(filename=filename, regions=tuple(regions)))

    if len(documents) != 238:
        raise ValueError("expected exactly 238 Ma2023 images")
    return tuple(documents)


def laboratory_rows(
    document: Ma2023Document,
) -> tuple[dict[int, Ma2023Region], ...]:
    rows: dict[int, dict[int, Ma2023Region]] = {}
    for region in document.regions:
        if region.table_no != 2 or region.row_no == 1:
            continue
        row = rows.setdefault(region.row_no, {})
        if region.column_no in row:
            raise ValueError(
                f"duplicate Ma2023 cell for {document.filename} "
                f"row={region.row_no} column={region.column_no}"
            )
        row[region.column_no] = region
    return tuple(rows[index] for index in sorted(rows))
