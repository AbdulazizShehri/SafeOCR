from __future__ import annotations

import hashlib
import io
from collections.abc import Sequence
from dataclasses import dataclass

import pytest
from PIL import Image

from safeocr.contracts import BoundingBox, PageAsset
from safeocr.ocr import (
    EngineFingerprint,
    EngineRuntimeError,
    extract_critical_crop,
    normalize_paddle_result,
    probe_runtime,
    read_tesseract_crop,
)

SHA = "a" * 64


def _page(png_bytes: bytes) -> PageAsset:
    return PageAsset(
        document_sha256=SHA,
        page_index=0,
        width_px=100,
        height_px=60,
        page_sha256=hashlib.sha256(png_bytes).hexdigest(),
    )


def _png(width: int = 100, height: int = 60) -> bytes:
    image = Image.new("RGB", (width, height), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _fingerprint() -> EngineFingerprint:
    return EngineFingerprint(
        engine_name="paddleocr",
        engine_version="3.7.0",
        model_name="PP-OCRv6_small_det+PP-OCRv6_small_rec",
        backend="onnxruntime-cpu",
    )


def test_engine_fingerprint_rejects_empty_identity_fields() -> None:
    with pytest.raises(ValueError):
        EngineFingerprint("", "3.7.0", "model", "onnxruntime-cpu")


def test_paddle_normalization_binds_spans_to_page() -> None:
    png = _png()
    page = _page(png)
    raw = {
        "res": {
            "rec_texts": ["Potassium", "6.8"],
            "rec_scores": [0.99, 0.91],
            "rec_boxes": [[1, 2, 40, 12], [50, 2, 70, 12]],
        }
    }

    result = normalize_paddle_result(page, raw, _fingerprint())

    assert len(result.spans) == 2
    assert all(span.page == page for span in result.spans)
    assert result.spans[1].text == "6.8"
    assert result.spans[1].confidence == 0.91
    assert result.spans[1].box == BoundingBox(50, 2, 71, 13)



class _ArrayLike:
    def __init__(self, value: object) -> None:
        self._value = value

    def tolist(self) -> object:
        return self._value


def test_paddle_numpy_like_arrays_are_normalized_without_numpy_dependency() -> None:
    png = _png()
    page = _page(png)
    raw = {
        "res": {
            "rec_texts": ["Potassium", "6.8"],
            "rec_scores": _ArrayLike([0.99, 0.91]),
            "rec_boxes": _ArrayLike([[1, 2, 40, 12], [50, 2, 70, 12]]),
        }
    }

    result = normalize_paddle_result(page, raw, _fingerprint())

    assert [span.text for span in result.spans] == ["Potassium", "6.8"]
    assert result.spans[1].box == BoundingBox(50, 2, 71, 13)

def test_paddle_blank_reads_are_dropped_without_misalignment() -> None:
    png = _png()
    page = _page(png)
    raw = {
        "res": {
            "rec_texts": ["Potassium", "", "6.8"],
            "rec_scores": [0.99, 0.20, 0.91],
            "rec_boxes": [[1, 2, 40, 12], [41, 2, 49, 12], [50, 2, 70, 12]],
        }
    }

    result = normalize_paddle_result(page, raw, _fingerprint())

    assert [span.text for span in result.spans] == ["Potassium", "6.8"]
    assert [span.confidence for span in result.spans] == [0.99, 0.91]


def test_paddle_length_mismatch_is_rejected() -> None:
    page = _page(_png())
    raw = {
        "res": {
            "rec_texts": ["6.8"],
            "rec_scores": [0.91, 0.40],
            "rec_boxes": [[1, 2, 20, 12]],
        }
    }
    with pytest.raises(ValueError):
        normalize_paddle_result(page, raw, _fingerprint())


@pytest.mark.parametrize(
    "box",
    [
        [-1, 2, 20, 12],
        [20, 2, 10, 12],
        [1, 2, 120, 12],
        [1, 2, 20],
    ],
)
def test_paddle_bad_boxes_are_rejected(box: list[int]) -> None:
    page = _page(_png())
    raw = {
        "res": {
            "rec_texts": ["6.8"],
            "rec_scores": [0.91],
            "rec_boxes": [box],
        }
    }
    with pytest.raises(ValueError):
        normalize_paddle_result(page, raw, _fingerprint())


def test_crop_rejects_page_hash_mismatch() -> None:
    png = _png()
    page = PageAsset(SHA, 0, 100, 60, "b" * 64)

    with pytest.raises(ValueError):
        extract_critical_crop(png, page, BoundingBox(10, 10, 30, 25))


def test_crop_rejects_dimension_mismatch() -> None:
    png = _png(90, 60)
    page = PageAsset(SHA, 0, 100, 60, hashlib.sha256(png).hexdigest())

    with pytest.raises(ValueError):
        extract_critical_crop(png, page, BoundingBox(10, 10, 30, 25))


def test_crop_padding_is_clipped_and_deterministic() -> None:
    png = _png()
    page = _page(png)
    requested = BoundingBox(1, 1, 20, 10)

    first = extract_critical_crop(png, page, requested, padding_px=5)
    second = extract_critical_crop(png, page, requested, padding_px=5)

    assert first.crop_box == BoundingBox(0, 0, 25, 15)
    assert first.requested_box == requested
    assert first.png_bytes == second.png_bytes
    assert first.crop_sha256 == second.crop_sha256


@dataclass
class _Completed:
    returncode: int
    stdout: bytes
    stderr: bytes


class _Runner:
    def __init__(self, completed: _Completed) -> None:
        self.completed = completed
        self.calls: list[dict[str, object]] = []

    def __call__(
        self,
        args: Sequence[str],
        *,
        input: bytes,
        stdout: int,
        stderr: int,
        timeout: float,
        check: bool,
        shell: bool,
    ) -> _Completed:
        self.calls.append(
            {
                "args": list(args),
                "input": input,
                "stdout": stdout,
                "stderr": stderr,
                "timeout": timeout,
                "check": check,
                "shell": shell,
            }
        )
        return self.completed


def test_tesseract_invocation_is_safe_and_not_clinically_corrected() -> None:
    crop = extract_critical_crop(
        _png(),
        _page(_png()),
        BoundingBox(10, 10, 30, 25),
    )
    runner = _Runner(_Completed(0, b"6.B\n", b""))

    read = read_tesseract_crop(
        crop,
        executable="tesseract",
        runner=runner,
        timeout_seconds=4.0,
    )

    call = runner.calls[0]
    assert call["args"] == [
        "tesseract",
        "stdin",
        "stdout",
        "-l",
        "eng",
        "--psm",
        "7",
    ]
    assert call["shell"] is False
    assert call["timeout"] == 4.0
    assert read.text == "6.B"


@pytest.mark.parametrize(
    "completed",
    [
        _Completed(2, b"", b"failure"),
        _Completed(0, b"\xff", b""),
    ],
)
def test_tesseract_runtime_failures_are_explicit(completed: _Completed) -> None:
    png = _png()
    crop = extract_critical_crop(png, _page(png), BoundingBox(10, 10, 30, 25))
    runner = _Runner(completed)

    with pytest.raises(EngineRuntimeError):
        read_tesseract_crop(crop, executable="tesseract", runner=runner)


def test_runtime_probe_does_not_require_importing_heavy_models() -> None:
    probe = probe_runtime(
        package_versions={
            "paddleocr": "3.7.0",
            "onnxruntime": "1.23.2",
        },
        tesseract_path=None,
    )

    assert probe.paddleocr_version == "3.7.0"
    assert probe.onnxruntime_version == "1.23.2"
    assert probe.tesseract_available is False
