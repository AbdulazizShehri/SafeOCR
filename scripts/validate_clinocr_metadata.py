from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from safeocr.clinocr import (
    CLINOCR_UPSTREAM_COMMIT,
    ClinOcrRole,
    frozen_safety_track_manifest,
    load_lookup_json,
    validate_lookup,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate pinned ClinOCR-Bench metadata without reading evaluation truth"
    )
    parser.add_argument("--lookup", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    lookup_bytes = args.lookup.read_bytes()
    records = load_lookup_json(args.lookup)
    validate_lookup(records, strict_counts=True)
    manifest = frozen_safety_track_manifest()

    exemplar_count = sum(item.role is ClinOcrRole.EXEMPLAR for item in records)
    evaluation_count = sum(item.role is ClinOcrRole.EVALUATION for item in records)
    subset_counts = {
        subset: sum(
            item.role is ClinOcrRole.EVALUATION and item.subset == subset
            for item in records
        )
        for subset in manifest.subsets
    }

    payload = {
        "schema_version": 1,
        "upstream_commit": CLINOCR_UPSTREAM_COMMIT,
        "lookup_sha256": hashlib.sha256(lookup_bytes).hexdigest(),
        "document_count": len(records),
        "exemplar_count": exemplar_count,
        "evaluation_count": evaluation_count,
        "evaluation_subset_counts": subset_counts,
        "threshold_tuning_allowed": manifest.threshold_tuning_allowed,
        "zero_shot_only": manifest.zero_shot_only,
        "ground_truth_opened": False,
        "evaluation_images_opened": False,
        "evaluation_outcomes_inspected": False,
    }
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")


if __name__ == "__main__":
    main()
