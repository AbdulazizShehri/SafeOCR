from __future__ import annotations

from pathlib import Path

from safeocr.clinocr_eval import summary_stats, word_error_rate

_ROOT = Path(__file__).resolve().parents[1]
_RUNNER = _ROOT / "scripts" / "run_clinocr_external_ocr.py"
_SCORER = _ROOT / "scripts" / "score_clinocr_external_wer.py"
_PROTOCOL = _ROOT / "paper" / "EXTERNAL_VALIDATION_PROTOCOL.md"


def test_word_error_rate_matches_expected_edit_operations() -> None:
    exact = word_error_rate("a b c", "a b c")
    assert exact.wer == 0.0

    substitution = word_error_rate("a b c", "a x c")
    assert substitution.wer == 1 / 3
    assert substitution.substitution == 1 / 3
    assert substitution.deletion == 0.0
    assert substitution.insertion == 0.0

    deletion = word_error_rate("a b c", "a c")
    assert deletion.wer == 1 / 3
    assert deletion.deletion == 1 / 3

    insertion = word_error_rate("a b", "a x b")
    assert insertion.wer == 0.5
    assert insertion.insertion == 0.5


def test_summary_stats_match_official_baseline_formula() -> None:
    stats = summary_stats((0.0, 0.5, 1.0))
    assert stats.n == 3
    assert stats.mean == 0.5
    assert stats.median == 0.5
    assert stats.q1 == 0.25
    assert stats.q3 == 0.75
    assert stats.minimum == 0.0
    assert stats.maximum == 1.0


def test_ocr_runner_cannot_open_ground_truth() -> None:
    source = _RUNNER.read_text(encoding="utf-8")
    assert "ground_truth_path" not in source
    assert "ground_truth/" not in source
    assert '"ground_truth_opened": False' in source
    assert '"tuning_performed": False' in source
    assert '"working_tree_dirty": working_tree_dirty' in source
    assert "external OCR requires a clean exact-head working tree" in source
    assert 'encoding="utf-8"' in source
    assert 'errors="replace"' in source
    assert "328" in source


def test_scorer_requires_frozen_ocr_attestation_before_ground_truth() -> None:
    source = _SCORER.read_text(encoding="utf-8")
    attestation_index = source.index('metadata.get("ground_truth_opened")')
    truth_index = source.index("record.ground_truth_path")
    assert attestation_index < truth_index
    assert 'metadata.get("tuning_performed")' in source


def test_protocol_freezes_no_tuning_and_field_level_claim_boundary() -> None:
    text = _PROTOCOL.read_text(encoding="utf-8")
    assert "FROZEN BEFORE OUTCOME INSPECTION" in text
    assert "no threshold tuning" in text
    assert "not a safeocr field-level safety validation" in text.lower()
    assert "328 test/evaluation documents" in text
