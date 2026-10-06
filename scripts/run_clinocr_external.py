from __future__ import annotations

import argparse
import csv
import importlib
import importlib.metadata
import json
import math
import random
import statistics
import subprocess
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol, cast

DATASET_SHA256 = "ce1d231138050abf7f458ba5e6bd75c6ee2f3832b72f22296843da4c5ba45457"
BASELINE_COMMIT = "306e5502c9d4f5de39bb03689a8d9bc5df101031"
SUBSETS = ("normal", "handwriting", "poor", "rotated", "tables", "mixed")
BOOTSTRAP_SEED = 20261006
BOOTSTRAP_REPLICATES = 10000


class _PaddleResult(Protocol):
    json: Mapping[str, object]


class _PaddlePipeline(Protocol):
    def predict(self, input: str) -> Iterable[_PaddleResult]: ...


class _PaddleFactory(Protocol):
    def __call__(self, **kwargs: object) -> _PaddlePipeline: ...


@dataclass(frozen=True, slots=True)
class EvalCase:
    subset: str
    template: int
    sample: int
    doc_id: str
    image_path: Path
    truth_path: Path


@dataclass(frozen=True, slots=True)
class WerResult:
    wer: float
    sub: float
    deletion: float
    insertion: float


def _word_error_rate(gold: str, pred: str) -> WerResult:
    """Match ClinOCR-Bench baseline whitespace-token WER semantics."""
    ref = gold.split()
    hyp = pred.split()
    if not ref:
        value = 0.0 if not hyp else math.inf
        return WerResult(value, value, value, value)

    n, m = len(ref), len(hyp)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j - 1],
                    dp[i - 1][j],
                    dp[i][j - 1],
                )

    substitutions = deletions = insertions = 0
    i, j = n, m
    while i > 0 or j > 0:
        if (
            i > 0
            and j > 0
            and ref[i - 1] == hyp[j - 1]
            and dp[i][j] == dp[i - 1][j - 1]
        ):
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            substitutions += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            deletions += 1
            i -= 1
        else:
            insertions += 1
            j -= 1

    return WerResult(
        wer=(substitutions + deletions + insertions) / n,
        sub=substitutions / n,
        deletion=deletions / n,
        insertion=insertions / n,
    )


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


def _paddle_text(pipeline: _PaddlePipeline, image_path: Path) -> str:
    results = list(pipeline.predict(str(image_path)))
    if len(results) != 1:
        raise RuntimeError(f"expected one PaddleOCR page result, got {len(results)}")
    raw = results[0].json
    res = raw.get("res")
    if not isinstance(res, Mapping):
        raise RuntimeError("PaddleOCR result missing res mapping")
    result_mapping = cast(Mapping[str, object], res)
    texts_raw = result_mapping.get("rec_texts")
    if not isinstance(texts_raw, Sequence) or isinstance(
        texts_raw, (str, bytes, bytearray)
    ):
        raise RuntimeError("PaddleOCR result missing rec_texts sequence")
    texts = cast(Sequence[object], texts_raw)
    normalized: list[str] = []
    for item in texts:
        if not isinstance(item, str):
            raise RuntimeError("PaddleOCR rec_texts contains non-string item")
        if item.strip():
            normalized.append(item.strip())
    return "\n".join(normalized)


def _tesseract_text(executable: Path, image_path: Path) -> str:
    completed = subprocess.run(
        [str(executable), str(image_path), "stdout", "-l", "eng"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        timeout=120,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Tesseract failed with {completed.returncode}: {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def _find_unique(directory: Path, pattern: str) -> Path:
    matches = tuple(directory.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one match for {directory / pattern}, got {len(matches)}"
        )
    return matches[0]


def _load_cases(root: Path) -> tuple[EvalCase, ...]:
    lookup = root / "oneshot_lookup.csv"
    cases: list[EvalCase] = []
    with lookup.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["role"] != "eval":
                continue
            subset = row["subset"]
            if subset not in SUBSETS:
                raise RuntimeError(f"unexpected subset: {subset}")
            template = int(row["template"])
            sample = int(row["sample"])
            stem = f"template_{template}_sample_{sample}_"
            image_path = _find_unique(root / "scans" / subset, f"{stem}*.jpg")
            truth_path = _find_unique(root / "ground_truth" / subset, f"{stem}*.txt")
            doc_id = f"{subset}_t{template}_s{sample}"
            cases.append(
                EvalCase(
                    subset=subset,
                    template=template,
                    sample=sample,
                    doc_id=doc_id,
                    image_path=image_path,
                    truth_path=truth_path,
                )
            )
    if len(cases) != 328:
        raise RuntimeError(f"expected 328 evaluation cases, got {len(cases)}")
    return tuple(cases)


def _bootstrap_mean_ci(values: Sequence[float]) -> tuple[float, float]:
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(values)
    means: list[float] = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(statistics.fmean(sample))
    means.sort()
    lo = means[int(0.025 * BOOTSTRAP_REPLICATES)]
    hi = means[int(0.975 * BOOTSTRAP_REPLICATES) - 1]
    return lo, hi


def _summarize(rows: Sequence[dict[str, object]], engine: str) -> dict[str, object]:
    selected = [row for row in rows if row["engine"] == engine]
    result: dict[str, object] = {
        "engine": engine,
        "document_count": len(selected),
        "failure_count": sum(bool(row["failed"]) for row in selected),
    }
    by_subset: dict[str, dict[str, object]] = {}
    for subset in SUBSETS:
        subset_rows = [row for row in selected if row["subset"] == subset]
        wers = [float(cast(float, row["wer"])) for row in subset_rows]
        ordered = sorted(wers)
        q1 = statistics.median(ordered[: len(ordered) // 2])
        q3 = statistics.median(ordered[(len(ordered) + 1) // 2 :])
        by_subset[subset] = {
            "n": len(wers),
            "mean_wer": statistics.fmean(wers),
            "median_wer": statistics.median(wers),
            "q1_wer": q1,
            "q3_wer": q3,
            "failure_count": sum(bool(row["failed"]) for row in subset_rows),
        }
    result["subsets"] = by_subset

    all_wers = [float(cast(float, row["wer"])) for row in selected]
    ci = _bootstrap_mean_ci(all_wers)
    result["overall"] = {
        "mean_wer": statistics.fmean(all_wers),
        "median_wer": statistics.median(all_wers),
        "bootstrap_mean_ci95": [ci[0], ci[1]],
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
    }
    return result


def _load_existing(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise RuntimeError("checkpoint row must be a JSON object")
            rows.append(cast(dict[str, object], value))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run frozen ClinOCR-Bench external OCR evaluation")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--tesseract",
        type=Path,
        default=Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    )
    args = parser.parse_args()

    cases = _load_cases(args.dataset_root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = args.output_dir / "document_results.jsonl"
    rows = _load_existing(checkpoint)
    completed = {(str(row["doc_id"]), str(row["engine"])) for row in rows}

    paddle = _build_paddle_pipeline()
    paddle_version = importlib.metadata.version("paddleocr")
    tesseract_version = subprocess.run(
        [str(args.tesseract), "--version"],
        check=True,
        capture_output=True,
        text=True,
        shell=False,
        timeout=10,
    ).stdout.splitlines()[0].strip()

    for case_index, case in enumerate(cases, start=1):
        truth = case.truth_path.read_text(encoding="utf-8").strip()
        for engine in ("paddleocr", "tesseract"):
            key = (case.doc_id, engine)
            if key in completed:
                continue

            started = time.perf_counter()
            failed = False
            error: str | None = None
            try:
                if engine == "paddleocr":
                    prediction = _paddle_text(paddle, case.image_path)
                else:
                    prediction = _tesseract_text(args.tesseract, case.image_path)
            except Exception as exc:
                failed = True
                error = f"{type(exc).__name__}: {exc}"
                prediction = ""
            elapsed = time.perf_counter() - started
            score = _word_error_rate(truth, prediction)
            row: dict[str, object] = {
                "doc_id": case.doc_id,
                "subset": case.subset,
                "template": case.template,
                "sample": case.sample,
                "engine": engine,
                "failed": failed,
                "error": error,
                "runtime_seconds": elapsed,
                **asdict(score),
            }
            with checkpoint.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
            prediction_dir = args.output_dir / "predictions" / engine / case.subset
            prediction_dir.mkdir(parents=True, exist_ok=True)
            (prediction_dir / f"{case.doc_id}.txt").write_text(
                prediction + "\n", encoding="utf-8", newline="\n"
            )
            rows.append(row)
            completed.add(key)
        print(f"{case_index}/328 {case.doc_id}", flush=True)

    paddle_summary = _summarize(rows, "paddleocr")
    tesseract_summary = _summarize(rows, "tesseract")

    by_key = {(str(row["doc_id"]), str(row["engine"])): row for row in rows}
    deltas: list[float] = []
    paddle_better = tesseract_better = ties = 0
    for case in cases:
        p = float(cast(float, by_key[(case.doc_id, "paddleocr")]["wer"]))
        t = float(cast(float, by_key[(case.doc_id, "tesseract")]["wer"]))
        deltas.append(p - t)
        if p < t:
            paddle_better += 1
        elif t < p:
            tesseract_better += 1
        else:
            ties += 1

    summary = {
        "schema_version": 1,
        "experiment": "clinocr_external_ocr_generalization",
        "preregistered_protocol_commit": "5a396d7",
        "dataset": {
            "name": "ClinOCR-Bench",
            "version": "v1.0",
            "sha256": DATASET_SHA256,
            "evaluation_documents": len(cases),
        },
        "metric_semantics": {
            "name": "word_error_rate",
            "official_baseline_commit": BASELINE_COMMIT,
            "tokenization": "python_whitespace_split",
        },
        "runtime": {
            "paddleocr_version": paddle_version,
            "paddle_model": "PP-OCRv6_small_det+PP-OCRv6_small_rec",
            "paddle_backend": "onnxruntime-cpu",
            "paddle_recognition_batch_size": 1,
            "tesseract_version": tesseract_version,
        },
        "paddleocr": paddle_summary,
        "tesseract": tesseract_summary,
        "paired_comparison": {
            "mean_wer_delta_paddle_minus_tesseract": statistics.fmean(deltas),
            "median_wer_delta_paddle_minus_tesseract": statistics.median(deltas),
            "paddle_lower_wer_count": paddle_better,
            "tesseract_lower_wer_count": tesseract_better,
            "tie_count": ties,
        },
        "interpretation_boundary": [
            "This experiment measures full-document OCR transcription generalization only.",
            (
                "ClinOCR-Bench transcript truth does not support SafeOCR critical-field "
                "unsafe-accept or verified-coverage claims."
            ),
            "No ClinOCR-Bench evaluation outcome was used to tune the frozen SafeOCR v0.1 policy.",
        ],
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
