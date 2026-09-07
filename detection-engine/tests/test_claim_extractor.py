"""
Unit tests for detection-engine/stages/claim_extractor.py
==========================================================

All tests mock the OpenAI client — no real API calls are made.

Covered scenarios
-----------------
1. Multi-claim paragraph  → multiple Claims with correct types / citations.
2. Single claim with a clear statute citation → claim.citation populated.
3. Single claim with no citation         → claim.citation is None.
4. Malformed LLM output (both attempts)  → ClaimExtractionError raised.
5. First attempt bad, second good        → retry succeeds silently.
6. Empty input string                    → returns [] without calling LLM.
7. Unknown claim type                    → falls back to ClaimType.OTHER.
8. EXTRACTION_PROMPT sanity              → {llm_output} placeholder present.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# ── resolve imports ──────────────────────────────────────────────────────────
# Add project root (three levels up from tests/) so `shared` is importable,
# and add detection-engine/ so `stages` is importable as a plain package.
_HERE = Path(__file__).resolve().parent
_DETECTION_ENGINE = _HERE.parent
_PROJECT_ROOT = _DETECTION_ENGINE.parent

for _p in (_PROJECT_ROOT, _DETECTION_ENGINE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from stages.claim_extractor import (          # noqa: E402
    EXTRACTION_PROMPT,
    ClaimExtractionError,
    extract_claims,
)
from shared.schemas import Claim, ClaimType   # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_response(content: str) -> MagicMock:
    """Build a minimal mock that looks like an openai ChatCompletion response."""
    choice = SimpleNamespace(message=SimpleNamespace(content=content))
    mock = MagicMock()
    mock.choices = [choice]
    return mock


def _client(content: str) -> MagicMock:
    """Return a mock OpenAI client that always returns *content*."""
    c = MagicMock()
    c.chat.completions.create.return_value = _make_response(content)
    return c


# ─────────────────────────────────────────────────────────────────────────────
# Fixture data
# ─────────────────────────────────────────────────────────────────────────────

_MULTI_CLAIM_JSON = json.dumps([
    {
        "text": "Section 43A of the IT Act imposes strict liability on body corporates.",
        "type": "SECTION_REF",
        "citation": "Section 43A, Information Technology Act 2000",
        "context": "Section 43A of the IT Act imposes strict liability on body corporates for data breaches.",
        "span_start": 0,
        "span_end": 70,
    },
    {
        "text": "Privacy is a fundamental right under the Indian Constitution.",
        "type": "HOLDING",
        "citation": "K.S. Puttaswamy v. Union of India (2017) 10 SCC 1",
        "context": "Privacy is a fundamental right under the Indian Constitution per the Puttaswamy ruling.",
        "span_start": 71,
        "span_end": 130,
    },
    {
        "text": "Data breach victims are not required to prove willful negligence.",
        "type": "PROCEDURAL",
        "citation": None,
        "context": "Under Section 43A, data breach victims are not required to prove willful negligence.",
        "span_start": 131,
        "span_end": 195,
    },
])

_SINGLE_CITATION_JSON = json.dumps([
    {
        "text": "Section 66A of the IT Act criminalises offensive online speech.",
        "type": "SECTION_REF",
        "citation": "Section 66A, Information Technology Act 2000",
        "context": "Section 66A of the IT Act criminalises offensive online speech.",
        "span_start": 0,
        "span_end": 62,
    }
])

_NO_CITATION_JSON = json.dumps([
    {
        "text": "An intermediary that fails to act on a takedown notice loses its safe harbour.",
        "type": "HOLDING",
        "citation": None,
        "context": "An intermediary that fails to act on a takedown notice loses its safe harbour under Indian law.",
        "span_start": 0,
        "span_end": 75,
    }
])

_UNKNOWN_TYPE_JSON = json.dumps([
    {
        "text": "Some legal assertion.",
        "type": "COMPLETELY_UNKNOWN_TYPE",
        "citation": None,
        "context": "Some legal assertion.",
        "span_start": 0,
        "span_end": 21,
    }
])


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — Multi-claim paragraph
# ─────────────────────────────────────────────────────────────────────────────

class TestMultiClaimParagraph:
    def test_returns_correct_number_of_claims(self):
        claims = extract_claims("multi-claim legal text", client=_client(_MULTI_CLAIM_JSON))
        assert len(claims) == 3

    def test_all_items_are_claim_instances(self):
        claims = extract_claims("multi-claim legal text", client=_client(_MULTI_CLAIM_JSON))
        assert all(isinstance(c, Claim) for c in claims)

    def test_claim_types_are_correct(self):
        claims = extract_claims("multi-claim legal text", client=_client(_MULTI_CLAIM_JSON))
        assert claims[0].type == ClaimType.SECTION_REF
        assert claims[1].type == ClaimType.HOLDING
        assert claims[2].type == ClaimType.PROCEDURAL

    def test_claim_ids_are_sequential(self):
        claims = extract_claims("multi-claim legal text", client=_client(_MULTI_CLAIM_JSON))
        assert claims[0].id == "claim_001"
        assert claims[1].id == "claim_002"
        assert claims[2].id == "claim_003"

    def test_citations_are_populated(self):
        claims = extract_claims("multi-claim legal text", client=_client(_MULTI_CLAIM_JSON))
        assert claims[0].citation == "Section 43A, Information Technology Act 2000"
        assert "Puttaswamy" in claims[1].citation
        assert claims[2].citation is None  # third claim has no citation

    def test_context_fields_are_populated(self):
        claims = extract_claims("multi-claim legal text", client=_client(_MULTI_CLAIM_JSON))
        assert "strict liability" in claims[0].context
        assert "Puttaswamy" in claims[1].context
        assert "willful negligence" in claims[2].context

    def test_spans_stored_correctly(self):
        claims = extract_claims("multi-claim legal text", client=_client(_MULTI_CLAIM_JSON))
        assert claims[0].span == (0, 70)
        assert claims[1].span == (71, 130)
        assert claims[2].span == (131, 195)

    def test_claim_text_content(self):
        claims = extract_claims("multi-claim legal text", client=_client(_MULTI_CLAIM_JSON))
        assert "strict liability" in claims[0].text
        assert "fundamental right" in claims[1].text
        assert "willful negligence" in claims[2].text


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — Single claim with a clear statute citation
# ─────────────────────────────────────────────────────────────────────────────

class TestSingleClaimWithCitation:
    def test_returns_one_claim(self):
        claims = extract_claims("Section 66A legal text", client=_client(_SINGLE_CITATION_JSON))
        assert len(claims) == 1

    def test_claim_type_is_section_ref(self):
        claims = extract_claims("Section 66A legal text", client=_client(_SINGLE_CITATION_JSON))
        assert claims[0].type == ClaimType.SECTION_REF

    def test_citation_is_populated(self):
        claims = extract_claims("Section 66A legal text", client=_client(_SINGLE_CITATION_JSON))
        assert claims[0].citation == "Section 66A, Information Technology Act 2000"

    def test_claim_text_contains_section(self):
        claims = extract_claims("Section 66A legal text", client=_client(_SINGLE_CITATION_JSON))
        assert "66A" in claims[0].text


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — Claim with no citation
# ─────────────────────────────────────────────────────────────────────────────

class TestClaimWithNoCitation:
    def test_citation_is_none(self):
        claims = extract_claims("intermediary text", client=_client(_NO_CITATION_JSON))
        assert claims[0].citation is None

    def test_claim_type_is_holding(self):
        claims = extract_claims("intermediary text", client=_client(_NO_CITATION_JSON))
        assert claims[0].type == ClaimType.HOLDING

    def test_claim_text_is_correct(self):
        claims = extract_claims("intermediary text", client=_client(_NO_CITATION_JSON))
        assert "safe harbour" in claims[0].text

    def test_context_is_preserved(self):
        claims = extract_claims("intermediary text", client=_client(_NO_CITATION_JSON))
        assert "Indian law" in claims[0].context


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — Malformed LLM output triggers retry → ClaimExtractionError
# ─────────────────────────────────────────────────────────────────────────────

class TestMalformedLLMOutput:
    def test_raises_claim_extraction_error(self):
        bad_client = MagicMock()
        bad_client.chat.completions.create.return_value = _make_response(
            "The model went rogue and returned prose instead of JSON."
        )
        with pytest.raises(ClaimExtractionError):
            extract_claims("some legal text", client=bad_client)

    def test_llm_called_exactly_twice(self):
        bad_client = MagicMock()
        bad_client.chat.completions.create.return_value = _make_response("not json!!")
        with pytest.raises(ClaimExtractionError):
            extract_claims("some legal text", client=bad_client)
        assert bad_client.chat.completions.create.call_count == 2

    def test_exception_carries_raw_response(self):
        raw = "This is definitely not JSON at all."
        bad_client = MagicMock()
        bad_client.chat.completions.create.return_value = _make_response(raw)
        with pytest.raises(ClaimExtractionError) as exc_info:
            extract_claims("some legal text", client=bad_client)
        assert exc_info.value.raw_response == raw

    def test_json_object_instead_of_array_raises(self):
        """LLM returns a JSON object {} instead of array [] — must also fail."""
        bad_client = _client(json.dumps({"text": "oops", "type": "HOLDING"}))
        with pytest.raises(ClaimExtractionError):
            extract_claims("some legal text", client=bad_client)


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — Retry succeeds on second attempt
# ─────────────────────────────────────────────────────────────────────────────

class TestRetryPath:
    def test_retry_succeeds_silently(self):
        retry_client = MagicMock()
        retry_client.chat.completions.create.side_effect = [
            _make_response("not json at all on the first try"),
            _make_response(_SINGLE_CITATION_JSON),
        ]
        claims = extract_claims("Section 66A legal text", client=retry_client)
        assert len(claims) == 1
        assert retry_client.chat.completions.create.call_count == 2

    def test_retry_claim_data_is_correct(self):
        retry_client = MagicMock()
        retry_client.chat.completions.create.side_effect = [
            _make_response("garbage"),
            _make_response(_SINGLE_CITATION_JSON),
        ]
        claims = extract_claims("Section 66A legal text", client=retry_client)
        assert claims[0].citation == "Section 66A, Information Technology Act 2000"


# ─────────────────────────────────────────────────────────────────────────────
# Test 6 — Empty input
# ─────────────────────────────────────────────────────────────────────────────

class TestEmptyInput:
    def test_empty_string_returns_empty_list(self):
        c = MagicMock()
        assert extract_claims("", client=c) == []
        c.chat.completions.create.assert_not_called()

    def test_whitespace_only_returns_empty_list(self):
        c = MagicMock()
        assert extract_claims("   \n\t  ", client=c) == []
        c.chat.completions.create.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Test 7 — Unknown claim type falls back to OTHER
# ─────────────────────────────────────────────────────────────────────────────

class TestUnknownClaimType:
    def test_unknown_type_defaults_to_other(self):
        claims = extract_claims("some legal text", client=_client(_UNKNOWN_TYPE_JSON))
        assert len(claims) == 1
        assert claims[0].type == ClaimType.OTHER


# ─────────────────────────────────────────────────────────────────────────────
# Test 8 — EXTRACTION_PROMPT sanity check
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractionPromptConstant:
    def test_prompt_has_llm_output_placeholder(self):
        assert "{llm_output}" in EXTRACTION_PROMPT

    def test_prompt_lists_all_claim_types(self):
        for t in ("CASE_CITATION", "SECTION_REF", "HOLDING", "PROCEDURAL", "OTHER"):
            assert t in EXTRACTION_PROMPT

    def test_prompt_mentions_citation_field(self):
        assert "citation" in EXTRACTION_PROMPT

    def test_prompt_mentions_context_field(self):
        assert "context" in EXTRACTION_PROMPT
