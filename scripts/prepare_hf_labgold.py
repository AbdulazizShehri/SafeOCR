from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import cast

from safeocr.labgold import (
    LabTemplate,
    TruthRegion,
    apply_corruption,
    generate_fake_lab_record,
    render_lab_report,
)


def _mapping(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return cast(dict[str, object], value)


def _integer(value: object, *, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    return value


def _optional_integer(value: object, *, name: str) -> int | None:
    if value is None:
        return None
    return _integer(value, name=name)


def _string(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _load_cases(path: Path) -> list[dict[str, object]]:
    root = _mapping(json.loads(path.read_text(encoding="utf-8")), name="split")
    raw_cases = root.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("split.cases must be a list")
    return [
        _mapping(item, name="case")
        for item in cast(list[object], raw_cases)
    ]


def _regions(rendered: tuple[TruthRegion, ...]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for region in rendered:
        output.append(
            {
                "role": region.role,
                "row_id": region.row_id,
                "text": region.text,
                "box": {
                    "x1": region.box.x1,
                    "y1": region.box.y1,
                    "x2": region.box.x2,
                    "y2": region.box.y2,
                },
            }
        )
    return output


def prepare(
    *,
    split_path: Path,
    output: Path,
    card_path: Path | None = None,
) -> None:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("output directory must be empty")
    images = output / "images"
    images.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for case in _load_cases(split_path):
        case_id = _string(case.get("case_id"), name="case_id")
        record_seed = _integer(case.get("record_seed"), name="record_seed")
        corruption_seed = _optional_integer(
            case.get("corruption_seed"), name="corruption_seed"
        )
        template = LabTemplate(_string(case.get("template"), name="template"))
        role = _string(case.get("role"), name="role")

        record = generate_fake_lab_record(record_seed)
        clean = render_lab_report(record, template)
        if corruption_seed is None:
            rendered = clean
            source_page_sha256: str | None = None
        else:
            corrupted = apply_corruption(clean, seed=corruption_seed)
            rendered = corrupted
            source_page_sha256 = corrupted.source_page_sha256

        filename = f"{case_id}.png"
        image_path = images / filename
        image_path.write_bytes(rendered.png_bytes)

        image_sha256 = hashlib.sha256(rendered.png_bytes).hexdigest()
        if image_sha256 != rendered.page_sha256:
            raise RuntimeError(f"page hash mismatch for {case_id}")

        rows.append(
            {
                "case_id": case_id,
                "role": role,
                "record_seed": record_seed,
                "corruption_seed": corruption_seed,
                "template": template.value,
                "file_name": f"images/{filename}",
                "image_sha256": image_sha256,
                "source_page_sha256": source_page_sha256,
                "synthetic_patient_id": record.patient_id,
                "synthetic_report_id": record.report_id,
                "critical_field_count": len(record.rows),
                "regions": _regions(rendered.regions),
            }
        )

    serialized_rows = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )

    manifest_path = output / "manifest.jsonl"
    manifest_path.write_text(
        serialized_rows,
        encoding="utf-8",
        newline="\n",
    )
    metadata_path = output / "metadata.jsonl"
    metadata_path.write_text(
        serialized_rows,
        encoding="utf-8",
        newline="\n",
    )

    viewer_rows: list[dict[str, object]] = []
    for row in rows:
        viewer_row = dict(row)
        file_name = _string(viewer_row.get("file_name"), name="file_name")
        viewer_row["file_name"] = Path(file_name).name
        viewer_rows.append(viewer_row)
    viewer_metadata_path = images / "metadata.jsonl"
    viewer_metadata_path.write_text(
        "".join(
            json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
            for row in viewer_rows
        ),
        encoding="utf-8",
        newline="\n",
    )

    if card_path is not None:
        card_text = card_path.read_text(encoding="utf-8")
        (output / "README.md").write_text(
            card_text,
            encoding="utf-8",
            newline="\n",
        )

    summary = {
        "schema_version": 1,
        "case_count": len(rows),
        "calibration_documents": sum(
            row["role"] == "calibration" for row in rows
        ),
        "evaluation_documents": sum(
            row["role"] == "evaluation" for row in rows
        ),
        "critical_fields_per_document": 6,
        "manifest_sha256": hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest(),
        "metadata_sha256": hashlib.sha256(
            metadata_path.read_bytes()
        ).hexdigest(),
        "viewer_metadata_sha256": hashlib.sha256(
            viewer_metadata_path.read_bytes()
        ).hexdigest(),
        "readme_sha256": (
            None
            if card_path is None
            else hashlib.sha256((output / "README.md").read_bytes()).hexdigest()
        ),
    }
    (output / "dataset_info.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare the SafeOCR-LabGold Hugging Face dataset"
    )
    parser.add_argument(
        "--split",
        type=Path,
        default=Path("docs/evidence/F6_LABGOLD_SPLIT.json"),
    )
    parser.add_argument(
        "--card",
        type=Path,
        default=Path("huggingface/dataset/README.md"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(split_path=args.split, output=args.output, card_path=args.card)
    print((args.output / "manifest.jsonl").as_posix())
    print((args.output / "metadata.jsonl").as_posix())
    print((args.output / "images" / "metadata.jsonl").as_posix())
    print((args.output / "dataset_info.json").as_posix())


if __name__ == "__main__":
    main()
