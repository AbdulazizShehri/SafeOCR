from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import platform
import subprocess
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Protocol, cast

from safeocr.contracts import PageAsset
from safeocr.labgold import LabTemplate, generate_fake_lab_record, render_lab_report
from safeocr.ocr import (
    EngineFingerprint,
    extract_critical_crop,
    normalize_paddle_result,
    read_tesseract_crop,
)


class _PaddleResult(Protocol):
    json: Mapping[str, object]


class _PaddlePipeline(Protocol):
    def predict(self, input: str) -> Iterable[_PaddleResult]: ...


class _PaddleFactory(Protocol):
    def __call__(self, **kwargs: object) -> _PaddlePipeline: ...


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_tesseract(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend(
        [
            Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
            Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("Tesseract executable not found; pass --tesseract explicitly")


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


def _model_hashes() -> dict[str, dict[str, object]]:
    home = Path.home() / ".paddlex" / "official_models"
    files = {
        "PP-OCRv6_small_det_onnx": home / "PP-OCRv6_small_det_onnx" / "inference.onnx",
        "PP-OCRv6_small_rec_onnx": home / "PP-OCRv6_small_rec_onnx" / "inference.onnx",
    }
    result: dict[str, dict[str, object]] = {}
    for name, path in files.items():
        if not path.is_file():
            raise RuntimeError(f"required model file missing: {path}")
        result[name] = {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
    return result


def _build_paddle_pipeline() -> _PaddlePipeline:
    module = importlib.import_module("paddleocr")
    factory = cast(_PaddleFactory, module.PaddleOCR)
    return factory(
        text_detection_model_name="PP-OCRv6_small_det",
        text_recognition_model_name="PP-OCRv6_small_rec",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        engine="onnxruntime",
        device="cpu",
    )


def run_smoke(*, tesseract: Path) -> dict[str, object]:
    rendered = render_lab_report(generate_fake_lab_record(53), LabTemplate.CLASSIC)
    page_sha = hashlib.sha256(rendered.png_bytes).hexdigest()
    page = PageAsset(
        document_sha256=page_sha,
        page_index=0,
        width_px=rendered.width_px,
        height_px=rendered.height_px,
        page_sha256=page_sha,
    )

    with tempfile.TemporaryDirectory(prefix="safeocr-f3-") as tmp:
        image_path = Path(tmp) / "labgold.png"
        image_path.write_bytes(rendered.png_bytes)
        pipeline = _build_paddle_pipeline()
        paddle_results = list(pipeline.predict(str(image_path)))

    if len(paddle_results) != 1:
        raise RuntimeError(f"expected one PaddleOCR result, got {len(paddle_results)}")

    normalized = normalize_paddle_result(
        page,
        paddle_results[0].json,
        EngineFingerprint(
            engine_name="paddleocr",
            engine_version=importlib.metadata.version("paddleocr"),
            model_name="PP-OCRv6_small_det+PP-OCRv6_small_rec",
            backend="onnxruntime-cpu",
        ),
    )
    if not normalized.spans:
        raise RuntimeError("PaddleOCR smoke produced no normalized spans")
    if not all(
        span.box.x2 <= page.width_px and span.box.y2 <= page.height_px
        for span in normalized.spans
    ):
        raise RuntimeError("PaddleOCR smoke produced an out-of-page span")

    truth_value = None
    for index, region in enumerate(rendered.regions):
        if region.role == "analyte" and region.text == "Potassium":
            truth_value = next(
                (item for item in rendered.regions[index + 1 :] if item.role == "value"),
                None,
            )
            break
    if truth_value is None:
        raise RuntimeError("Potassium truth value was not found in LabGold")

    crop = extract_critical_crop(
        rendered.png_bytes,
        page,
        truth_value.box,
        padding_px=6,
    )
    tesseract_read = read_tesseract_crop(
        crop,
        executable=str(tesseract),
        timeout_seconds=10.0,
    )
    paddle_truth_match = any(span.text == truth_value.text for span in normalized.spans)
    tesseract_truth_match = tesseract_read.text == truth_value.text
    if not paddle_truth_match:
        raise RuntimeError("PaddleOCR did not recover the clean LabGold Potassium value")
    if not tesseract_truth_match:
        raise RuntimeError(
            "Tesseract critical-crop read did not match the clean LabGold truth"
        )

    eng_data = tesseract.parent / "tessdata" / "eng.traineddata"
    if not eng_data.is_file():
        raise RuntimeError("Tesseract English traineddata not found")

    return {
        "schema_version": 1,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "packages": {
            "paddleocr": importlib.metadata.version("paddleocr"),
            "paddlex": importlib.metadata.version("paddlex"),
            "onnxruntime": importlib.metadata.version("onnxruntime"),
        },
        "models": _model_hashes(),
        "tesseract": {
            "version": _tesseract_version(tesseract),
            "eng_traineddata_sha256": _sha256(eng_data),
            "eng_traineddata_bytes": eng_data.stat().st_size,
        },
        "labgold": {
            "seed": 53,
            "template": LabTemplate.CLASSIC.value,
            "page_sha256": page.page_sha256,
            "truth_field": "Potassium",
            "truth_value": truth_value.text,
        },
        "results": {
            "paddle_normalized_span_count": len(normalized.spans),
            "paddle_truth_value_detected": paddle_truth_match,
            "all_paddle_spans_in_page": True,
            "tesseract_truth_value": tesseract_read.text,
            "tesseract_truth_value_match": tesseract_truth_match,
            "critical_crop_sha256": crop.crop_sha256,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SafeOCR F3 local runtime smoke")
    parser.add_argument("--tesseract", default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    tesseract = _resolve_tesseract(args.tesseract)
    payload = run_smoke(tesseract=tesseract)
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")


if __name__ == "__main__":
    main()
