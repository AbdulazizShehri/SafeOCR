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

from safeocr.clinocr import ClinOcrRole, load_lookup_json, validate_lookup
from safeocr.contracts import PageAsset
from safeocr.ocr import EngineFingerprint, normalize_paddle_result


class _PaddleResult(Protocol):
    json: Mapping[str, object]


class _PaddlePipeline(Protocol):
    def predict(self, input: str) -> Iterable[_PaddleResult]: ...


class _PaddleFactory(Protocol):
    def __call__(self, **kwargs: object) -> _PaddlePipeline: ...


def _build_paddle_pipeline() -> _PaddlePipeline:
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


def _resolve_tesseract(explicit: str | None) -> Path:
    candidates = [
        Path(explicit) if explicit else None,
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return candidate
    raise RuntimeError("Tesseract executable not found")


def _tesseract_version(executable: Path) -> str:
    completed = subprocess.run(
        [str(executable), "--version"],
        check=True,
        capture_output=True,
        text=True,
        shell=False,
        timeout=10,
    )
    return completed.stdout.splitlines()[0].strip()


def _run_tesseract(image_path: Path, executable: Path) -> str:
    completed = subprocess.run(
        [str(executable), str(image_path), "stdout", "-l", "eng", "--psm", "3"],
        check=False,
        capture_output=True,
        text=True,
        shell=False,
        timeout=60,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _run_paddle(image_path: Path, pipeline: _PaddlePipeline) -> str:
    image_bytes = image_path.read_bytes()
    digest = hashlib.sha256(image_bytes).hexdigest()
    with Image.open(image_path) as opened:
        width, height = opened.size

    page = PageAsset(
        document_sha256=digest,
        page_index=0,
        width_px=width,
        height_px=height,
        page_sha256=digest,
    )
    results = list(pipeline.predict(str(image_path)))
    if len(results) != 1:
        return ""
    normalized = normalize_paddle_result(
        page,
        results[0].json,
        EngineFingerprint(
            engine_name="paddleocr",
            engine_version=importlib.metadata.version("paddleocr"),
            model_name="PP-OCRv6_small_det+PP-OCRv6_small_rec",
            backend="onnxruntime-cpu",
        ),
    )
    return "\n".join(span.text for span in normalized.spans).strip()


def _write_text(output_dir: Path, doc_id: str, text: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{doc_id}.txt").write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run frozen SafeOCR OCR engines on ClinOCR-Bench test images"
    )
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--engine", choices=("tesseract", "paddleocr"), required=True)
    parser.add_argument("--tesseract", default=None)
    args = parser.parse_args()

    lookup = args.dataset_root / "oneshot_lookup.json"
    records = load_lookup_json(lookup)
    validate_lookup(records, strict_counts=True)
    evaluation = tuple(item for item in records if item.role is ClinOcrRole.EVALUATION)
    if len(evaluation) != 328:
        raise RuntimeError("expected exactly 328 external evaluation documents")

    output_dir = args.output_root / args.engine
    existing: set[str] = (
        {path.stem for path in output_dir.glob("*.txt")}
        if output_dir.exists()
        else set()
    )

    pipeline = _build_paddle_pipeline() if args.engine == "paddleocr" else None
    tesseract = _resolve_tesseract(args.tesseract) if args.engine == "tesseract" else None

    failures: list[str] = []
    for index, record in enumerate(evaluation, start=1):
        if record.doc_id in existing:
            continue
        image_path = args.dataset_root / record.image_path
        if not image_path.is_file():
            failures.append(record.doc_id)
            _write_text(output_dir, record.doc_id, "")
            continue
        try:
            text = (
                _run_paddle(image_path, pipeline)
                if pipeline is not None
                else _run_tesseract(image_path, cast(Path, tesseract))
            )
        except Exception:
            failures.append(record.doc_id)
            text = ""
        _write_text(output_dir, record.doc_id, text)
        print(f"{index:03d}/328 {args.engine} {record.doc_id}")

    metadata = {
        "schema_version": 1,
        "dataset": "ClinOCR-Bench-v1.0",
        "evaluation_documents": len(evaluation),
        "engine": args.engine,
        "paddleocr_version": (
            importlib.metadata.version("paddleocr") if args.engine == "paddleocr" else None
        ),
        "paddle_models": (
            "PP-OCRv6_small_det+PP-OCRv6_small_rec"
            if args.engine == "paddleocr"
            else None
        ),
        "paddle_backend": "onnxruntime-cpu" if args.engine == "paddleocr" else None,
        "tesseract_version": (
            _tesseract_version(cast(Path, tesseract))
            if args.engine == "tesseract"
            else None
        ),
        "failures": failures,
        "ground_truth_opened": False,
        "tuning_performed": False,
    }
    (output_dir / "_run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
