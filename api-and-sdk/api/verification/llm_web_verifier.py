"""
api/verification/llm_web_verifier.py
=====================================
LLM-powered autonomous web search verifier for legal claims.

When the local KB (FAISS/Postgres) cannot find *relevant* legal text for a
claim — either because kb_lookup returned hit=False, or because the retrieved
passage is off-topic for the specific claim — this module asks the LLM to
search the web **independently** and determine whether the claim is accurate.

Mechanism
---------
Uses the OpenAI **Responses API** with the ``web_search_preview`` built-in
tool (requires openai SDK >= 1.66.0 and models: gpt-4o, gpt-4o-mini, o1, o3).
The LLM autonomously decides what to search, fetches live results, reasons
over them, and returns a structured JSON verdict.

No pre-defined scraping providers (Indian Kanoon, LawCite, Google CSE) are
used here. The LLM handles discovery entirely.

Public API
----------
    llm_web_search_verify(claim, *, client=None, model=None) -> Verdict

Verdict labels returned
-----------------------
    SUPPORTED          – web evidence confirms the claim
    CONTRADICTED       – web evidence contradicts the claim
    PARTIALLY_SUPPORTED – web evidence partially matches the claim
    UNVERIFIABLE       – LLM could not find authoritative sources

Error handling
--------------
Never propagates as an unhandled exception. On any failure (SDK version too
old, API error, parse error) falls back to UNVERIFIABLE with an explanatory
reasoning note.

Logging
-------
    logger = logging.getLogger(__name__)
Every call logs claim_id, final label, and source_found at INFO level.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

# ── resolve project root so shared/ is importable regardless of cwd ──────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from shared.schemas import Claim, Verdict, VerdictLabel  # noqa: E402

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

#: Model used for autonomous web search. Must support the web_search_preview tool.
#: Supported: gpt-4o, gpt-4o-mini, o1, o3 (not gpt-3.5-turbo).
WEB_SEARCH_MODEL_DEFAULT: str = "gpt-4o-mini"

#: Valid verdict strings the LLM may return
VALID_VERDICT_STRINGS: frozenset[str] = frozenset(
    {"SUPPORTED", "CONTRADICTED", "PARTIALLY_SUPPORTED", "UNVERIFIABLE"}
)

_VERDICT_MAP: dict[str, VerdictLabel] = {
    "SUPPORTED": VerdictLabel.SUPPORTED,
    "CONTRADICTED": VerdictLabel.CONTRADICTED,
    "PARTIALLY_SUPPORTED": VerdictLabel.PARTIALLY_SUPPORTED,
    "UNVERIFIABLE": VerdictLabel.UNVERIFIABLE,
}

# ─────────────────────────────────────────────────────────────────────────────
# Prompt template
# ─────────────────────────────────────────────────────────────────────────────
_WEB_SEARCH_SYSTEM_PROMPT = """\
You are an expert Indian legal fact-checker. Your task is to verify whether a
legal claim extracted from an AI-generated answer is accurate.

You have access to a web search tool. Use it to find authoritative sources:
- Official Indian government sites (indiacode.nic.in, legislative.gov.in)
- Indian Kanoon (indiankanoon.org) — Supreme Court and High Court judgments
- Bare act text repositories

Instructions:
1. Search specifically for the statute section, case name, or legal concept in the claim.
2. Prefer primary sources (bare act text, official gazette, Supreme Court judgment) over 
   commentary or news articles.
3. Read the retrieved content carefully and compare it against the claim.
4. Base your verdict ONLY on what you find, not on your training data.

Verdict definitions:
- SUPPORTED: The claim matches what authoritative sources say.
- CONTRADICTED: The claim says something that contradicts what sources say.
- PARTIALLY_SUPPORTED: The claim is partially correct but contains inaccuracies or omissions.
- UNVERIFIABLE: You could not find authoritative sources to confirm or deny the claim.

After searching, respond with ONLY this JSON (no text before or after):
{
  "reasoning": "<2-4 sentences explaining your search and comparison>",
  "verdict": "SUPPORTED" | "CONTRADICTED" | "PARTIALLY_SUPPORTED" | "UNVERIFIABLE",
  "evidence_span": "<exact quote from the source you found, or empty string>",
  "unsupported_detail": "<what part of the claim is wrong or unverified, empty if SUPPORTED>",
  "source_found": "<URL or name of the primary source you used, or empty string>",
  "confidence": <float 0.0-1.0>
}"""

_WEB_SEARCH_USER_TEMPLATE = """\
Verify this legal claim from an AI-generated Indian legal answer:

CLAIM: {claim_text}

ASSERTED CITATION (if any): {claim_citation}
CLAIM TYPE: {claim_type}

Search the web for authoritative Indian legal sources and determine if this claim is accurate.
Return only the JSON verdict as specified."""


# ─────────────────────────────────────────────────────────────────────────────
# LLM client helper
# ─────────────────────────────────────────────────────────────────────────────
def _get_llm_client():  # -> OpenAI
    """Return an openai.OpenAI client configured for native OpenAI."""
    try:
        from openai import OpenAI
        import httpx
    except ImportError as exc:
        raise ImportError(
            "openai package required. Install: pip install openai"
        ) from exc

    # Use OPENAI_NATIVE_API_KEY explicitly or fallback to OPENAI_API_KEY
    api_key = os.environ.get("OPENAI_NATIVE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_NATIVE_API_KEY is not set. Add it to your .env file."
        )

    # Force base_url to None (ignore OPENAI_BASE_URL which points to Groq)
    base_url = None

    http_client = httpx.Client(
        verify=False,   # Disable SSL verification (matches existing pattern in codebase)
        timeout=90.0    # Longer timeout for web search
    )

    return OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)


def _resolve_model() -> str:
    """Return the model to use for web search verification."""
    # Since JUDGE_MODEL in .env is typically used for the Groq fallback 
    # (e.g. openai/gpt-oss-120b), we default strictly to WEB_SEARCH_MODEL_DEFAULT
    # which is gpt-4o-mini for best accuracy vs free tier usage.
    model = os.environ.get("WEB_VERIFIER_MODEL", WEB_SEARCH_MODEL_DEFAULT)
    
    supported_prefixes = ("gpt-4", "o1", "o3")
    if not any(model.startswith(pfx) for pfx in supported_prefixes):
        logger.warning(
            "llm_web_verifier: model %r may not support web_search_preview. "
            "Falling back to %r.", model, WEB_SEARCH_MODEL_DEFAULT
        )
        model = WEB_SEARCH_MODEL_DEFAULT
    return model


# ─────────────────────────────────────────────────────────────────────────────
# JSON parsing
# ─────────────────────────────────────────────────────────────────────────────
def _parse_verdict_json(raw: str) -> dict[str, Any]:
    """Parse and validate the LLM JSON response from web search.

    Strips markdown fences if present.

    Raises:
        json.JSONDecodeError: If not valid JSON.
        ValueError: If verdict is out of taxonomy.
    """
    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)

    # Handle case where LLM wraps JSON in text before/after
    # Try to extract the JSON object
    json_match = re.search(r'\{.*\}', stripped, flags=re.DOTALL)
    if json_match:
        stripped = json_match.group(0)

    parsed = json.loads(stripped)

    if not isinstance(parsed, dict):
        raise ValueError(
            f"LLM returned JSON {type(parsed).__name__} — expected an object."
        )

    verdict_str = str(parsed.get("verdict", "")).upper()
    if verdict_str not in VALID_VERDICT_STRINGS:
        raise ValueError(
            f"LLM returned out-of-taxonomy verdict {verdict_str!r}. "
            f"Valid: {sorted(VALID_VERDICT_STRINGS)}"
        )

    return parsed


# ─────────────────────────────────────────────────────────────────────────────
# Extract text from Responses API output
# ─────────────────────────────────────────────────────────────────────────────
def _extract_text_from_response(response: Any) -> str:
    """Extract the final text output from an OpenAI Responses API response.

    The Responses API returns an object with an ``output`` list. The last
    message-type item in that list contains the assistant's text response.
    """
    # response.output_text is available in newer SDK versions
    if hasattr(response, "output_text"):
        return response.output_text or ""

    # Fall back to iterating output items
    if hasattr(response, "output"):
        for item in reversed(response.output):
            # OutputMessage has type='message'
            if getattr(item, "type", None) == "message":
                for content_block in getattr(item, "content", []):
                    if getattr(content_block, "type", None) == "output_text":
                        return content_block.text or ""
                    # Some SDK versions return .text directly
                    if hasattr(content_block, "text"):
                        return content_block.text or ""

    # Last resort: string representation
    return str(response)


# ─────────────────────────────────────────────────────────────────────────────
# Fallback verdict
# ─────────────────────────────────────────────────────────────────────────────
def _fallback_unverifiable(claim: Claim, reason: str) -> Verdict:
    """Return UNVERIFIABLE when web search or parsing fails."""
    logger.info(
        "llm_web_verifier | claim_id=%s | label=UNVERIFIABLE (fallback) | reason=%s",
        claim.id, reason[:120]
    )
    return Verdict(
        claim_id=claim.id,
        label=VerdictLabel.UNVERIFIABLE,
        evidence=[],
        stage_reached=2,
        confidence=None,
        reasoning=f"Web search verification failed: {reason}",
        evidence_span=None,
        unsupported_detail=None,
        temporal_flag=False,
        temporal_note=None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def llm_web_search_verify(
    claim: Claim,
    *,
    client: Any = None,
    model: Optional[str] = None,
) -> Verdict:
    """Verify *claim* by having the LLM autonomously search the web.

    Called when ``kb_lookup`` returns no relevant legal text for the claim.
    The LLM uses the ``web_search_preview`` built-in tool to find authoritative
    Indian legal sources and reason about whether the claim is accurate.

    Args:
        claim:  The atomic Claim to verify (from shared/schemas.py).
        client: Pre-built OpenAI client. If None, constructed from env vars.
                Inject a mock in tests.
        model:  Model name override. Must support web_search_preview.
                Falls back to JUDGE_MODEL env var, then to 'gpt-4o-mini'.

    Returns:
        Verdict with label SUPPORTED, CONTRADICTED, PARTIALLY_SUPPORTED, or
        UNVERIFIABLE. Never raises — returns UNVERIFIABLE on any failure.

    Raises:
        Never. All exceptions are caught and converted to UNVERIFIABLE.
    """
    _client = client if client is not None else _get_llm_client()
    _model = model or _resolve_model()

    user_content = _WEB_SEARCH_USER_TEMPLATE.format(
        claim_text=claim.text,
        claim_citation=claim.citation or "(none)",
        claim_type=claim.type.value if hasattr(claim.type, "value") else str(claim.type),
    )

    logger.info(
        "llm_web_verifier | claim_id=%s | model=%s | initiating web search | claim=%.80r",
        claim.id, _model, claim.text
    )

    # ── Call Responses API with web_search_preview tool ───────────────────────
    try:
        response = _client.responses.create(
            model=_model,
            tools=[{"type": "web_search_preview"}],
            input=[
                {"role": "system", "content": _WEB_SEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
    except AttributeError:
        # Responses API not available in this SDK version (< 1.66.0)
        return _fallback_unverifiable(
            claim,
            "OpenAI Responses API not available in installed SDK version. "
            "Upgrade with: pip install --upgrade openai"
        )
    except Exception as exc:
        logger.error(
            "llm_web_verifier | claim_id=%s | Responses API call failed: %s",
            claim.id, exc
        )
        return _fallback_unverifiable(claim, f"API call failed: {exc}")

    # ── Extract raw text from response ────────────────────────────────────────
    raw_text = _extract_text_from_response(response)

    if not raw_text or not raw_text.strip():
        return _fallback_unverifiable(claim, "LLM returned empty response after web search")

    logger.debug(
        "llm_web_verifier | claim_id=%s | raw_response_length=%d",
        claim.id, len(raw_text)
    )

    # ── Parse JSON verdict ────────────────────────────────────────────────────
    for attempt in range(2):
        try:
            data = _parse_verdict_json(raw_text)

            verdict_str = str(data["verdict"]).upper()
            label = _VERDICT_MAP[verdict_str]

            evidence_span = data.get("evidence_span") or None
            evidence = [evidence_span] if evidence_span else []

            source_found = data.get("source_found") or ""
            if source_found and evidence_span:
                evidence.append(f"[Source: {source_found}]")

            confidence_raw = data.get("confidence")
            confidence: float | None = None
            if confidence_raw is not None:
                try:
                    confidence = max(0.0, min(1.0, float(confidence_raw)))
                except (TypeError, ValueError):
                    confidence = None

            verdict = Verdict(
                claim_id=claim.id,
                label=label,
                evidence=evidence,
                stage_reached=2,
                confidence=confidence,
                reasoning=data.get("reasoning") or None,
                evidence_span=evidence_span,
                unsupported_detail=data.get("unsupported_detail") or None,
                temporal_flag=False,
                temporal_note=None,
            )

            logger.info(
                "llm_web_verifier | claim_id=%s | label=%s | confidence=%s | source=%r",
                claim.id,
                label.value,
                f"{confidence:.3f}" if confidence is not None else "None",
                source_found[:80] if source_found else "(none)",
            )
            return verdict

        except (json.JSONDecodeError, ValueError) as exc:
            if attempt == 0:
                logger.warning(
                    "llm_web_verifier | claim_id=%s | JSON parse failed on attempt 1 — "
                    "retrying. Error: %s | raw=%.200r",
                    claim.id, exc, raw_text
                )
                # No re-call to LLM, but try stripping more aggressively
                raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            else:
                logger.error(
                    "llm_web_verifier | claim_id=%s | JSON parse failed on attempt 2. "
                    "Error: %s | raw=%.300r",
                    claim.id, exc, raw_text
                )
                return _fallback_unverifiable(
                    claim,
                    f"Could not parse LLM web-search response: {exc}"
                )

    return _fallback_unverifiable(claim, "Unreachable fallback")
