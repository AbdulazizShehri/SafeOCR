from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, cast

_METHOD_ORDER = ("primary_ocr", "tesseract_crop", "naive_agreement", "safeocr")


def _read_json(path: Path) -> dict[str, Any]:
    parsed = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(parsed, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return cast(dict[str, Any], parsed)


def _number(value: object, *, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    return float(value)


def _integer(value: object, *, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deterministic F6 closeout artifacts")
    parser.add_argument(
        "--final",
        type=Path,
        default=Path("docs/evidence/F6_FINAL_EVALUATION.json"),
    )
    parser.add_argument(
        "--clinocr",
        type=Path,
        default=Path("docs/evidence/F6_CLINOCR_METADATA.json"),
    )
    parser.add_argument(
        "--risk-csv",
        type=Path,
        default=Path("docs/evidence/F6_RISK_COVERAGE.csv"),
    )
    parser.add_argument(
        "--closeout",
        type=Path,
        default=Path("docs/evidence/F6_CLOSEOUT.json"),
    )
    args = parser.parse_args()

    final = _read_json(args.final)
    clinocr = _read_json(args.clinocr)
    methods_raw = final.get("methods")
    if not isinstance(methods_raw, dict):
        raise ValueError("final evidence methods must be an object")
    methods = cast(dict[str, object], methods_raw)

    rows: list[dict[str, object]] = []
    for method in _METHOD_ORDER:
        raw = methods.get(method)
        if not isinstance(raw, dict):
            raise ValueError(f"missing final method metrics: {method}")
        metrics = cast(dict[str, object], raw)
        interval = metrics.get("unsafe_accept_interval_95")
        if not isinstance(interval, list):
            raise ValueError(f"{method} requires a two-value unsafe interval")
        interval_values = cast(list[object], interval)
        if len(interval_values) != 2:
            raise ValueError(f"{method} requires a two-value unsafe interval")
        rows.append(
            {
                "method": method,
                "coverage": _number(metrics.get("verified_coverage"), name="coverage"),
                "unsafe_accept_rate": _number(
                    metrics.get("unsafe_accept_rate"),
                    name="unsafe_accept_rate",
                ),
                "unsafe_accept_ci95_low": _number(
                    interval_values[0], name="unsafe_accept_ci95_low"
                ),
                "unsafe_accept_ci95_high": _number(
                    interval_values[1], name="unsafe_accept_ci95_high"
                ),
                "accepted_count": _integer(
                    metrics.get("accepted_count"),
                    name="accepted_count",
                ),
                "evaluable_count": _integer(
                    metrics.get("evaluable_count"),
                    name="evaluable_count",
                ),
            }
        )

    args.risk_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.risk_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    safeocr = cast(dict[str, object], methods["safeocr"])
    patient_rate = safeocr.get("patient_attribution_error_rate")
    fhir_rate = safeocr.get("fhir_mapping_error_rate")

    closeout = {
        "schema_version": 1,
        "status": "F6_COMPLETE_WITH_DECLARED_LIMITATIONS",
        "primary_final_evidence": str(args.final).replace("\\", "/"),
        "risk_coverage_artifact": str(args.risk_csv).replace("\\", "/"),
        "final_git_head": final.get("git", {}).get("head")
        if isinstance(final.get("git"), dict)
        else None,
        "labgold_split_sha256": final.get("split_sha256"),
        "safeocr": {
            "critical_field_exact_accuracy": safeocr.get(
                "critical_field_exact_accuracy"
            ),
            "unsafe_accept_rate": safeocr.get("unsafe_accept_rate"),
            "unsafe_accept_interval_95": safeocr.get("unsafe_accept_interval_95"),
            "verified_coverage": safeocr.get("verified_coverage"),
            "review_rate": safeocr.get("review_rate"),
            "abstention_rate": safeocr.get("abstention_rate"),
            "patient_attribution_error_rate": patient_rate,
            "table_association_error_rate": final.get(
                "association_scoring", {}
            ).get("primary_ocr", {}).get("table_association_error_rate")
            if isinstance(final.get("association_scoring"), dict)
            else None,
            "fhir_mapping_error_rate": fhir_rate,
        },
        "clinocr_integration": {
            "upstream_commit": clinocr.get("upstream_commit"),
            "lookup_sha256": clinocr.get("lookup_sha256"),
            "evaluation_count": clinocr.get("evaluation_count"),
            "threshold_tuning_allowed": clinocr.get("threshold_tuning_allowed"),
            "evaluation_outcomes_inspected": clinocr.get(
                "evaluation_outcomes_inspected"
            ),
        },
        "limitations": [
            (
                "The primary v0.1 policy has one frozen SafeOCR operating point. "
                "A post-hoc threshold sweep after final-set inspection would violate the "
                "evaluation contract, so the risk-coverage artifact reports preregistered "
                "operating points rather than a retrospectively tuned continuous curve."
            ),
            (
                "ClinOCR-Bench v1.0 supplies full-document transcript truth, not SafeOCR "
                "critical-field/patient/FHIR annotations. F6.3 therefore freezes a no-tuning "
                "external adapter and Safety Track manifest without fabricating unsupported "
                "critical-field outcome claims."
            ),
            (
                "The LabGold raw primary OCR baseline observed zero accepted errors at full "
                "coverage; therefore LabGold alone does not establish SafeOCR superiority "
                "over the primary OCR baseline."
            ),
            (
                "SafeOCR FHIR mapping error is not estimable from the frozen F6 primary "
                "artifact because per-field FHIR export was not part of the preregistered "
                "final runner. F5 provides validator conformance evidence, not an F6 mapping "
                "error-rate estimate."
            ),
        ],
    }
    serialized = json.dumps(closeout, indent=2, sort_keys=True) + "\n"
    args.closeout.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")


if __name__ == "__main__":
    main()
