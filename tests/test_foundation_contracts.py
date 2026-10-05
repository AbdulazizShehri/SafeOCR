from __future__ import annotations

import json
from typing import cast

import pytest

from safeocr.contracts import (
    BoundingBox,
    CandidateSpan,
    Criticality,
    DecisionRecord,
    DecisionState,
    EvidenceRecord,
    LabFieldCandidate,
    PageAsset,
    VerificationSignals,
    decide,
    export_allowed,
)

VALID_SHA = "a" * 64


def _signals(**overrides: bool) -> VerificationSignals:
    values = {
        "candidate_present": True,
        "visual_grounded": True,
        "independent_agreement": True,
        "perturbation_stable": True,
        "structural_association": True,
        "numeric_parse_unambiguous": True,
        "unit_valid": True,
        "patient_linkage_unambiguous": True,
        "runtime_healthy": True,
    }
    values.update(overrides)
    return VerificationSignals(**values)


def test_bounding_box_rejects_inverted_coordinates() -> None:
    with pytest.raises(ValueError):
        BoundingBox(x1=10, y1=10, x2=5, y2=20)


def test_page_asset_rejects_invalid_sha256() -> None:
    with pytest.raises(ValueError):
        PageAsset(
            document_sha256="not-a-sha",
            page_index=0,
            width_px=100,
            height_px=100,
            page_sha256=VALID_SHA,
        )


@pytest.mark.parametrize(
    ("text", "engine_name", "engine_version"),
    [
        ("", "paddleocr", "1"),
        ("6.8", "", "1"),
        ("6.8", "paddleocr", ""),
    ],
)
def test_candidate_span_requires_engine_identity_and_text(
    text: str, engine_name: str, engine_version: str
) -> None:
    page = PageAsset(VALID_SHA, 0, 100, 100, VALID_SHA)
    box = BoundingBox(1, 1, 20, 20)
    with pytest.raises(ValueError):
        CandidateSpan(
            page=page,
            box=box,
            text=text,
            engine_name=engine_name,
            engine_version=engine_version,
        )


@pytest.mark.parametrize(
    ("signals", "expected"),
    [
        (_signals(candidate_present=False), DecisionState.ABSTAINED),
        (_signals(visual_grounded=False), DecisionState.ABSTAINED),
        (_signals(runtime_healthy=False), DecisionState.ABSTAINED),
        (_signals(independent_agreement=False), DecisionState.REVIEW_REQUIRED),
        (_signals(perturbation_stable=False), DecisionState.REVIEW_REQUIRED),
        (_signals(structural_association=False), DecisionState.REVIEW_REQUIRED),
        (_signals(numeric_parse_unambiguous=False), DecisionState.REVIEW_REQUIRED),
        (_signals(unit_valid=False), DecisionState.REVIEW_REQUIRED),
        (_signals(patient_linkage_unambiguous=False), DecisionState.REVIEW_REQUIRED),
        (_signals(), DecisionState.VERIFIED_AUTO),
    ],
)
def test_fail_closed_decision_policy(
    signals: VerificationSignals, expected: DecisionState
) -> None:
    assert decide(signals, criticality=Criticality.CRITICAL).state is expected


def test_export_gate_requires_a_consistent_evidence_record() -> None:
    verified_signals = _signals()
    verified_field = _field()
    verified = EvidenceRecord(
        field=verified_field,
        signals=verified_signals,
        decision=decide(verified_signals, criticality=verified_field.criticality),
        policy_version="f1-v1",
    )

    review_signals = _signals(unit_valid=False)
    review_field = _field()
    review = EvidenceRecord(
        field=review_field,
        signals=review_signals,
        decision=decide(review_signals, criticality=review_field.criticality),
        policy_version="f1-v1",
    )

    assert export_allowed(verified) is True
    assert export_allowed(review) is False


def test_verification_signals_reject_non_boolean_values() -> None:
    with pytest.raises(ValueError):
        VerificationSignals(
            candidate_present=cast(bool, "true"),
            visual_grounded=True,
            independent_agreement=True,
            perturbation_stable=True,
            structural_association=True,
            numeric_parse_unambiguous=True,
            unit_valid=True,
            patient_linkage_unambiguous=True,
            runtime_healthy=True,
        )


def test_decision_serialization_is_deterministic() -> None:
    decision = decide(_signals(), criticality=Criticality.CRITICAL)
    first = decision.to_json()
    second = decision.to_json()

    assert first == second
    payload = json.loads(first)
    assert payload["state"] == "VERIFIED_AUTO"
    assert payload["failed_gates"] == []


def _field(*, document_sha: str = VALID_SHA) -> LabFieldCandidate:
    page = PageAsset(document_sha, 0, 100, 100, VALID_SHA)
    analyte = CandidateSpan(
        page=page,
        box=BoundingBox(1, 1, 30, 15),
        text="Potassium",
        engine_name="paddleocr",
        engine_version="1",
    )
    value = CandidateSpan(
        page=page,
        box=BoundingBox(31, 1, 50, 15),
        text="6.8",
        engine_name="paddleocr",
        engine_version="1",
    )
    return LabFieldCandidate(
        analyte_text="Potassium",
        value_text="6.8",
        unit_text="mmol/L",
        criticality=Criticality.CRITICAL,
        source_spans=(analyte, value),
    )


def test_lab_field_rejects_source_spans_from_multiple_documents() -> None:
    page_a = PageAsset("a" * 64, 0, 100, 100, "c" * 64)
    page_b = PageAsset("b" * 64, 0, 100, 100, "d" * 64)
    span_a = CandidateSpan(
        page_a, BoundingBox(1, 1, 10, 10), "Potassium", "paddleocr", "1"
    )
    span_b = CandidateSpan(page_b, BoundingBox(20, 1, 30, 10), "6.8", "paddleocr", "1")

    with pytest.raises(ValueError):
        LabFieldCandidate(
            analyte_text="Potassium",
            value_text="6.8",
            unit_text="mmol/L",
            criticality=Criticality.CRITICAL,
            source_spans=(span_a, span_b),
        )


def test_evidence_record_rejects_inconsistent_decision() -> None:
    signals = _signals()
    wrong = DecisionRecord(
        state=DecisionState.REVIEW_REQUIRED,
        criticality=Criticality.CRITICAL,
        failed_gates=("unit_valid",),
    )

    with pytest.raises(ValueError):
        EvidenceRecord(
            field=_field(),
            signals=signals,
            decision=wrong,
            policy_version="f1-v1",
        )


def test_evidence_record_serialization_is_deterministic() -> None:
    signals = _signals()
    field = _field()
    decision = decide(signals, criticality=field.criticality)
    evidence = EvidenceRecord(
        field=field,
        signals=signals,
        decision=decision,
        policy_version="f1-v1",
    )

    first = evidence.to_json()
    second = evidence.to_json()

    assert first == second
    payload = json.loads(first)
    assert payload["policy_version"] == "f1-v1"
    assert payload["decision"]["state"] == "VERIFIED_AUTO"
    assert payload["field"]["value_text"] == "6.8"
    assert payload["field"]["source_spans"][0]["page"]["document_sha256"] == VALID_SHA
