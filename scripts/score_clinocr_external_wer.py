from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from safeocr.clinocr import ClinOcrRole, load_lookup_json, validate_lookup
from safeocr.clinocr_eval import SummaryStats, summary_stats, word_error_rate


def _metric_summary(rows: list[dict[str, float]], key: str) -> SummaryStats:
    return summary_stats(tuple(row[key] for row in rows))


def _serialize_summary(summary: SummaryStats) -> dict[str, float | int]:
    return asdict(summary)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score frozen ClinOCR-Bench external OCR outputs with official-compatible WER"
    )
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--ocr-root", type=Path, required=True)
    parser.add_argument("--engine", choices=("tesseract", "paddleocr"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records = load_lookup_json(args.dataset_root / "oneshot_lookup.json")
    validate_lookup(records, strict_counts=True)
    evaluation = tuple(item for item in records if item.role is ClinOcrRole.EVALUATION)
    if len(evaluation) != 328:
        raise RuntimeError("expected exactly 328 evaluation documents")

    output_dir = args.ocr_root / args.engine
    metadata_path = output_dir / "_run_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("ground_truth_opened") is not False:
        raise RuntimeError("OCR run metadata must attest ground_truth_opened=false")
    if metadata.get("tuning_performed") is not False:
        raise RuntimeError("OCR run metadata must attest tuning_performed=false")

    by_subset: dict[str, list[dict[str, float]]] = {}
    overall: list[dict[str, float]] = []
    per_document: list[dict[str, Any]] = []

    for record in evaluation:
        prediction_path = output_dir / f"{record.doc_id}.txt"
        if not prediction_path.is_file():
            raise FileNotFoundError(f"missing frozen OCR output: {prediction_path}")
        truth_path = args.dataset_root / record.ground_truth_path
        if not truth_path.is_file():
            raise FileNotFoundError(f"missing benchmark ground truth: {truth_path}")

        pred = prediction_path.read_text(encoding="utf-8")
        gold = truth_path.read_text(encoding="utf-8")
        metrics = word_error_rate(gold, pred)
        row = {
            "wer": metrics.wer,
            "substitution": metrics.substitution,
            "deletion": metrics.deletion,
            "insertion": metrics.insertion,
        }
        overall.append(row)
        by_subset.setdefault(record.subset, []).append(row)
        per_document.append(
            {
                "doc_id": record.doc_id,
                "subset": record.subset,
                **row,
            }
        )

    def bundle(rows: list[dict[str, float]]) -> dict[str, object]:
        return {
            "n": len(rows),
            "wer": _serialize_summary(_metric_summary(rows, "wer")),
            "substitution": _serialize_summary(
                _metric_summary(rows, "substitution")
            ),
            "deletion": _serialize_summary(_metric_summary(rows, "deletion")),
            "insertion": _serialize_summary(_metric_summary(rows, "insertion")),
        }

    overall_bundle = bundle(overall)
    payload = {
        "schema_version": 1,
        "dataset": "ClinOCR-Bench-v1.0",
        "engine": args.engine,
        "evaluation_documents": len(evaluation),
        "scoring": {
            "tokenization": "whitespace split",
            "metric": "WER=(S+D+I)/reference_words",
            "compatible_with": "ClinOCR-Bench-Baseline",
        },
        "run_metadata": metadata,
        "overall": overall_bundle,
        "subsets": {
            subset: bundle(rows)
            for subset, rows in sorted(by_subset.items())
        },
        "per_document": sorted(per_document, key=lambda item: str(item["doc_id"])),
    }
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized, encoding="utf-8", newline="\n")

    overall_wer_raw = overall_bundle["wer"]
    if not isinstance(overall_wer_raw, dict):
        raise TypeError("overall WER summary must be an object")
    overall_wer = cast(dict[str, float | int], overall_wer_raw)
    print(
        f"{args.engine}: N={len(evaluation)} "
        f"mean_WER={float(overall_wer['mean']):.4f} "
        f"median_WER={float(overall_wer['median']):.4f}"
    )


if __name__ == "__main__":
    main()
