from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from safeocr.contracts import (
    BoundingBox,
    CandidateSpan,
    Criticality,
    LabFieldCandidate,
    PageAsset,
)
from safeocr.evaluation import match_span_to_truth_region, wilson_interval
from safeocr.labgold import TruthRegion
from safeocr.ma2023 import Ma2023Region, laboratory_rows, load_ma2023_annotations
from safeocr.ocr import (
    CriticalCrop,
    EngineFingerprint,
    PageOcrResult,
    extract_critical_crop,
    read_tesseract_crop,
)
from safeocr.verification import (
    FieldEvidenceInput,
    PerturbationRead,
    UnitStatus,
    independent_agreement,
    make_approved_perturbations,
    normalize_evidence_text,
    parse_critical_value,
    perturbation_stable,
    structural_association,
    validate_ucum_unit,
    visual_grounding,
)


@dataclass(frozen=True, slots=True)
class Counts:
    eligible: int = 0
    value_span_matched: int = 0
    context_spans_matched: int = 0
    primary_value_exact: int = 0
    primary_field_exact: int = 0
    independent_agreement: int = 0
    perturbation_stable: int = 0
    structural_association: int = 0
    unit_valid: int = 0
    component_pass: int = 0
    unsafe_component_pass: int = 0
    runtime_failure: int = 0


def _resolve_tesseract() -> Path:
    for candidate in (
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ):
        if candidate.is_file():
            return candidate
    raise RuntimeError("Tesseract executable not found")


def _tesseract_version(executable: Path) -> str:
    completed = subprocess.run(
        [str(executable), "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return completed.stdout.splitlines()[0].strip()


def _page_result(path: Path) -> PageOcrResult:
    raw = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
    page_raw = cast(dict[str, object], raw["page"])
    fp_raw = cast(dict[str, object], raw["fingerprint"])
    page = PageAsset(
        document_sha256=str(page_raw["document_sha256"]),
        page_index=int(str(page_raw["page_index"])),
        width_px=int(str(page_raw["width_px"])),
        height_px=int(str(page_raw["height_px"])),
        page_sha256=str(page_raw["page_sha256"]),
    )
    fingerprint = EngineFingerprint(
        engine_name=str(fp_raw["engine_name"]),
        engine_version=str(fp_raw["engine_version"]),
        model_name=str(fp_raw["model_name"]),
        backend=str(fp_raw["backend"]),
    )
    raw_spans = cast(list[object], raw["spans"])
    spans: list[CandidateSpan] = []
    for raw_item in raw_spans:
        if not isinstance(raw_item, dict):
            raise ValueError("OCR span must be an object")
        item = cast(dict[str, object], raw_item)
        raw_box = item["box"]
        if not isinstance(raw_box, dict):
            raise ValueError("OCR span box must be an object")
        box = cast(dict[str, object], raw_box)
        raw_confidence = item["confidence"]
        confidence = (
            None
            if raw_confidence is None
            else float(str(raw_confidence))
        )
        spans.append(
            CandidateSpan(
                page=page,
                box=BoundingBox(
                    x1=int(str(box["x1"])),
                    y1=int(str(box["y1"])),
                    x2=int(str(box["x2"])),
                    y2=int(str(box["y2"])),
                ),
                text=str(item["text"]),
                engine_name=fingerprint.engine_name,
                engine_version=fingerprint.engine_version,
                confidence=confidence,
            )
        )
    return PageOcrResult(page=page, fingerprint=fingerprint, spans=tuple(spans))


def _truth_region(region: Ma2023Region) -> TruthRegion:
    return TruthRegion(
        role=f"column-{region.column_no}",
        row_id=str(region.row_no),
        text=region.text,
        box=region.box,
    )


def _same(left: str, right: str) -> bool:
    return normalize_evidence_text(left) == normalize_evidence_text(right)


def _perturbation_reads(
    crop: CriticalCrop,
    *,
    tesseract: Path,
    tesseract_version: str,
) -> tuple[PerturbationRead, ...]:
    reads: list[PerturbationRead] = []
    for image in make_approved_perturbations(crop):
        variant = CriticalCrop(
            source_page=crop.source_page,
            requested_box=crop.requested_box,
            crop_box=crop.crop_box,
            png_bytes=image.png_bytes,
            crop_sha256=image.image_sha256,
        )
        read = read_tesseract_crop(
            variant,
            executable=str(tesseract),
            engine_version=tesseract_version,
            timeout_seconds=10.0,
        )
        reads.append(
            PerturbationRead(
                name=image.name,
                image_sha256=image.image_sha256,
                text=read.text,
                runtime_healthy=True,
            )
        )
    return tuple(reads)


def _increment(counts: Counts, **updates: int) -> Counts:
    payload = asdict(counts)
    for key, value in updates.items():
        payload[key] = int(payload[key]) + value
    return Counts(**payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    metadata = json.loads((args.ocr / "_run_metadata.json").read_text(encoding="utf-8"))
    if metadata.get("annotation_source_opened") is not False:
        raise RuntimeError("OCR metadata must attest annotation_source_opened=false")
    if metadata.get("tuning_performed") is not False:
        raise RuntimeError("OCR metadata must attest tuning_performed=false")
    if metadata.get("working_tree_dirty") is not False:
        raise RuntimeError("OCR run must originate from a clean exact head")

    documents = load_ma2023_annotations(args.labels)
    tesseract = _resolve_tesseract()
    tesseract_version = _tesseract_version(tesseract)

    totals = Counts()
    strata = {"scan": Counts(), "illumination": Counts()}
    exclusions: Counter[str] = Counter()
    rows_out: list[dict[str, object]] = []

    for document in documents:
        kind = "scan" if document.filename.startswith("scan_") else "illumination"
        result = _page_result(args.ocr / f"{Path(document.filename).stem}.json")
        image_path = args.images / document.filename
        image_bytes = image_path.read_bytes()

        for row in laboratory_rows(document):
            analyte_gold = row.get(2)
            value_gold = row.get(3)
            unit_gold = row.get(4)
            if analyte_gold is None or not analyte_gold.text:
                exclusions["missing_analyte"] += 1
                continue
            if value_gold is None or not value_gold.text:
                exclusions["missing_value"] += 1
                continue
            if parse_critical_value(value_gold.text) is None:
                exclusions["unsupported_gold_value"] += 1
                continue
            if unit_gold is None or not unit_gold.text:
                exclusions["missing_unit"] += 1
                continue

            totals = _increment(totals, eligible=1)
            strata[kind] = _increment(strata[kind], eligible=1)

            analyte = match_span_to_truth_region(result, _truth_region(analyte_gold))
            value = match_span_to_truth_region(result, _truth_region(value_gold))
            unit = match_span_to_truth_region(result, _truth_region(unit_gold))

            if value is None:
                rows_out.append(
                    {
                        "filename": document.filename,
                        "row": value_gold.row_no,
                        "stratum": kind,
                        "matched": False,
                        "component_pass": False,
                    }
                )
                continue

            totals = _increment(totals, value_span_matched=1)
            strata[kind] = _increment(strata[kind], value_span_matched=1)
            value_exact = _same(value.text, value_gold.text)
            if value_exact:
                totals = _increment(totals, primary_value_exact=1)
                strata[kind] = _increment(strata[kind], primary_value_exact=1)

            if analyte is None or unit is None:
                rows_out.append(
                    {
                        "filename": document.filename,
                        "row": value_gold.row_no,
                        "stratum": kind,
                        "matched": True,
                        "value_exact": value_exact,
                        "component_pass": False,
                    }
                )
                continue

            totals = _increment(totals, context_spans_matched=1)
            strata[kind] = _increment(strata[kind], context_spans_matched=1)
            field_exact = (
                value_exact
                and _same(analyte.text, analyte_gold.text)
                and _same(unit.text, unit_gold.text)
            )
            if field_exact:
                totals = _increment(totals, primary_field_exact=1)
                strata[kind] = _increment(strata[kind], primary_field_exact=1)

            field = LabFieldCandidate(
                analyte_text=analyte.text,
                value_text=value.text,
                unit_text=unit.text,
                criticality=Criticality.CRITICAL,
                source_spans=(analyte, value, unit),
            )
            crop = extract_critical_crop(
                image_bytes,
                result.page,
                value.box,
                padding_px=6,
            )
            binding = FieldEvidenceInput(
                field=field,
                analyte_span=analyte,
                value_span=value,
                unit_span=unit,
                value_crop=crop,
            )

            try:
                independent = read_tesseract_crop(
                    crop,
                    executable=str(tesseract),
                    engine_version=tesseract_version,
                    timeout_seconds=10.0,
                )
                perturbations = _perturbation_reads(
                    crop,
                    tesseract=tesseract,
                    tesseract_version=tesseract_version,
                )
                independent_ok = independent_agreement(
                    field.value_text,
                    independent,
                    expected_crop_sha256=crop.crop_sha256,
                )
                perturbation_ok = perturbation_stable(
                    field.value_text,
                    perturbations,
                    source_crop=crop,
                )
            except Exception:
                totals = _increment(totals, runtime_failure=1)
                strata[kind] = _increment(strata[kind], runtime_failure=1)
                rows_out.append(
                    {
                        "filename": document.filename,
                        "row": value_gold.row_no,
                        "stratum": kind,
                        "matched": True,
                        "value_exact": value_exact,
                        "field_exact": field_exact,
                        "component_pass": False,
                        "runtime_failure": True,
                    }
                )
                continue

            structural_ok = structural_association(binding)
            grounding_ok = visual_grounding(binding)
            numeric_ok = parse_critical_value(field.value_text) is not None
            unit_status = validate_ucum_unit(field.unit_text).status
            unit_ok = unit_status is UnitStatus.VALID
            component_pass = all(
                (
                    grounding_ok,
                    independent_ok,
                    perturbation_ok,
                    structural_ok,
                    numeric_ok,
                    unit_ok,
                )
            )

            update = {
                "independent_agreement": int(independent_ok),
                "perturbation_stable": int(perturbation_ok),
                "structural_association": int(structural_ok),
                "unit_valid": int(unit_ok),
                "component_pass": int(component_pass),
                "unsafe_component_pass": int(component_pass and not value_exact),
            }
            totals = _increment(totals, **update)
            strata[kind] = _increment(strata[kind], **update)
            rows_out.append(
                {
                    "filename": document.filename,
                    "row": value_gold.row_no,
                    "stratum": kind,
                    "matched": True,
                    "value_exact": value_exact,
                    "field_exact": field_exact,
                    "independent_agreement": independent_ok,
                    "perturbation_stable": perturbation_ok,
                    "structural_association": structural_ok,
                    "unit_valid": unit_ok,
                    "component_pass": component_pass,
                    "unsafe_component_pass": component_pass and not value_exact,
                }
            )

    interval = wilson_interval(totals.unsafe_component_pass, totals.component_pass)
    payload = {
        "schema_version": 1,
        "dataset": "Ma2023-public-laboratory-reports",
        "design": "oracle-localised verifier component evaluation",
        "ocr_run_metadata": metadata,
        "tesseract_version": tesseract_version,
        "counts": asdict(totals),
        "strata": {key: asdict(value) for key, value in strata.items()},
        "exclusions": dict(sorted(exclusions.items())),
        "unsafe_component_pass_interval_95": interval,
        "rows": rows_out,
        "claim_boundary": {
            "end_to_end_extraction": False,
            "full_safeocr_policy": False,
            "patient_linkage": False,
            "fhir_mapping": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"counts": asdict(totals), "interval": interval}, sort_keys=True))


if __name__ == "__main__":
    main()
