from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from safeocr.labgold import LabTemplate, generate_fake_lab_record, render_lab_report
from safeocr.report import field_from_trace_json, write_report


def _mapping(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return cast(dict[str, object], value)


def _integer(value: object, *, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    return value


def _string(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the canonical SafeOCR static evidence report"
    )
    parser.add_argument(
        "--smoke",
        type=Path,
        default=Path("docs/evidence/F4_RUNTIME_SMOKE.json"),
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=Path("docs/evidence/F7_EVIDENCE_REPORT.html"),
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=Path("docs/evidence/F7_EVIDENCE_REPORT.json"),
    )
    args = parser.parse_args()

    parsed = cast(object, json.loads(args.smoke.read_text(encoding="utf-8")))
    root = _mapping(parsed, name="F4 smoke")
    labgold = _mapping(root.get("labgold"), name="labgold")
    clean = _mapping(root.get("clean"), name="clean")
    trace = _mapping(clean.get("trace"), name="clean.trace")

    seed = _integer(labgold.get("seed"), name="labgold.seed")
    template = LabTemplate(_string(labgold.get("template"), name="labgold.template"))
    expected_page_sha = _string(labgold.get("page_sha256"), name="labgold.page_sha256")

    rendered = render_lab_report(generate_fake_lab_record(seed), template)
    if rendered.page_sha256 != expected_page_sha:
        raise RuntimeError("regenerated LabGold page does not match F4 evidence")

    field = field_from_trace_json(trace, page_png_bytes=rendered.png_bytes)
    if field.page_sha256 != rendered.page_sha256:
        raise RuntimeError("report field page identity does not match regenerated source")

    write_report(
        (field,),
        html_path=args.html,
        json_path=args.json,
        title="SafeOCR v0.1 Evidence Report",
    )
    print(args.html.as_posix())
    print(args.json.as_posix())


if __name__ == "__main__":
    main()
