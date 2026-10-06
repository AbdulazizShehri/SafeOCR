from __future__ import annotations

import hashlib
import importlib.metadata
import io
import re
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, cast, runtime_checkable

from PIL import Image

from safeocr.contracts import BoundingBox, CandidateSpan, PageAsset


class EngineRuntimeError(RuntimeError):
    """Raised when an OCR runtime cannot produce a trustworthy execution result."""


@dataclass(frozen=True, slots=True)
class EngineFingerprint:
    """Pinned identity for one OCR engine/model/backend combination."""

    engine_name: str
    engine_version: str
    model_name: str
    backend: str

    def __post_init__(self) -> None:
        for name, value in (
            ("engine_name", self.engine_name),
            ("engine_version", self.engine_version),
            ("model_name", self.model_name),
            ("backend", self.backend),
        ):
            if not value.strip():
                raise ValueError(f"{name} must be non-empty")


@dataclass(frozen=True, slots=True)
class PageOcrResult:
    """Normalized full-page OCR result bound to one immutable source page."""

    page: PageAsset
    fingerprint: EngineFingerprint
    spans: tuple[CandidateSpan, ...]

    def __post_init__(self) -> None:
        for span in self.spans:
            if span.page != self.page:
                raise ValueError("all OCR spans must be bound to the supplied source page")
            if span.engine_name != self.fingerprint.engine_name:
                raise ValueError("span engine_name must match the engine fingerprint")
            if span.engine_version != self.fingerprint.engine_version:
                raise ValueError("span engine_version must match the engine fingerprint")


@dataclass(frozen=True, slots=True)
class CriticalCrop:
    """Deterministic crop derived from an exact source-page region."""

    source_page: PageAsset
    requested_box: BoundingBox
    crop_box: BoundingBox
    png_bytes: bytes
    crop_sha256: str


@dataclass(frozen=True, slots=True)
class CropRead:
    """Independent OCR read bound to the exact critical crop."""

    text: str
    engine_name: str
    engine_version: str
    executable: str
    crop_sha256: str

    def __post_init__(self) -> None:
        if not self.engine_name.strip():
            raise ValueError("engine_name must be non-empty")
        if not self.engine_version.strip():
            raise ValueError("engine_version must be non-empty")
        if not self.executable.strip():
            raise ValueError("executable must be non-empty")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", self.crop_sha256):
            raise ValueError("crop_sha256 must be a 64-character hexadecimal SHA-256")


@dataclass(frozen=True, slots=True)
class RuntimeProbe:
    """Dependency availability without importing heavy OCR models."""

    paddleocr_version: str | None
    onnxruntime_version: str | None
    tesseract_available: bool
    tesseract_path: str | None


@runtime_checkable
class _SupportsToList(Protocol):
    def tolist(self) -> object: ...


class _CompletedLike(Protocol):
    returncode: int
    stdout: bytes
    stderr: bytes


class _Runner(Protocol):
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
    ) -> _CompletedLike: ...


def _require_sequence(value: object, *, field: str) -> Sequence[object]:
    if isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{field} must be a sequence")
    if isinstance(value, Sequence):
        return cast(Sequence[object], value)
    if isinstance(value, _SupportsToList):
        return _require_sequence(value.tolist(), field=field)
    raise ValueError(f"{field} must be a sequence")


def _require_result_mapping(raw: Mapping[str, object]) -> Mapping[str, object]:
    res = raw.get("res")
    if not isinstance(res, Mapping):
        raise ValueError("Paddle result must contain a mapping under 'res'")
    return cast(Mapping[str, object], res)


def _parse_score(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Paddle recognition scores must be numeric")
    score = float(value)
    if not 0.0 <= score <= 1.0:
        raise ValueError("Paddle recognition scores must be between 0 and 1")
    return score


def _parse_box(value: object, page: PageAsset) -> BoundingBox:
    raw_box = _require_sequence(value, field="rec_boxes item")
    if len(raw_box) != 4:
        raise ValueError("Paddle rec_boxes items must contain exactly four coordinates")

    coords: list[int] = []
    for raw_coord in raw_box:
        if isinstance(raw_coord, bool) or not isinstance(raw_coord, int):
            raise ValueError("Paddle rec_boxes coordinates must be integers")
        coords.append(raw_coord)

    x1, y1, x_max, y_max = coords
    if x1 < 0 or y1 < 0:
        raise ValueError("Paddle rec_boxes coordinates must be non-negative")
    if x_max < x1 or y_max < y1:
        raise ValueError("Paddle rec_boxes coordinates must not be inverted")

    # Paddle documents rec_boxes as [xmin, ymin, xmax, ymax] pixel coordinates.
    # SafeOCR uses half-open boxes, so include the max-coordinate pixel with +1.
    box = BoundingBox(x1=x1, y1=y1, x2=x_max + 1, y2=y_max + 1)
    if box.x2 > page.width_px or box.y2 > page.height_px:
        raise ValueError("Paddle rec_boxes item exceeds source-page geometry")
    return box


def normalize_paddle_result(
    page: PageAsset,
    raw: Mapping[str, object],
    fingerprint: EngineFingerprint,
) -> PageOcrResult:
    """Normalize PaddleOCR's current OCR-pipeline JSON shape into SafeOCR spans."""

    res = _require_result_mapping(raw)
    texts = _require_sequence(res.get("rec_texts"), field="rec_texts")
    scores = _require_sequence(res.get("rec_scores"), field="rec_scores")
    boxes = _require_sequence(res.get("rec_boxes"), field="rec_boxes")

    if len(texts) != len(scores) or len(texts) != len(boxes):
        raise ValueError("Paddle rec_texts, rec_scores, and rec_boxes must have equal lengths")

    spans: list[CandidateSpan] = []
    for raw_text, raw_score, raw_box in zip(texts, scores, boxes, strict=True):
        if not isinstance(raw_text, str):
            raise ValueError("Paddle rec_texts items must be strings")
        score = _parse_score(raw_score)
        box = _parse_box(raw_box, page)
        if not raw_text.strip():
            continue
        spans.append(
            CandidateSpan(
                page=page,
                box=box,
                text=raw_text,
                engine_name=fingerprint.engine_name,
                engine_version=fingerprint.engine_version,
                confidence=score,
            )
        )

    return PageOcrResult(page=page, fingerprint=fingerprint, spans=tuple(spans))


def extract_critical_crop(
    page_png_bytes: bytes,
    page: PageAsset,
    requested_box: BoundingBox,
    *,
    padding_px: int = 0,
) -> CriticalCrop:
    """Create a deterministic PNG crop after validating source-page identity."""

    if type(padding_px) is not int or padding_px < 0:
        raise ValueError("padding_px must be a non-negative int")
    if hashlib.sha256(page_png_bytes).hexdigest() != page.page_sha256:
        raise ValueError("source page bytes do not match PageAsset.page_sha256")
    if requested_box.x2 > page.width_px or requested_box.y2 > page.height_px:
        raise ValueError("requested crop box exceeds source-page geometry")

    with Image.open(io.BytesIO(page_png_bytes)) as opened:
        if opened.format != "PNG":
            raise ValueError("critical-crop source must be PNG")
        image = opened.convert("RGB")

    if image.size != (page.width_px, page.height_px):
        raise ValueError("decoded page dimensions do not match PageAsset geometry")

    crop_box = BoundingBox(
        x1=max(0, requested_box.x1 - padding_px),
        y1=max(0, requested_box.y1 - padding_px),
        x2=min(page.width_px, requested_box.x2 + padding_px),
        y2=min(page.height_px, requested_box.y2 + padding_px),
    )
    cropped = image.crop((crop_box.x1, crop_box.y1, crop_box.x2, crop_box.y2))
    buffer = io.BytesIO()
    cropped.save(buffer, format="PNG", optimize=False, compress_level=9)
    png_bytes = buffer.getvalue()

    return CriticalCrop(
        source_page=page,
        requested_box=requested_box,
        crop_box=crop_box,
        png_bytes=png_bytes,
        crop_sha256=hashlib.sha256(png_bytes).hexdigest(),
    )


def _subprocess_runner(
    args: Sequence[str],
    *,
    input: bytes,
    stdout: int,
    stderr: int,
    timeout: float,
    check: bool,
    shell: bool,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        args,
        input=input,
        stdout=stdout,
        stderr=stderr,
        timeout=timeout,
        check=check,
        shell=shell,
    )


def read_tesseract_crop(
    crop: CriticalCrop,
    *,
    executable: str,
    engine_version: str,
    runner: _Runner = _subprocess_runner,
    timeout_seconds: float = 5.0,
) -> CropRead:
    """Read one critical crop with Tesseract without content-aware correction."""

    if not executable.strip():
        raise ValueError("Tesseract executable must be non-empty")
    if not engine_version.strip():
        raise ValueError("Tesseract engine_version must be non-empty")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    args = [
        executable,
        "stdin",
        "stdout",
        "-l",
        "eng",
        "--psm",
        "7",
    ]
    try:
        completed = runner(
            args,
            input=crop.png_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
            shell=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        raise EngineRuntimeError("Tesseract execution failed") from exc

    if completed.returncode != 0:
        raise EngineRuntimeError(
            f"Tesseract exited with non-zero status {completed.returncode}"
        )
    try:
        text = completed.stdout.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise EngineRuntimeError("Tesseract stdout was not valid UTF-8") from exc

    return CropRead(
        text=text,
        engine_name="tesseract",
        engine_version=engine_version,
        executable=executable,
        crop_sha256=crop.crop_sha256,
    )


def _installed_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def probe_runtime(
    *,
    package_versions: Mapping[str, str] | None = None,
    tesseract_path: str | object | None = ...,
) -> RuntimeProbe:
    """Report runtime availability without importing PaddleOCR or ONNX Runtime."""

    if package_versions is None:
        paddleocr_version = _installed_version("paddleocr")
        onnxruntime_version = _installed_version("onnxruntime")
    else:
        paddleocr_version = package_versions.get("paddleocr")
        onnxruntime_version = package_versions.get("onnxruntime")

    resolved_tesseract = shutil.which("tesseract") if tesseract_path is ... else tesseract_path
    if resolved_tesseract is not None and not isinstance(resolved_tesseract, str):
        raise ValueError("tesseract_path must be a string or None")

    return RuntimeProbe(
        paddleocr_version=paddleocr_version,
        onnxruntime_version=onnxruntime_version,
        tesseract_available=resolved_tesseract is not None,
        tesseract_path=resolved_tesseract,
    )
