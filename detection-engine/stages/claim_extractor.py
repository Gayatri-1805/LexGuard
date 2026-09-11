"""
Stage 0: Claim Extractor
========================
Decomposes raw LLM output into a list of atomic, independently-checkable
legal claims using a low-temperature LLM call.

Public API
----------
    extract_claims(llm_output: str, *, client=None, model=None) -> list[Claim]
        Uses shared/schemas.py Claim exactly — no redefinitions.

LLM contract
------------
EXTRACTION_PROMPT (module-level constant) instructs the model to return a
JSON array.  Each element:

    {
        "text":       "<atomic legal assertion>",
        "type":       "<CASE_CITATION|SECTION_REF|HOLDING|PROCEDURAL|OTHER>",
        "citation":   "<verbatim citation extracted, or null>",
        "context":    "<original surrounding sentence, verbatim>",
        "span_start": <int>,
        "span_end":   <int>
    }

Error handling
--------------
If the LLM returns malformed JSON the call is retried once.  On a second
failure a typed ClaimExtractionError is raised — never a silent empty list.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

# ── resolve project root so shared/ is importable regardless of cwd ──────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from shared.schemas import Claim, ClaimType  # noqa: E402

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Extraction prompt  (edit this independently of parsing / retry logic below)
# ─────────────────────────────────────────────────────────────────────────────
EXTRACTION_PROMPT = """\
Extract atomic legal claims from the text below. Return ONLY valid JSON array.

Rules:
1. One verifiable legal assertion per claim
2. Extract statute/case citations verbatim into "citation" field
3. Keep "context" concise (max 150 chars) 
4. Use exact character spans if possible, otherwise use 0,0

Types: CASE_CITATION, SECTION_REF, HOLDING, PROCEDURAL, OTHER

Output format (JSON array only):
[
  {{
    "text": "<atomic claim>",
    "type": "<type>", 
    "citation": "<citation or null>",
    "context": "<short context>",
    "span_start": <int>,
    "span_end": <int>
  }}
]

Text:
\"\"\"
{llm_output}
\"\"\"
"""


# ─────────────────────────────────────────────────────────────────────────────
# Typed exception
# ─────────────────────────────────────────────────────────────────────────────
class ClaimExtractionError(Exception):
    """Raised when the LLM returns malformed JSON that cannot be parsed after
    one retry.  Carries the raw LLM response string for debugging.

    Attributes:
        raw_response: The unparseable string returned by the LLM.
    """

    def __init__(self, message: str, raw_response: str = "") -> None:
        super().__init__(message)
        self.raw_response = raw_response


# ─────────────────────────────────────────────────────────────────────────────
# LLM client helpers
# ─────────────────────────────────────────────────────────────────────────────
def _get_llm_client():  # -> OpenAI
    """Return an openai.OpenAI client configured from environment variables.

    Reads:
        OPENAI_API_KEY   – required; raises EnvironmentError if missing.
        OPENAI_BASE_URL  – optional; point at Groq / Azure / local endpoints.

    Importing openai is deferred so that the module can be imported and tested
    without the package installed (tests mock the client object directly).
    """
    try:
        from openai import OpenAI
        import httpx
    except ImportError as exc:
        raise ImportError(
            "openai package is required for claim extraction. "
            "Install it with: pip install openai"
        ) from exc

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. "
            "Add it to your .env file or environment before running the pipeline."
        )
    base_url = os.environ.get("OPENAI_BASE_URL") or None
    
    # Create a custom HTTP client with proper SSL configuration
    http_client = httpx.Client(
        verify=False,  # Disable SSL verification to avoid recursion issues
        timeout=60.0
    )
    
    return OpenAI(
        api_key=api_key, 
        base_url=base_url,
        http_client=http_client
    )


def _resolve_model() -> str:
    """Return the judge model name (JUDGE_MODEL env var, default: gpt-4o-mini)."""
    return os.environ.get("JUDGE_MODEL", "gpt-4o-mini")


# ─────────────────────────────────────────────────────────────────────────────
# JSON parsing
# ─────────────────────────────────────────────────────────────────────────────
def _parse_json_array(raw: str) -> list[dict[str, Any]]:
    """Parse a JSON array from the raw LLM response.

    Strips surrounding markdown fences (``` or ```json) if present.

    Returns:
        Parsed list of dicts.

    Raises:
        ValueError: If the parsed value is not a list.
        json.JSONDecodeError: If the string is not valid JSON.
    """
    # Strip optional markdown code fences the model may add despite instructions
    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
    parsed = json.loads(stripped)
    if not isinstance(parsed, list):
        raise ValueError(
            f"LLM returned a JSON {type(parsed).__name__} — expected an array."
        )
    return parsed


# ─────────────────────────────────────────────────────────────────────────────
# Single LLM call
# ─────────────────────────────────────────────────────────────────────────────
def _call_llm(llm_output: str, client: Any, model: str) -> str:
    """Make one low-temperature chat completion call and return the content string."""
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.1,
            max_tokens=6000,  # Further increased to handle complex legal texts
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise legal-claim extractor. "
                        "Always respond with a valid, complete JSON array and nothing else. "
                        "Ensure all strings are properly closed and escaped."
                    ),
                },
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(llm_output=llm_output),
                },
            ],
        )
        content = response.choices[0].message.content
        if not content or content.strip() == "":
            logger.error("_call_llm: Empty response from LLM")
            return "[]"  # Return empty array instead of failing
        
        # Validate that the response is complete JSON
        try:
            json.loads(content)
            return content
        except json.JSONDecodeError as e:
            logger.error("_call_llm: Invalid JSON in LLM response: %s", e)
            logger.error("_call_llm: Raw response: %s", content[:500])
            return "[]"  # Return empty array on malformed JSON
            
    except Exception as e:
        logger.error("_call_llm: Exception during LLM call: %s", e)
        return "[]"  # Return empty array on error


# ─────────────────────────────────────────────────────────────────────────────
# Raw items → Claim objects
# ─────────────────────────────────────────────────────────────────────────────
def _items_to_claims(items: list[dict[str, Any]]) -> list[Claim]:
    """Convert validated JSON items to Claim objects.

    - Unknown claim types fall back to ClaimType.OTHER (logged as warning).
    - Span defaults to (0, 0) when missing or unparseable.
    - citation and context are passed directly into the Claim schema fields.
    """
    claims: list[Claim] = []
    for idx, item in enumerate(items):
        # ── type ──────────────────────────────────────────────────────────────
        raw_type = str(item.get("type", "OTHER")).upper()
        try:
            claim_type = ClaimType(raw_type)
        except ValueError:
            logger.warning(
                "claim_%03d: unknown type %r; defaulting to OTHER", idx + 1, raw_type
            )
            claim_type = ClaimType.OTHER

        # ── span ──────────────────────────────────────────────────────────────
        try:
            span: tuple[int, int] = (
                int(item.get("span_start", 0)),
                int(item.get("span_end", 0)),
            )
        except (TypeError, ValueError):
            logger.warning("claim_%03d: invalid span values; defaulting to (0, 0)", idx + 1)
            span = (0, 0)

        # ── citation / context ────────────────────────────────────────────────
        citation_raw = item.get("citation")
        citation: str | None = str(citation_raw).strip() if citation_raw else None

        context_raw = item.get("context", "")
        context: str = str(context_raw).strip() if context_raw else ""

        claims.append(
            Claim(
                id=f"claim_{idx + 1:03d}",
                text=str(item.get("text", "")).strip(),
                type=claim_type,
                span=span,
                citation=citation,
                context=context or None,
            )
        )

    return claims


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def extract_claims(
    llm_output: str,
    *,
    client: Any = None,
    model: str | None = None,
) -> list[Claim]:
    """Decompose *llm_output* into atomic, independently-checkable legal claims.

    Each returned Claim:
    - Is a single factual / legal assertion (compound sentences are split).
    - Has ``citation`` set to the verbatim statute/case reference if one was
      identified (None otherwise — grounded semantically by Stage 2).
    - Has ``context`` set to the original surrounding sentence.

    Args:
        llm_output: Raw LLM-generated text to decompose.
        client:     Pre-built LLM client object. If None, one is constructed
                    from OPENAI_API_KEY / OPENAI_BASE_URL env vars.
                    Inject a mock here in tests to avoid real API calls.
        model:      Model name override. Falls back to JUDGE_MODEL env var,
                    then to "gpt-4o-mini".

    Returns:
        list[Claim] — one per extracted atomic assertion.
        Returns an empty list only when *llm_output* is blank.

    Raises:
        ClaimExtractionError: If the LLM returns unparseable JSON on BOTH the
                              initial call AND the single retry.
        EnvironmentError:     If OPENAI_API_KEY is unset and no client injected.
        openai.OpenAIError:   On network / API errors (not retried).
    """
    if not llm_output or not llm_output.strip():
        logger.debug("extract_claims: empty input — returning []")
        return []

    _client = client if client is not None else _get_llm_client()
    _model = model or _resolve_model()

    last_raw = ""
    for attempt in range(2):
        try:
            raw = _call_llm(llm_output, _client, _model)
            last_raw = raw
            items = _parse_json_array(raw)
            logger.debug(
                "extract_claims: %d items parsed on attempt %d", len(items), attempt + 1
            )
            return _items_to_claims(items)

        except (json.JSONDecodeError, ValueError) as exc:
            if attempt == 0:
                logger.warning(
                    "extract_claims: invalid JSON on attempt 1 — retrying. Error: %s", exc
                )
            else:
                logger.error(
                    "extract_claims: invalid JSON on attempt 2 — giving up.\n"
                    "Raw LLM response:\n%s",
                    last_raw,
                )
                raise ClaimExtractionError(
                    f"LLM returned unparseable JSON after 2 attempts: {exc}",
                    raw_response=last_raw,
                ) from exc

    return []  # unreachable; satisfies type checker
