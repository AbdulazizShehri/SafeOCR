from __future__ import annotations

import argparse
import hashlib
import shutil
import urllib.request
from pathlib import Path

from safeocr.fhir_validator import (
    OFFICIAL_VALIDATOR_SHA256,
    OFFICIAL_VALIDATOR_VERSION,
)

VALIDATOR_VERSION = OFFICIAL_VALIDATOR_VERSION
VALIDATOR_URL = (
    "https://github.com/hapifhir/org.hl7.fhir.core/releases/download/"
    f"{VALIDATOR_VERSION}/validator_cli.jar"
)
VALIDATOR_SHA256 = OFFICIAL_VALIDATOR_SHA256
DEFAULT_DESTINATION = (
    Path(".safeocr-tools")
    / "fhir-validator"
    / VALIDATOR_VERSION
    / "validator_cli.jar"
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def install_validator(destination: Path = DEFAULT_DESTINATION) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file():
        digest = _sha256_file(destination)
        if digest != VALIDATOR_SHA256:
            raise RuntimeError(
                "existing validator JAR checksum mismatch; remove it manually before retry"
            )
        return destination

    partial = destination.with_suffix(".jar.part")
    partial.unlink(missing_ok=True)
    try:
        with (
            urllib.request.urlopen(VALIDATOR_URL, timeout=60) as response,
            partial.open("wb") as output,
        ):
            shutil.copyfileobj(response, output, length=1024 * 1024)
        digest = _sha256_file(partial)
        if digest != VALIDATOR_SHA256:
            raise RuntimeError(
                f"downloaded validator checksum mismatch: {digest}"
            )
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)

    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Install pinned HL7 FHIR validator")
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()

    path = install_validator(args.destination)
    print(path)
    print(f"sha256={_sha256_file(path)}")


if __name__ == "__main__":
    main()
