"""
Unit tests for detection-engine/stages/verdict.py
==================================================

All LLM calls are mocked — no real API calls are made.

Covered scenarios
-----------------
1. All four verdict types (SUPPORTED, CONTRADICTED, PARTIALLY_SUPPORTED, UNVERIFIABLE)
   produce the correct VerdictLabel and populate all fields correctly.
2. Malformed JSON on attempt 1 → retry → successful parse on attempt 2.
3. Malformed JSON on BOTH attempts → fallback to UNVERIFIABLE, no exception raised.
4. Out-of-taxonomy verdict string → treated as invalid JSON → retry → fallback.
5. Temperature is set to JUDGE_TEMPERATURE (0.1) on every call.
6. Analytics logger.info is called once per verdict.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch, PropertyMock

import pytest

# ── path setup ────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_DETECTION_ENGINE = _HERE.parent
_PROJECT_ROOT = _DETECTION_ENGINE.parent

for _p in (_PROJECT_ROOT, _DETECTION_ENGINE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from shared.schemas import Claim, ClaimType, VerdictLabel
from stages.verdict import (
    JUDGE_TEMPERATURE,
    _fallback_verdict,
    _parse_verdict_json,
    get_verdict,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _claim(text: str = "Section 43A imposes strict liability.", cid: str = "claim_001") -> Claim:
    return Claim(id=cid, text=text, type=ClaimType.SECTION_REF, span=(0, len(text)))


def _claim_with_citation() -> Claim:
    return Claim(
        id="claim_cit",
        text="Section 43A imposes strict liability.",
        citation="Section 43A, Information Technology Act 2000",
        type=ClaimType.SECTION_REF,
        span=(0, 40),
    )


def _llm_json(
    verdict: str = "SUPPORTED",
    reasoning: str = "The excerpt directly states strict liability.",
    evidence_span: str = "Section 43A imposes strict liability.",
    unsupported_detail: str = "",
    temporal_flag: bool = False,
    temporal_note: str = "",
    confidence: float = 0.92,
) -> str:
    return json.dumps({
        "reasoning": reasoning,
        "verdict": verdict,
        "evidence_span": evidence_span,
        "unsupported_detail": unsupported_detail,
        "temporal_flag": temporal_flag,
        "temporal_note": temporal_note,
        "confidence": confidence,
    })


def _mock_client(response_content: str) -> MagicMock:
    """Return a mock OpenAI client whose first completion returns response_content."""
    choice = MagicMock()
    choice.message.content = response_content
    completion = MagicMock()
    completion.choices = [choice]
    client = MagicMock()
    client.chat.completions.create.return_value = completion
    return client


def _mock_client_sequence(*responses: str) -> MagicMock:
    """Return a mock client that returns each response in sequence."""
    choices = []
    for r in responses:
        choice = MagicMock()
        choice.message.content = r
        completion = MagicMock()
        completion.choices = [choice]
        choices.append(completion)
    client = MagicMock()
    client.chat.completions.create.side_effect = choices
    return client


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — All four verdict types
# ─────────────────────────────────────────────────────────────────────────────
class TestAllVerdictTypes:
    @pytest.mark.parametrize("verdict_str,expected_label", [
        ("SUPPORTED", VerdictLabel.SUPPORTED),
        ("CONTRADICTED", VerdictLabel.CONTRADICTED),
        ("PARTIALLY_SUPPORTED", VerdictLabel.PARTIALLY_SUPPORTED),
        ("UNVERIFIABLE", VerdictLabel.UNVERIFIABLE),
    ])
    def test_verdict_label_mapping(self, verdict_str, expected_label):
        client = _mock_client(_llm_json(verdict=verdict_str))
        result = get_verdict(_claim(), "Some excerpt", "statute:43A", "http://example.com",
                             client=client)
        assert result.label == expected_label

    def test_supported_populates_evidence(self):
        span = "Section 43A imposes strict liability on body corporates."
        client = _mock_client(_llm_json(verdict="SUPPORTED", evidence_span=span))
        result = get_verdict(_claim(), "Some excerpt", "statute:43A", "http://example.com",
                             client=client)
        assert span in result.evidence

    def test_claim_id_is_set(self):
        client = _mock_client(_llm_json())
        result = get_verdict(_claim(cid="claim_007"), "excerpt", "src", "url", client=client)
        assert result.claim_id == "claim_007"

    def test_confidence_is_set(self):
        client = _mock_client(_llm_json(confidence=0.88))
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.confidence == pytest.approx(0.88, abs=1e-6)

    def test_reasoning_is_set(self):
        client = _mock_client(_llm_json(reasoning="This is the reasoning."))
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.reasoning == "This is the reasoning."

    def test_stage_reached_is_2(self):
        client = _mock_client(_llm_json())
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.stage_reached == 2

    def test_temporal_flag_true(self):
        client = _mock_client(_llm_json(temporal_flag=True, temporal_note="Amended in 2023"))
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.temporal_flag is True
        assert result.temporal_note == "Amended in 2023"

    def test_temporal_flag_false_by_default(self):
        client = _mock_client(_llm_json(temporal_flag=False))
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.temporal_flag is False

    def test_partially_supported_sets_unsupported_detail(self):
        client = _mock_client(_llm_json(
            verdict="PARTIALLY_SUPPORTED",
            unsupported_detail="The penalty amount is not mentioned in the excerpt.",
        ))
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.label == VerdictLabel.PARTIALLY_SUPPORTED
        assert "penalty amount" in (result.unsupported_detail or "")

    def test_empty_evidence_span_gives_empty_evidence_list(self):
        client = _mock_client(_llm_json(verdict="UNVERIFIABLE", evidence_span=""))
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.evidence == []


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — Malformed JSON: fail once then succeed
# ─────────────────────────────────────────────────────────────────────────────
class TestRetryOnMalformedJson:
    def test_retry_succeeds_on_second_attempt(self):
        client = _mock_client_sequence("NOT JSON AT ALL", _llm_json(verdict="SUPPORTED"))
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.label == VerdictLabel.SUPPORTED
        assert client.chat.completions.create.call_count == 2

    def test_first_attempt_malformed_logs_warning(self, caplog):
        client = _mock_client_sequence("NOT JSON AT ALL", _llm_json(verdict="SUPPORTED"))
        with caplog.at_level(logging.WARNING, logger="stages.verdict"):
            get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert any("attempt 1" in r.message for r in caplog.records)


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — Both attempts fail → UNVERIFIABLE fallback, no exception
# ─────────────────────────────────────────────────────────────────────────────
class TestBothAttemptsFail:
    def test_returns_unverifiable_on_double_failure(self):
        client = _mock_client_sequence("NOT JSON", "ALSO NOT JSON")
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.label == VerdictLabel.UNVERIFIABLE

    def test_no_exception_raised_on_double_failure(self):
        client = _mock_client_sequence("bad", "also bad")
        try:
            get_verdict(_claim(), "excerpt", "src", "url", client=client)
        except Exception as exc:
            pytest.fail(f"get_verdict raised {exc!r} — it must never propagate exceptions")

    def test_fallback_has_reasoning_note(self):
        client = _mock_client_sequence("bad", "also bad")
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.reasoning is not None
        assert "unparseable" in result.reasoning.lower()

    def test_fallback_evidence_list_is_empty(self):
        client = _mock_client_sequence("bad", "also bad")
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.evidence == []

    def test_fallback_stage_reached_is_2(self):
        client = _mock_client_sequence("bad", "also bad")
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.stage_reached == 2

    def test_call_count_is_2_on_double_failure(self):
        client = _mock_client_sequence("bad", "also bad")
        get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert client.chat.completions.create.call_count == 2


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — Out-of-taxonomy verdict string
# ─────────────────────────────────────────────────────────────────────────────
class TestOutOfTaxonomyVerdict:
    def test_invalid_verdict_string_triggers_retry(self):
        bad = json.dumps({"verdict": "MAYBE", "reasoning": "r", "evidence_span": "",
                          "unsupported_detail": "", "temporal_flag": False,
                          "temporal_note": "", "confidence": 0.5})
        client = _mock_client_sequence(bad, _llm_json(verdict="UNVERIFIABLE"))
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        # Second attempt succeeds with a valid verdict
        assert result.label == VerdictLabel.UNVERIFIABLE
        assert client.chat.completions.create.call_count == 2

    def test_invalid_verdict_on_both_attempts_falls_back(self):
        bad = json.dumps({"verdict": "MAYBE", "reasoning": "r", "evidence_span": "",
                          "unsupported_detail": "", "temporal_flag": False,
                          "temporal_note": "", "confidence": 0.5})
        client = _mock_client_sequence(bad, bad)
        result = get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert result.label == VerdictLabel.UNVERIFIABLE


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — Temperature is set correctly
# ─────────────────────────────────────────────────────────────────────────────
class TestTemperature:
    def test_temperature_constant_is_valid(self):
        assert 0.0 <= JUDGE_TEMPERATURE <= 0.2  # low for deterministic legal judgements

    def test_temperature_passed_to_llm_call(self):
        client = _mock_client(_llm_json())
        get_verdict(_claim(), "excerpt", "src", "url", client=client)
        call_kwargs = client.chat.completions.create.call_args
        assert call_kwargs.kwargs.get("temperature") == JUDGE_TEMPERATURE

    def test_temperature_is_exactly_1_0(self):
        """Confirm the value is 0.1 for deterministic legal judgements."""
        assert JUDGE_TEMPERATURE == 0.1


# ─────────────────────────────────────────────────────────────────────────────
# Test 6 — Analytics logging
# ─────────────────────────────────────────────────────────────────────────────
class TestLogging:
    def test_logger_info_called_once_on_success(self, caplog):
        client = _mock_client(_llm_json())
        with caplog.at_level(logging.INFO, logger="stages.verdict"):
            get_verdict(_claim(cid="claim_log"), "excerpt", "statute:43A", "url",
                        client=client)
        info_records = [r for r in caplog.records if r.levelname == "INFO"]
        assert len(info_records) == 1

    def test_log_contains_claim_id(self, caplog):
        client = _mock_client(_llm_json())
        with caplog.at_level(logging.INFO, logger="stages.verdict"):
            get_verdict(_claim(cid="claim_XYZ"), "excerpt", "src", "url", client=client)
        assert "claim_XYZ" in caplog.text

    def test_log_contains_label(self, caplog):
        client = _mock_client(_llm_json(verdict="CONTRADICTED"))
        with caplog.at_level(logging.INFO, logger="stages.verdict"):
            get_verdict(_claim(), "excerpt", "src", "url", client=client)
        assert "CONTRADICTED" in caplog.text

    def test_log_contains_source_name(self, caplog):
        client = _mock_client(_llm_json())
        with caplog.at_level(logging.INFO, logger="stages.verdict"):
            get_verdict(_claim(), "excerpt", "statute:43A", "url", client=client)
        assert "statute:43A" in caplog.text

    def test_fallback_also_logs_info(self, caplog):
        client = _mock_client_sequence("bad", "also bad")
        with caplog.at_level(logging.INFO, logger="stages.verdict"):
            get_verdict(_claim(cid="claim_fallback"), "excerpt", "src", "url", client=client)
        info_records = [r for r in caplog.records if r.levelname == "INFO"]
        assert len(info_records) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Test 7 — _parse_verdict_json unit tests
# ─────────────────────────────────────────────────────────────────────────────
class TestParseVerdictJson:
    def test_valid_json_object_parsed(self):
        raw = _llm_json(verdict="SUPPORTED")
        result = _parse_verdict_json(raw)
        assert result["verdict"] == "SUPPORTED"

    def test_strips_markdown_fences(self):
        raw = "```json\n" + _llm_json() + "\n```"
        result = _parse_verdict_json(raw)
        assert "verdict" in result

    def test_raises_on_non_dict_json(self):
        with pytest.raises(ValueError, match="expected an object"):
            _parse_verdict_json("[1, 2, 3]")

    def test_raises_on_invalid_verdict(self):
        raw = json.dumps({"verdict": "MAYBE", "reasoning": "", "evidence_span": "",
                          "unsupported_detail": "", "temporal_flag": False,
                          "temporal_note": "", "confidence": 0.5})
        with pytest.raises(ValueError, match="out-of-taxonomy"):
            _parse_verdict_json(raw)

    def test_raises_on_malformed_json(self):
        import json as _json
        with pytest.raises(_json.JSONDecodeError):
            _parse_verdict_json("{ this is not json }")
