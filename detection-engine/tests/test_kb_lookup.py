"""
Unit tests for detection-engine/stages/kb_lookup.py
=====================================================

All tests use a mocked VectorRetriever — no real FAISS index required.

Covered scenarios
-----------------
1. Clear hit above threshold  → hit=True, best_score high, passages populated.
2. Near-miss below threshold  → hit=False, passages STILL returned (for debug).
3. Empty KB result            → hit=False, passages=[], best_score=0.0.
4. Source label builder       → statute and case metadata produce correct strings.
5. Score clamping             → out-of-range FAISS scores are clamped to [0, 1].
6. Custom threshold override  → threshold kwarg overrides KB_HIT_THRESHOLD.
7. Logging                    → logger.info is called once per lookup.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── resolve imports ──────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_DETECTION_ENGINE = _HERE.parent
_PROJECT_ROOT = _DETECTION_ENGINE.parent

for _p in (_PROJECT_ROOT, _DETECTION_ENGINE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from stages.kb_lookup import (       # noqa: E402
    KB_HIT_THRESHOLD,
    KBLookupResult,
    KBPassage,
    _build_source,
    kb_lookup,
)
from shared.schemas import Claim, ClaimType  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _claim(text: str = "Section 43A imposes strict liability.", cid: str = "claim_001") -> Claim:
    return Claim(id=cid, text=text, type=ClaimType.SECTION_REF, span=(0, len(text)))


def _mock_retriever(raw_results: list[dict]) -> MagicMock:
    """Return a mock VectorRetriever whose retrieve_with_metadata returns raw_results."""
    mock = MagicMock()
    mock.retrieve_with_metadata.return_value = raw_results
    return mock


# Representative FAISS metadata dicts (matching build_index.py schema)
_STATUTE_ROW = {
    "text": "Section 43A: Compensation for failure to protect data. "
            "Where a body corporate fails to implement reasonable security practices...",
    "source_type": "statute",
    "ref_id": 12,
    "section_number": "43A",
    "act_name": "Information Technology Act 2000",
    "status": "in_force",
    "score": 0.87,
}

_CASE_ROW = {
    "text": "K.S. Puttaswamy v. Union of India (2017): Privacy is a fundamental right.",
    "source_type": "case",
    "ref_id": 3,
    "case_name": "K.S. Puttaswamy v. Union of India",
    "citation": "(2017) 10 SCC 1",
    "related_section": "None",
    "score": 0.72,
}

_LOW_SCORE_ROW = {
    "text": "Some tangentially related passage.",
    "source_type": "statute",
    "ref_id": 99,
    "section_number": "2",
    "act_name": "Information Technology Act 2000",
    "status": "in_force",
    "score": 0.31,  # below KB_HIT_THRESHOLD
}


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — Clear hit above threshold
# ─────────────────────────────────────────────────────────────────────────────

class TestClearHit:
    def test_hit_is_true(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([_STATUTE_ROW]))
        assert result.hit is True

    def test_returns_kb_lookup_result(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([_STATUTE_ROW]))
        assert isinstance(result, KBLookupResult)

    def test_best_score_matches_top_result(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([_STATUTE_ROW]))
        assert abs(result.best_score - 0.87) < 1e-9

    def test_passage_count_matches_results(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([_STATUTE_ROW, _CASE_ROW]))
        assert len(result.passages) == 2

    def test_passage_text_preserved(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([_STATUTE_ROW]))
        assert "Section 43A" in result.passages[0].text

    def test_passage_score_set(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([_STATUTE_ROW]))
        assert abs(result.passages[0].score - 0.87) < 1e-9

    def test_passage_source_is_statute_label(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([_STATUTE_ROW]))
        assert result.passages[0].source == "statute:43A"

    def test_passage_metadata_excludes_text_key(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([_STATUTE_ROW]))
        assert "text" not in result.passages[0].metadata

    def test_metadata_contains_source_type(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([_STATUTE_ROW]))
        assert result.passages[0].metadata["source_type"] == "statute"

    def test_retriever_called_with_correct_args(self):
        retriever = _mock_retriever([_STATUTE_ROW])
        claim = _claim()
        kb_lookup(claim, top_k=5, retriever=retriever)
        retriever.retrieve_with_metadata.assert_called_once_with(claim.text, top_k=5)


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — Near-miss below threshold
# ─────────────────────────────────────────────────────────────────────────────

class TestNearMiss:
    def test_hit_is_false(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([_LOW_SCORE_ROW]))
        assert result.hit is False

    def test_passages_still_returned(self):
        """Near-misses must be visible for debugging even when hit=False."""
        result = kb_lookup(_claim(), retriever=_mock_retriever([_LOW_SCORE_ROW]))
        assert len(result.passages) == 1

    def test_best_score_reflects_low_score(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([_LOW_SCORE_ROW]))
        assert abs(result.best_score - 0.31) < 1e-9

    def test_passage_text_preserved_on_miss(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([_LOW_SCORE_ROW]))
        assert "tangentially related" in result.passages[0].text

    def test_multiple_near_misses_all_returned(self):
        result = kb_lookup(
            _claim(),
            retriever=_mock_retriever([_LOW_SCORE_ROW, _LOW_SCORE_ROW]),
        )
        assert len(result.passages) == 2


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — Empty KB result
# ─────────────────────────────────────────────────────────────────────────────

class TestEmptyKB:
    def test_hit_is_false(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([]))
        assert result.hit is False

    def test_passages_is_empty_list(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([]))
        assert result.passages == []

    def test_best_score_is_zero(self):
        result = kb_lookup(_claim(), retriever=_mock_retriever([]))
        assert result.best_score == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — _build_source label builder
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildSource:
    def test_statute_source_uses_section_number(self):
        assert _build_source(_STATUTE_ROW) == "statute:43A"

    def test_case_source_uses_case_name(self):
        assert _build_source(_CASE_ROW) == "case:K.S. Puttaswamy v. Union of India"

    def test_unknown_source_type_fallback(self):
        label = _build_source({"source_type": "treaty", "ref_id": 7})
        assert label == "treaty:7"

    def test_statute_fallback_to_ref_id_when_no_section_number(self):
        label = _build_source({"source_type": "statute", "ref_id": 42})
        assert label == "statute:42"

    def test_case_fallback_to_citation_when_no_case_name(self):
        label = _build_source({"source_type": "case", "citation": "(2017) 10 SCC 1", "ref_id": 3})
        assert label == "case:(2017) 10 SCC 1"

    def test_completely_empty_dict_returns_unknown(self):
        label = _build_source({})
        assert "unknown" in label


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — Score clamping
# ─────────────────────────────────────────────────────────────────────────────

class TestScoreClamping:
    def test_score_above_one_is_clamped(self):
        row = {**_STATUTE_ROW, "score": 1.05}
        result = kb_lookup(_claim(), retriever=_mock_retriever([row]))
        assert result.passages[0].score <= 1.0

    def test_negative_score_is_clamped_to_zero(self):
        row = {**_STATUTE_ROW, "score": -0.1}
        result = kb_lookup(_claim(), retriever=_mock_retriever([row]))
        assert result.passages[0].score >= 0.0

    def test_clamped_score_affects_hit(self):
        # If score clamps to 0.0 it must not trigger a hit
        row = {**_STATUTE_ROW, "score": -0.5}
        result = kb_lookup(_claim(), retriever=_mock_retriever([row]))
        assert result.hit is False


# ─────────────────────────────────────────────────────────────────────────────
# Test 6 — Custom threshold override
# ─────────────────────────────────────────────────────────────────────────────

class TestCustomThreshold:
    def test_very_high_threshold_makes_high_score_a_miss(self):
        # 0.87 score, threshold = 0.95 → miss
        result = kb_lookup(_claim(), threshold=0.95, retriever=_mock_retriever([_STATUTE_ROW]))
        assert result.hit is False

    def test_very_low_threshold_makes_low_score_a_hit(self):
        # 0.31 score, threshold = 0.20 → hit
        result = kb_lookup(_claim(), threshold=0.20, retriever=_mock_retriever([_LOW_SCORE_ROW]))
        assert result.hit is True

    def test_threshold_exactly_equal_to_score_is_a_hit(self):
        row = {**_STATUTE_ROW, "score": 0.55}
        result = kb_lookup(_claim(), threshold=0.55, retriever=_mock_retriever([row]))
        assert result.hit is True  # >= not >

    def test_module_constant_is_float(self):
        assert isinstance(KB_HIT_THRESHOLD, float)

    def test_module_constant_is_in_valid_range(self):
        assert 0.0 < KB_HIT_THRESHOLD < 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Test 7 — Logging
# ─────────────────────────────────────────────────────────────────────────────

class TestLogging:
    def test_logger_info_called_once_per_lookup(self, caplog):
        with caplog.at_level(logging.INFO, logger="stages.kb_lookup"):
            kb_lookup(_claim(), retriever=_mock_retriever([_STATUTE_ROW]))
        info_records = [r for r in caplog.records if r.levelname == "INFO"]
        assert len(info_records) == 1

    def test_log_contains_claim_id(self, caplog):
        with caplog.at_level(logging.INFO, logger="stages.kb_lookup"):
            kb_lookup(_claim(cid="claim_042"), retriever=_mock_retriever([_STATUTE_ROW]))
        assert "claim_042" in caplog.text

    def test_log_contains_hit_status(self, caplog):
        with caplog.at_level(logging.INFO, logger="stages.kb_lookup"):
            kb_lookup(_claim(), retriever=_mock_retriever([_STATUTE_ROW]))
        assert "hit=True" in caplog.text

    def test_log_contains_miss_status(self, caplog):
        with caplog.at_level(logging.INFO, logger="stages.kb_lookup"):
            kb_lookup(_claim(), retriever=_mock_retriever([_LOW_SCORE_ROW]))
        assert "hit=False" in caplog.text
