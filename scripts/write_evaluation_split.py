from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from safeocr.evaluation import (
    LABGOLD_SPLIT_SHA256,
    frozen_labgold_split,
    labgold_split_manifest_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the frozen SafeOCR F6 LabGold split")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs") / "evidence" / "F6_LABGOLD_SPLIT.json",
    )
    args = parser.parse_args()

    payload = labgold_split_manifest_json(frozen_labgold_split())
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    if digest != LABGOLD_SPLIT_SHA256:
        raise RuntimeError(
            "frozen LabGold split hash changed; explicit preregistration update required"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8", newline="\n")
    print(f"wrote {args.output} sha256={digest}")


if __name__ == "__main__":
    main()
