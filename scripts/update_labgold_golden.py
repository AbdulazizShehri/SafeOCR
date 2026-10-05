from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Final

from safeocr.labgold import (
    LabTemplate,
    apply_corruption,
    generate_fake_lab_record,
    render_lab_report,
)

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_DEFAULT_OUTPUT: Final[Path] = _REPO_ROOT / "benchmarks" / "labgold" / "golden-v1.json"
_RECORD_SEED: Final[int] = 61
_CORRUPTION_SEED: Final[int] = 3003


def build_golden_payload() -> dict[str, object]:
    """Build the canonical runtime-bound SafeOCR-LabGold regression payload."""

    record = generate_fake_lab_record(_RECORD_SEED)
    rendered = {template: render_lab_report(record, template) for template in LabTemplate}
    classic_manifest = json.loads(
        rendered[LabTemplate.CLASSIC].to_manifest_json()
    )
    corrupted_grid = apply_corruption(
        rendered[LabTemplate.GRID],
        seed=_CORRUPTION_SEED,
    )
    corrupted_manifest = json.loads(corrupted_grid.to_manifest_json())

    return {
        "corrupted_grid_sha256": corrupted_grid.page_sha256,
        "corruption_profile": corrupted_manifest["corruption"],
        "corruption_seed": _CORRUPTION_SEED,
        "golden_schema_version": "labgold-golden-v1",
        "labgold_schema_version": classic_manifest["schema_version"],
        "record_seed": _RECORD_SEED,
        "renderer": classic_manifest["renderer"],
        "template_hashes": {
            template.value: report.page_sha256
            for template, report in rendered.items()
        },
        "template_version": classic_manifest["template_version"],
    }


def write_golden(path: Path = _DEFAULT_OUTPUT) -> Path:
    """Write a canonical golden fixture using deterministic JSON formatting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(
        build_golden_payload(),
        indent=2,
        sort_keys=True,
    )
    path.write_text(content + "\n", encoding="utf-8", newline="\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate the runtime-bound SafeOCR-LabGold golden fixture. "
            "Review the resulting Git diff before committing."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help="output JSON path",
    )
    args = parser.parse_args()
    written = write_golden(args.output)
    print(written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
