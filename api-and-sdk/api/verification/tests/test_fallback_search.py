"""
Unit tests for api/verification/fallback_search.py
===================================================

All tests mock the provider HTTP calls. No real network requests are made.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_HERE = Path(__file__).resolve().parent
_API_AND_SDK = _HERE.parent.parent
_PROJECT_ROOT = _API_AND_SDK.parent

for _p in (_PROJECT_ROOT, _API_AND_SDK):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from shared.schemas import Claim, ClaimType
from api.verification.fallback_search import (
    FallbackPassage,
    FallbackResult,
    fallback_search,
)


@pytest.fixture
def claim():
    return Claim(
        id="test_001",
        text="A test claim about something.",
        type=ClaimType.OTHER,
        span=(0, 20),
    )


@pytest.fixture
def claim_with_cit():
    return Claim(
        id="test_002",
        text="A test claim about something.",
        citation="2017 10 SCC 1",
        type=ClaimType.OTHER,
        span=(0, 20),
    )


def test_all_providers_fail_returns_empty_result(claim):
    result = fallback_search(
        claim,
        _ik_provider=lambda q: [],
        _google_provider=lambda q: [],
    )
    assert not result.found
    assert result.passages == []


def test_first_provider_succeeds_short_circuits(claim):
    mock_ik = MagicMock(return_value=[
        FallbackPassage(text="IK text", source="IK", url="url", retrieved_via="indian_kanoon")
    ])
    mock_google = MagicMock(return_value=[])
    
    result = fallback_search(
        claim,
        _ik_provider=mock_ik,
        _google_provider=mock_google,
    )
    
    assert result.found
    assert len(result.passages) == 1
    assert result.passages[0].retrieved_via == "indian_kanoon"
    mock_ik.assert_called_once()
    mock_google.assert_not_called()


def test_first_provider_fails_second_succeeds(claim):
    def crashing_ik(q):
        raise ValueError("IK is down")
        
    mock_google = MagicMock(return_value=[
        FallbackPassage(text="Google text", source="Google CSE", url="url", retrieved_via="google_cse")
    ])
    
    result = fallback_search(
        claim,
        _ik_provider=crashing_ik,
        _google_provider=mock_google,
    )
    
    assert result.found
    assert len(result.passages) == 1
    assert result.passages[0].retrieved_via == "google_cse"
    mock_google.assert_called_once()


def test_lawcite_skipped_when_no_citation(claim):
    mock_lawcite = MagicMock(return_value=[
        FallbackPassage(text="LawCite text", source="LawCite", url="url", retrieved_via="lawcite")
    ])
    mock_ik = MagicMock(return_value=[
        FallbackPassage(text="IK text", source="IK", url="url", retrieved_via="indian_kanoon")
    ])
    mock_google = MagicMock(return_value=[])
    
    result = fallback_search(
        claim,
        _lawcite_provider=mock_lawcite,
        _ik_provider=mock_ik,
        _google_provider=mock_google,
    )
    
    # Needs to skip LawCite because there's no citation in `claim`
    assert result.found
    assert result.passages[0].retrieved_via == "indian_kanoon"
    mock_lawcite.assert_not_called()
    mock_ik.assert_called_once()


def test_lawcite_triggered_when_citation_exists(claim_with_cit):
    mock_lawcite = MagicMock(return_value=[
        FallbackPassage(text="LawCite text", source="LawCite", url="url", retrieved_via="lawcite")
    ])
    mock_ik = MagicMock(return_value=[])
    mock_google = MagicMock(return_value=[])
    
    result = fallback_search(
        claim_with_cit,
        _lawcite_provider=mock_lawcite,
        _ik_provider=mock_ik,
        _google_provider=mock_google,
    )
    
    # Must trigger LawCite because there is a citation in `claim_with_cit`
    assert result.found
    assert result.passages[0].retrieved_via == "lawcite"
    mock_lawcite.assert_called_once_with("2017 10 SCC 1")
    # Short circuits if lawcite finds something
    mock_ik.assert_not_called()
