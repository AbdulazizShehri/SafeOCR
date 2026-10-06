from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from safeocr.evaluation import match_span_to_truth_region
from safeocr.labgold import TruthRegion
from safeocr.ma2023 import Ma2023Region, laboratory_rows, load_ma2023_annotations
from safeocr.verification import normalize_evidence_text, parse_critical_value
from scripts.score_ma2023_external_verifier import load_page_result


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _truth(region: Ma2023Region) -> TruthRegion:
    return TruthRegion(
        role=f"column-{region.column_no}",
        row_id=str(region.row_no),
        text=region.text,
        box=region.box,
    )


def _same(left: str, right: str) -> bool:
    return normalize_evidence_text(left) == normalize_evidence_text(right)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--primary-artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    primary_raw: object = json.loads(
        args.primary_artifact.read_text(encoding="utf-8")
    )
    if not isinstance(primary_raw, dict):
        raise ValueError("primary artifact must be a JSON object")
    primary = cast(dict[str, Any], primary_raw)
    rows_raw = primary.get("rows")
    if not isinstance(rows_raw, list):
        raise ValueError("primary artifact must contain rows")
    rows = cast(list[object], rows_raw)

    passed: set[tuple[str, int]] = set()
    for raw_item in rows:
        if not isinstance(raw_item, dict):
            continue
        item = cast(dict[str, object], raw_item)
        if not item.get("component_pass"):
            continue
        filename = item.get("filename")
        row = item.get("row")
        if isinstance(filename, str) and isinstance(row, int):
            passed.add((filename, row))

    documents = load_ma2023_annotations(args.labels)
    counts: Counter[str] = Counter()
    strata: dict[str, Counter[str]] = {
        "scan": Counter(),
        "illumination": Counter(),
    }

    for document in documents:
        result = load_page_result(
            args.ocr / f"{Path(document.filename).stem}.json"
        )
        kind = "scan" if document.filename.startswith("scan_") else "illumination"
        for row in laboratory_rows(document):
            analyte_gold = row.get(2)
            value_gold = row.get(3)
            unit_gold = row.get(4)
            if not (
                analyte_gold
                and analyte_gold.text
                and value_gold
                and value_gold.text
                and unit_gold
                and unit_gold.text
            ):
                continue
            if parse_critical_value(value_gold.text) is None:
                continue
            key = (document.filename, value_gold.row_no)
            if key not in passed:
                continue

            analyte = match_span_to_truth_region(result, _truth(analyte_gold))
            value = match_span_to_truth_region(result, _truth(value_gold))
            unit = match_span_to_truth_region(result, _truth(unit_gold))

            analyte_exact = bool(
                analyte and _same(analyte.text, analyte_gold.text)
            )
            value_exact = bool(value and _same(value.text, value_gold.text))
            unit_exact = bool(unit and _same(unit.text, unit_gold.text))
            field_exact = analyte_exact and value_exact and unit_exact

            counts["component_pass"] += 1
            counts["full_field_exact"] += int(field_exact)
            counts["full_field_inexact"] += int(not field_exact)
            counts["analyte_mismatch"] += int(not analyte_exact)
            counts["value_mismatch"] += int(not value_exact)
            counts["unit_mismatch"] += int(not unit_exact)
            counts["both_analyte_unit_mismatch"] += int(
                not analyte_exact and not unit_exact
            )

            strata[kind]["component_pass"] += 1
            strata[kind]["full_field_exact"] += int(field_exact)
            strata[kind]["full_field_inexact"] += int(not field_exact)

    if counts["component_pass"] != len(passed):
        raise RuntimeError("diagnostic pass count does not match primary artifact")

    payload: dict[str, object] = {
        "schema_version": 1,
        "analysis_role": "exploratory_post_outcome_diagnostic",
        "primary_artifact": str(args.primary_artifact).replace("\\", "/"),
        "primary_artifact_sha256": _sha256(args.primary_artifact),
        "labels_sha256": _sha256(args.labels),
        "claim_boundary": {
            "primary_endpoint": False,
            "post_hoc_exploratory": True,
            "end_to_end_extraction": False,
            "full_safeocr_policy": False,
        },
        "counts": dict(sorted(counts.items())),
        "strata": {
            key: dict(sorted(value.items()))
            for key, value in sorted(strata.items())
        },
    }
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")


if __name__ == "__main__":
    main()
