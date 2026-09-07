"""
api/verification/fallback_search.py
====================================
External fallback search for Indian legal claims when the local FAISS KB misses.

Providers implemented:
    1. LawCite (citation only) — triggers ONLY if claim.citation is present.
    2. Indian Kanoon (api.indiankanoon.org) — optional, token-gated API.
    3. Google Custom Search JSON API — general fallback scoped to liiofindia.org
       and indiankanoon.org.

Public API
----------
    fallback_search(claim: Claim, jurisdiction: str = "IN") -> FallbackResult

Design notes
------------
* Each provider is isolated and handles its own timeouts/errors.
* LawCite is explicitly restricted to citation lookups. It is never used as a
  general text search engine.
* Logging matches the pattern used throughout the codebase.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel, ConfigDict, Field

# ── project root → shared/ importable ───────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from shared.schemas import Claim  # noqa: E402

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
PROVIDER_TIMEOUT: float = 5.0
PROVIDER_MIN_CALL_INTERVAL: float = 1.0
MAX_PASSAGES_PER_PROVIDER: int = 5

_LAWCITE_URL = "http://www.liiofindia.org/cgi-bin/LawCite"
_IK_SEARCH_URL = "https://api.indiankanoon.org/search/"
_GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"


# ─────────────────────────────────────────────────────────────────────────────
# Result models
# ─────────────────────────────────────────────────────────────────────────────
class FallbackPassage(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str = Field(..., description="Extracted text of the legal passage or snippet.")
    source: str = Field(..., description="Source label, e.g. 'LawCite', 'Indian Kanoon'.")
    url: str = Field(..., description="Direct URL to the source document or result page.")
    retrieved_via: str = Field(
        ...,
        description="Provider identifier. One of: 'lawcite', 'indian_kanoon', 'google_cse'.",
    )


class FallbackResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    found: bool = Field(..., description="True if at least one provider returned usable passages.")
    passages: list[FallbackPassage] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Rate-limiting helper
# ─────────────────────────────────────────────────────────────────────────────
_last_call_times: dict[str, float] = {}

def _enforce_rate_limit(provider: str) -> None:
    last = _last_call_times.get(provider, 0.0)
    elapsed = time.monotonic() - last
    if elapsed < PROVIDER_MIN_CALL_INTERVAL:
        time.sleep(PROVIDER_MIN_CALL_INTERVAL - elapsed)
    _last_call_times[provider] = time.monotonic()


# ─────────────────────────────────────────────────────────────────────────────
# Provider 1: LawCite (Citations Only)
# ─────────────────────────────────────────────────────────────────────────────
def _search_lawcite(citation: str) -> list[FallbackPassage]:
    """
    Search LawCite by citation string.
    Only queries the 'cit' GET parameter on the LawCite CGI script.
    """
    _enforce_rate_limit("lawcite")
    try:
        resp = requests.get(
            _LAWCITE_URL,
            params={"cit": citation},
            headers={"User-Agent": "LexGuard-HallucinationChecker/1.0"},
            timeout=PROVIDER_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("lawcite: request failed — %s", exc)
        return []

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("lawcite: beautifulsoup4 not installed — skipped")
        return []

    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        # LawCite usually returns a table of cases citing the requested citation
        # or the citing document directly. We'll greedily grab table rows or links.
        passages: list[FallbackPassage] = []
        
        # very generic scrape for LawCite rows
        for tr in soup.find_all("tr")[:MAX_PASSAGES_PER_PROVIDER]:
            a_tag = tr.find("a", href=True)
            if not a_tag:
                continue
            
            title = a_tag.get_text(strip=True)
            if not title:
                continue
                
            href = a_tag["href"]
            if href.startswith("/"):
                href = "http://www.liiofindia.org" + href
                
            # Grab all text in the row as the snippet
            snippet = tr.get_text(separator=" ", strip=True)
            
            passages.append(
                FallbackPassage(
                    text=snippet or title,
                    source="LawCite Result",
                    url=href,
                    retrieved_via="lawcite",
                )
            )

        if not passages:
            logger.debug("lawcite: no results parsed for citation %r", citation)
        return passages

    except Exception as exc:
        logger.warning("lawcite: HTML parsing error — %s", exc)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Provider 2: Indian Kanoon
# ─────────────────────────────────────────────────────────────────────────────
def _search_indian_kanoon(query: str) -> list[FallbackPassage]:
    api_key = os.environ.get("INDIAN_KANOON_API_KEY")
    if not api_key:
        logger.debug("indian_kanoon: INDIAN_KANOON_API_KEY not set")
        return []

    _enforce_rate_limit("indian_kanoon")
    try:
        resp = requests.post(
            _IK_SEARCH_URL,
            params={"formInput": query, "pagenum": 0},
            headers={"Authorization": f"Token {api_key}", "Accept": "application/json"},
            timeout=PROVIDER_TIMEOUT,
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
    except Exception as exc:
        logger.warning("indian_kanoon: request/decode failed — %s", exc)
        return []

    docs = data.get("docs", [])
    passages: list[FallbackPassage] = []
    for doc in docs[:MAX_PASSAGES_PER_PROVIDER]:
        tid = doc.get("tid", "")
        title = doc.get("title", "Indian Kanoon document")
        headline = doc.get("headline", title)
        try:
            from bs4 import BeautifulSoup as _BS
            headline = _BS(headline, "html.parser").get_text(strip=True)
        except ImportError:
            import re
            headline = re.sub(r"<[^>]+>", "", headline)

        passages.append(
            FallbackPassage(
                text=headline or title,
                source=f"Indian Kanoon — {doc.get('docsource', 'Unknown Court')}",
                url=f"https://indiankanoon.org/doc/{tid}/",
                retrieved_via="indian_kanoon",
            )
        )
    return passages


# ─────────────────────────────────────────────────────────────────────────────
# Provider 3: Google Custom Search API
# ─────────────────────────────────────────────────────────────────────────────
def _search_google_cse(query: str, jurisdiction: str) -> list[FallbackPassage]:
    api_key = os.environ.get("GOOGLE_CSE_API_KEY")
    cse_id = os.environ.get("GOOGLE_CSE_ID")
    if not api_key or not cse_id:
        logger.debug("google_cse: unused/no credentials")
        return []

    _enforce_rate_limit("google_cse")
    # Scope query explicitly to the Indian legal sites as requested
    scoped_query = f"{query} (site:liiofindia.org OR site:indiankanoon.org)"

    try:
        resp = requests.get(
            _GOOGLE_CSE_URL,
            params={
                "key": api_key, "cx": cse_id, "q": scoped_query,
                "num": MAX_PASSAGES_PER_PROVIDER, "gl": jurisdiction,
            },
            timeout=PROVIDER_TIMEOUT,
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
    except Exception as exc:
        logger.warning("google_cse: request/decode failed — %s", exc)
        return []

    items = data.get("items", [])
    passages: list[FallbackPassage] = []
    for item in items[:MAX_PASSAGES_PER_PROVIDER]:
        passages.append(
            FallbackPassage(
                text=item.get("snippet", item.get("title", "Google CSE result")),
                source=f"Google CSE — {item.get('displayLink', item.get('link', ''))}",
                url=item.get("link", _GOOGLE_CSE_URL),
                retrieved_via="google_cse",
            )
        )
    return passages


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def fallback_search(
    claim: Claim,
    jurisdiction: str = "IN",
    *,
    _lawcite_provider=None,
    _ik_provider=None,
    _google_provider=None,
) -> FallbackResult:
    """Search external sources for evidence grounding *claim*."""
    
    # 1. Condition: lawcite is ONLY used if there is a citation
    if claim.citation:
        lawcite_fn = _lawcite_provider or _search_lawcite
        try:
            passages = lawcite_fn(claim.citation)
            if passages:
                logger.info(
                    "fallback_search | claim_id=%s | provider=lawcite | passages=%d | citation=%r",
                    claim.id, len(passages), claim.citation
                )
                return FallbackResult(found=True, passages=passages)
        except Exception as exc:
            logger.error("fallback_search: lawcite error — %s", exc)

    # General query for the text engines
    query_parts = [claim.text]
    if claim.citation:
        query_parts.append(claim.citation)
    query = " ".join(query_parts)

    ik_fn = _ik_provider or _search_indian_kanoon
    google_fn = _google_provider or (lambda q: _search_google_cse(q, jurisdiction))

    for name, fn in [("indian_kanoon", ik_fn), ("google_cse", google_fn)]:
        try:
            passages = fn(query)
            if passages:
                logger.info(
                    "fallback_search | claim_id=%s | provider=%s | passages=%d | query=%.80r",
                    claim.id, name, len(passages), query
                )
                return FallbackResult(found=True, passages=passages)
        except Exception as exc:
            logger.error("fallback_search: %s error — %s", name, exc)

    logger.info("fallback_search | claim_id=%s | all providers failed | found=False", claim.id)
    return FallbackResult(found=False, passages=[])
