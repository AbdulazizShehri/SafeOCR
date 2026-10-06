from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Protocol, cast

from PIL import Image

from safeocr.contracts import PageAsset
from safeocr.ocr import EngineFingerprint, PageOcrResult, normalize_paddle_result


class _PaddleResult(Protocol):
    json: Mapping[str, object]


class _PaddlePipeline(Protocol):
    def predict(self, input: str) -> Iterable[_PaddleResult]: ...


class _PaddleFactory(Protocol):
    def __call__(self, **kwargs: object) -> _PaddlePipeline: ...


def _pipeline() -> _PaddlePipeline:
    module = importlib.import_module("paddleocr")
    factory = cast(_PaddleFactory, module.PaddleOCR)
    return factory(
        text_detection_model_name="PP-OCRv6_small_det",
        text_recognition_model_name="PP-OCRv6_small_rec",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        text_recognition_batch_size=1,
        engine="onnxruntime",
        device="cpu",
    )


def _git_state() -> tuple[str, bool]:
    root = Path(__file__).resolve().parents[1]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()
    return head, bool(status)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _dataset_manifest(
    images: tuple[Path, ...],
) -> tuple[dict[str, str], str]:
    hashes = {path.name: _sha256_bytes(path.read_bytes()) for path in images}
    canonical = json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    return hashes, _sha256_bytes(canonical)


def _run_state(
    *,
    git_head: str,
    manifest_sha256: str,
    fingerprint: EngineFingerprint,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "dataset": "Ma2023-public-laboratory-reports",
        "evaluation_images": 238,
        "git_head": git_head,
        "working_tree_dirty": False,
        "dataset_manifest_sha256": manifest_sha256,
        "engine": fingerprint.engine_name,
        "engine_version": fingerprint.engine_version,
        "models": fingerprint.model_name,
        "backend": fingerprint.backend,
    }


def _prepare_resume_state(
    output: Path,
    *,
    expected_state: dict[str, object],
) -> set[str]:
    output.mkdir(parents=True, exist_ok=True)
    state_path = output / "_run_state.json"
    existing_paths = tuple(
        path
        for path in output.glob("*.json")
        if path.name not in {"_run_metadata.json", "_run_state.json"}
    )
    if existing_paths:
        if not state_path.is_file():
            raise RuntimeError("existing OCR outputs require a matching run-state manifest")
        observed = json.loads(state_path.read_text(encoding="utf-8"))
        if observed != expected_state:
            raise RuntimeError("existing OCR outputs do not match the exact run state")
    else:
        state_path.write_text(
            json.dumps(expected_state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return {path.stem for path in existing_paths}


def _validate_existing_output(
    path: Path,
    *,
    expected_image_sha256: str,
    fingerprint: EngineFingerprint,
) -> None:
    raw = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
    page = cast(dict[str, object], raw.get("page"))
    observed_fp = cast(dict[str, object], raw.get("fingerprint"))
    if str(page.get("page_sha256")) != expected_image_sha256:
        raise RuntimeError(f"stale OCR output image hash: {path.name}")
    expected_fp = {
        "engine_name": fingerprint.engine_name,
        "engine_version": fingerprint.engine_version,
        "model_name": fingerprint.model_name,
        "backend": fingerprint.backend,
    }
    if {key: observed_fp.get(key) for key in expected_fp} != expected_fp:
        raise RuntimeError(f"stale OCR output engine fingerprint: {path.name}")


def _serialize(result: PageOcrResult) -> dict[str, object]:
    return {
        "page": {
            "document_sha256": result.page.document_sha256,
            "page_index": result.page.page_index,
            "width_px": result.page.width_px,
            "height_px": result.page.height_px,
            "page_sha256": result.page.page_sha256,
        },
        "fingerprint": {
            "engine_name": result.fingerprint.engine_name,
            "engine_version": result.fingerprint.engine_version,
            "model_name": result.fingerprint.model_name,
            "backend": result.fingerprint.backend,
        },
        "spans": [
            {
                "box": {
                    "x1": span.box.x1,
                    "y1": span.box.y1,
                    "x2": span.box.x2,
                    "y2": span.box.y2,
                },
                "text": span.text,
                "confidence": span.confidence,
            }
            for span in result.spans
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    images = tuple(sorted(args.images.glob("*.jpg")))
    if len(images) != 238:
        raise RuntimeError("expected exactly 238 public Ma2023 images")

    git_head, dirty = _git_state()
    if dirty:
        raise RuntimeError("Ma2023 OCR requires a clean exact-head working tree")

    fingerprint = EngineFingerprint(
        engine_name="paddleocr",
        engine_version=importlib.metadata.version("paddleocr"),
        model_name="PP-OCRv6_small_det+PP-OCRv6_small_rec",
        backend="onnxruntime-cpu",
    )
    image_hashes, manifest_sha256 = _dataset_manifest(images)
    expected_state = _run_state(
        git_head=git_head,
        manifest_sha256=manifest_sha256,
        fingerprint=fingerprint,
    )
    existing = _prepare_resume_state(
        args.output,
        expected_state=expected_state,
    )
    pipeline = _pipeline()

    failures: list[str] = []
    for index, image_path in enumerate(images, start=1):
        digest = image_hashes[image_path.name]
        output_path = args.output / f"{image_path.stem}.json"
        if image_path.stem in existing:
            _validate_existing_output(
                output_path,
                expected_image_sha256=digest,
                fingerprint=fingerprint,
            )
            continue
        with Image.open(image_path) as opened:
            width, height = opened.size
        page = PageAsset(
            document_sha256=digest,
            page_index=0,
            width_px=width,
            height_px=height,
            page_sha256=digest,
        )
        payload: dict[str, object]
        try:
            results = list(pipeline.predict(str(image_path)))
            if len(results) != 1:
                raise RuntimeError("expected one PaddleOCR result")
            normalized = normalize_paddle_result(page, results[0].json, fingerprint)
            payload = _serialize(normalized)
        except Exception:
            failures.append(image_path.name)
            payload = {
                "page": {
                    "document_sha256": digest,
                    "page_index": 0,
                    "width_px": width,
                    "height_px": height,
                    "page_sha256": digest,
                },
                "fingerprint": {
                    "engine_name": fingerprint.engine_name,
                    "engine_version": fingerprint.engine_version,
                    "model_name": fingerprint.model_name,
                    "backend": fingerprint.backend,
                },
                "spans": [],
            }
        (args.output / f"{image_path.stem}.json").write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"{index:03d}/238 {image_path.name}")

    metadata = {
        "schema_version": 1,
        "dataset": "Ma2023-public-laboratory-reports",
        "evaluation_images": 238,
        "git_head": git_head,
        "working_tree_dirty": dirty,
        "dataset_manifest_sha256": manifest_sha256,
        "run_state_sha256": _sha256_bytes(
            json.dumps(
                expected_state,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ),
        "engine": "paddleocr",
        "engine_version": fingerprint.engine_version,
        "models": fingerprint.model_name,
        "backend": fingerprint.backend,
        "failures": failures,
        "annotation_source_opened": False,
        "tuning_performed": False,
    }
    (args.output / "_run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
