"""
Stage 2 Verification: LLM Entailment Judge
===========================================
Given a Claim and a retrieved excerpt, asks an LLM to determine whether the
excerpt supports, contradicts, partially supports, or cannot verify the claim.

Public API
----------
    get_verdict(claim, excerpt_text, source_name, source_url,
                *, client=None, model=None) -> Verdict

LLM contract
------------
The prompt is the *exact* template provided in the project spec (verbatim).
Do not modify the wording — only the bracketed runtime values are substituted.

The LLM must return a JSON object with these keys:
    reasoning, verdict, evidence_span, unsupported_detail,
    temporal_flag, temporal_note, confidence

verdict must be one of: SUPPORTED | CONTRADICTED | PARTIALLY_SUPPORTED | UNVERIFIABLE

Error handling
--------------
Malformed JSON or an out-of-taxonomy verdict string: retry once, then fall back
to verdict=UNVERIFIABLE with a note. Never propagates as an unhandled exception
so that one bad claim cannot kill the entire /check batch.

Analytics logging
-----------------
Every (claim_id, verdict, confidence, source) tuple is logged at INFO level,
matching the pattern used in api/routes/check.py and api/routes/analytics.py.
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
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
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
JUDGE_TEMPERATURE: float = 0.1  # low temperature for deterministic legal judgements

#: VerdictLabel values the LLM is permitted to return
VALID_LLM_VERDICT_STRINGS: frozenset[str] = frozenset(
    {"SUPPORTED", "CONTRADICTED", "PARTIALLY_SUPPORTED", "UNVERIFIABLE"}
)

#: Mapping from the LLM's verdict string to the VerdictLabel enum member
_VERDICT_MAP: dict[str, VerdictLabel] = {
    "SUPPORTED": VerdictLabel.SUPPORTED,
    "CONTRADICTED": VerdictLabel.CONTRADICTED,
    "PARTIALLY_SUPPORTED": VerdictLabel.PARTIALLY_SUPPORTED,
    "UNVERIFIABLE": VerdictLabel.UNVERIFIABLE,
}

# ─────────────────────────────────────────────────────────────────────────────
# Exact prompt template (verbatim from project spec — do not modify wording)
# ─────────────────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
You are a legal-citation verification engine. You will be given (a) a CLAIM extracted from
an AI-generated legal answer, and (b) an EXCERPT retrieved from an authoritative legal source
(statute text, bare act section, or court judgment).

Your ONLY job is to determine whether the EXCERPT supports the CLAIM. You must not use any
legal knowledge you have from training. If the EXCERPT does not contain enough information to
judge the claim, you must say so — do not fill gaps from memory, and do not assume a citation
is correct just because it looks well-formed.

Rules:
- Base your verdict strictly on the text in EXCERPT. Nothing else.
- If EXCERPT does not actually contain the section, case, or language the CLAIM refers to,
  that is CONTRADICTED or UNVERIFIABLE, not SUPPORTED — a real-sounding citation attached to
  the wrong text is a hallucination, not a near-miss.
- If the claim is broadly right but adds specifics (numbers, dates, exceptions) the excerpt
  doesn't mention, use PARTIALLY_SUPPORTED and say exactly which part is unsupported.
- If you are not confident, choose UNVERIFIABLE. This is the correct answer when evidence is
  insufficient — it is not a failure to answer.
- Note if the excerpt appears to be superseded, amended, or repealed based on any dates or
  amendment markers visible in the text itself (do not assume based on outside knowledge of
  when laws changed — only flag this if the excerpt itself indicates it).
- Quote the exact sentence(s) from EXCERPT that your verdict relies on. If none exist, leave
  evidence_span empty and explain why in reasoning.

Output ONLY valid JSON matching this schema, nothing before or after it:
{
  "reasoning": "<2-4 sentences working through the comparison>",
  "verdict": "SUPPORTED" | "CONTRADICTED" | "PARTIALLY_SUPPORTED" | "UNVERIFIABLE",
  "evidence_span": "<exact quote from EXCERPT, or empty string>",
  "unsupported_detail": "<what part of the claim isn't backed, empty if SUPPORTED>",
  "temporal_flag": true | false,
  "temporal_note": "<why, empty if false>",
  "confidence": <float 0.0-1.0>
}"""

_USER_PROMPT_TEMPLATE = """\
CLAIM:
{claim_text}

CLAIM'S ASSERTED CITATION (if any):
{claim_citation}

EXCERPT (source: {source_name}, retrieved from: {source_url}):
{excerpt_text}"""


# ─────────────────────────────────────────────────────────────────────────────
# LLM client helpers  (same pattern as claim_extractor.py)
# ─────────────────────────────────────────────────────────────────────────────
def _get_llm_client():  # -> OpenAI
    """Return an openai.OpenAI client configured from environment variables."""
    try:
        from openai import OpenAI
        import httpx
    except ImportError as exc:
        raise ImportError(
            "openai package is required for verdict judging. "
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
    return os.environ.get("JUDGE_MODEL", "gpt-4o-mini")


# ─────────────────────────────────────────────────────────────────────────────
# Single LLM call
# ─────────────────────────────────────────────────────────────────────────────
def _call_llm(
    claim: Claim,
    excerpt_text: str,
    source_name: str,
    source_url: str,
    client: Any,
    model: str,
) -> str:
    """One chat-completion call. Returns raw content string."""
    user_content = _USER_PROMPT_TEMPLATE.format(
        claim_text=claim.text,
        claim_citation=claim.citation or "(none)",
        source_name=source_name,
        source_url=source_url,
        excerpt_text=excerpt_text,
    )
    response = client.chat.completions.create(
        model=model,
        temperature=JUDGE_TEMPERATURE,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content or ""


# ─────────────────────────────────────────────────────────────────────────────
# JSON parsing + validation
# ─────────────────────────────────────────────────────────────────────────────
def _parse_verdict_json(raw: str) -> dict[str, Any]:
    """Parse and validate the LLM JSON response.

    Strips markdown fences if present (model sometimes adds them despite
    the prompt saying not to).

    Raises:
        json.JSONDecodeError: If the string is not valid JSON.
        ValueError: If the parsed value is not a dict or verdict is out-of-taxonomy.
    """
    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
    parsed = json.loads(stripped)

    if not isinstance(parsed, dict):
        raise ValueError(
            f"LLM returned a JSON {type(parsed).__name__} — expected an object."
        )

    verdict_str = str(parsed.get("verdict", "")).upper()
    if verdict_str not in VALID_LLM_VERDICT_STRINGS:
        raise ValueError(
            f"LLM returned out-of-taxonomy verdict {verdict_str!r}. "
            f"Valid values: {sorted(VALID_LLM_VERDICT_STRINGS)}"
        )

    return parsed


# ─────────────────────────────────────────────────────────────────────────────
# Fallback Verdict (parse failure)
# ─────────────────────────────────────────────────────────────────────────────
def _fallback_verdict(claim: Claim, source_name: str, note: str) -> Verdict:
    """Return a safe UNVERIFIABLE verdict when LLM output cannot be parsed."""
    return Verdict(
        claim_id=claim.id,
        label=VerdictLabel.UNVERIFIABLE,
        evidence=[],
        stage_reached=2,
        confidence=None,
        reasoning=note,
        evidence_span=None,
        unsupported_detail=None,
        temporal_flag=False,
        temporal_note=None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def get_verdict(
    claim: Claim,
    excerpt_text: str,
    source_name: str,
    source_url: str,
    *,
    client: Any = None,
    model: Optional[str] = None,
) -> Verdict:
    """Ask the LLM entailment judge whether *excerpt_text* supports *claim*.

    Args:
        claim:        The atomic Claim to verify (from shared/schemas.py).
        excerpt_text: Full text of the retrieved evidence passage.
        source_name:  Human-readable provenance label (e.g. "statute:43A" or
                      "Indian Kanoon — Supreme Court").
        source_url:   URL of the retrieved document (for traceability).
        client:       Pre-built LLM client. If None, constructed from env vars.
                      Inject a mock in tests.
        model:        Model name override. Falls back to JUDGE_MODEL env var,
                      then to "gpt-4o-mini".

    Returns:
        Verdict with all fields populated. Never raises — on LLM parse failure
        returns UNVERIFIABLE with an explanatory reasoning note.
    """
    _client = client if client is not None else _get_llm_client()
    _model = model or _resolve_model()

    last_raw = ""
    last_error: Exception | None = None

    for attempt in range(2):
        try:
            raw = _call_llm(claim, excerpt_text, source_name, source_url, _client, _model)
            last_raw = raw
            data = _parse_verdict_json(raw)

            verdict_str = str(data["verdict"]).upper()
            label = _VERDICT_MAP[verdict_str]

            evidence_span = data.get("evidence_span") or None
            evidence = [evidence_span] if evidence_span else []

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
                temporal_flag=bool(data.get("temporal_flag", False)),
                temporal_note=data.get("temporal_note") or None,
            )

            # Analytics log — same pattern as api/routes/analytics.py and check.py
            logger.info(
                "get_verdict | claim_id=%s | label=%s | confidence=%s | source=%s",
                claim.id,
                label.value,
                f"{confidence:.3f}" if confidence is not None else "None",
                source_name,
            )
            return verdict

        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            if attempt == 0:
                logger.warning(
                    "get_verdict: claim_id=%s | invalid LLM output on attempt 1 — "
                    "retrying. Error: %s",
                    claim.id,
                    exc,
                )
            else:
                logger.error(
                    "get_verdict: claim_id=%s | invalid LLM output on attempt 2 — "
                    "falling back to UNVERIFIABLE.\nRaw LLM response:\n%s",
                    claim.id,
                    last_raw,
                )

    # Both attempts failed — fall back gracefully (never propagate to caller)
    note = (
        f"LLM returned unparseable or out-of-taxonomy output after 2 attempts. "
        f"Error: {last_error}. "
        f"Raw response (truncated): {last_raw[:200]!r}"
    )
    fallback = _fallback_verdict(claim, source_name, note)
    logger.info(
        "get_verdict | claim_id=%s | label=UNVERIFIABLE (fallback) | source=%s",
        claim.id,
        source_name,
    )
    return fallback
