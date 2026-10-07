from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any, cast

CANONICAL_MANIFEST_SHA256 = (
    "3a3fcdf1e3e045c0b6f8b334457d1e22dbd247a6a556e08235f808143abf5cec"
)
_SPLIT_MAP = {
    "calibration": "calibration",
    "evaluation": "evaluation",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mapping(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return cast(dict[str, object], value)


def _string(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _integer(value: object, *, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    return value


def _optional_integer(value: object, *, name: str) -> int | None:
    if value is None:
        return None
    return _integer(value, name=name)


def _load_rows(manifest_path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, line in enumerate(
        manifest_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line:
            continue
        parsed: object = json.loads(line)
        rows.append(_mapping(parsed, name=f"manifest row {index}"))
    if not rows:
        raise ValueError("manifest contains no rows")
    return rows


def _datasets_api() -> tuple[Any, Any]:
    try:
        module = importlib.import_module("datasets")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Hugging Face viewer generation requires the 'datasets' package. "
            "Install datasets>=4,<5 in the release environment."
        ) from exc
    dataset_class: Any = module.Dataset
    image_class: Any = module.Image
    return dataset_class, image_class


def project_viewer_row(dataset_root: Path, row: dict[str, object]) -> dict[str, object]:
    file_name = _string(row.get("file_name"), name="file_name")
    image_path = (dataset_root / file_name).resolve()
    root_resolved = dataset_root.resolve()
    if not image_path.is_relative_to(root_resolved):
        raise ValueError(f"image path escapes dataset root: {file_name}")
    if not image_path.is_file():
        raise FileNotFoundError(image_path)

    expected_sha = _string(row.get("image_sha256"), name="image_sha256")
    actual_sha = _sha256(image_path)
    if actual_sha != expected_sha:
        raise RuntimeError(
            f"image hash mismatch for {file_name}: expected {expected_sha}, got {actual_sha}"
        )

    role = _string(row.get("role"), name="role")
    if role not in _SPLIT_MAP:
        raise ValueError(f"unsupported role: {role}")

    regions = row.get("regions")
    if not isinstance(regions, list):
        raise ValueError("regions must be a list")

    return {
        "image": {
            "bytes": image_path.read_bytes(),
            "path": image_path.name,
        },
        "case_id": _string(row.get("case_id"), name="case_id"),
        "role": role,
        "record_seed": _integer(row.get("record_seed"), name="record_seed"),
        "corruption_seed": _optional_integer(
            row.get("corruption_seed"), name="corruption_seed"
        ),
        "template": _string(row.get("template"), name="template"),
        "image_sha256": expected_sha,
        "source_page_sha256": row.get("source_page_sha256"),
        "synthetic_patient_id": _string(
            row.get("synthetic_patient_id"), name="synthetic_patient_id"
        ),
        "synthetic_report_id": _string(
            row.get("synthetic_report_id"), name="synthetic_report_id"
        ),
        "critical_field_count": _integer(
            row.get("critical_field_count"), name="critical_field_count"
        ),
        "regions_json": json.dumps(
            regions,
            sort_keys=True,
            separators=(",", ":"),
        ),
    }


def prepare_viewer(
    *,
    dataset_root: Path,
    required_manifest_sha: str | None = CANONICAL_MANIFEST_SHA256,
) -> dict[str, object]:
    manifest_path = dataset_root / "manifest.jsonl"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)

    manifest_sha = _sha256(manifest_path)
    if required_manifest_sha is not None and manifest_sha != required_manifest_sha:
        raise RuntimeError(
            "non-canonical SafeOCR-LabGold manifest: "
            f"expected {required_manifest_sha}, got {manifest_sha}"
        )

    rows = _load_rows(manifest_path)
    viewer_dir = dataset_root / "viewer"
    if viewer_dir.exists() and any(viewer_dir.iterdir()):
        raise FileExistsError("viewer directory must be empty")
    viewer_dir.mkdir(parents=True, exist_ok=True)

    dataset_class, image_class = _datasets_api()
    split_rows: dict[str, list[dict[str, object]]] = {
        "calibration": [],
        "evaluation": [],
    }
    for row in rows:
        projected = project_viewer_row(dataset_root, row)
        split_name = _SPLIT_MAP[cast(str, projected["role"])]
        split_rows[split_name].append(projected)

    if len(split_rows["calibration"]) != 24:
        raise RuntimeError("expected 24 calibration documents")
    if len(split_rows["evaluation"]) != 48:
        raise RuntimeError("expected 48 final-evaluation documents")

    parquet_hashes: dict[str, str] = {}
    for split_name in ("calibration", "evaluation"):
        dataset = dataset_class.from_list(split_rows[split_name]).cast_column(
            "image", image_class()
        )
        path = viewer_dir / f"{split_name}.parquet"
        dataset.to_parquet(str(path))
        parquet_hashes[split_name] = _sha256(path)

    summary: dict[str, object] = {
        "schema_version": 1,
        "manifest_sha256": manifest_sha,
        "calibration_rows": len(split_rows["calibration"]),
        "evaluation_rows": len(split_rows["evaluation"]),
        "calibration_parquet_sha256": parquet_hashes["calibration"],
        "evaluation_parquet_sha256": parquet_hashes["evaluation"],
        "note": "Derived viewer artifacts; canonical authority remains manifest.jsonl and images/.",
    }
    (viewer_dir / "viewer_info.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare derived Hugging Face viewer Parquet for SafeOCR-LabGold"
    )
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument(
        "--allow-noncanonical",
        action="store_true",
        help="Allow a non-canonical manifest for development/testing only.",
    )
    args = parser.parse_args()

    required_sha = None if args.allow_noncanonical else CANONICAL_MANIFEST_SHA256
    summary = prepare_viewer(
        dataset_root=args.dataset_root,
        required_manifest_sha=required_sha,
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
