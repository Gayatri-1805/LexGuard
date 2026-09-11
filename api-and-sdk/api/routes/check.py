"""
POST /check endpoint for hallucination detection.

Accepts a CheckRequest, calls the pipeline, logs results to analytics DB,
and returns the CheckResponse.

Hybrid routing (per-claim):
    kb_lookup hit + relevant info  →  _kb_direct_verdict()  (NO LLM judge)
    kb_lookup hit + irrelevant     →  llm_web_search_verify()  (LLM autonomous web search)
    kb_lookup miss                 →  llm_web_search_verify()  (LLM autonomous web search)
    web search also fails          →  UNVERIFIABLE

Background task logs to DB async (doesn't block response to caller).
"""

import logging
import sys
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import exc as sqlalchemy_exc

# Add both api-and-sdk root and detection-engine root to path
_API_SDK_ROOT = Path(__file__).resolve().parent.parent.parent
_DETECTION_ENGINE_ROOT = _API_SDK_ROOT.parent / "detection-engine"
for _p in (_API_SDK_ROOT, _DETECTION_ENGINE_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from shared.schemas import (
    CheckRequest, CheckResponse, Claim, Verdict, VerdictLabel, Decision
)
from api.kb.db import SessionLocal
from api.analytics.models import CheckLog

# Detection-engine stages
from stages.claim_extractor import extract_claims
from stages.kb_lookup import kb_lookup, KBLookupResult

# LLM autonomous web search verifier (used when KB has no relevant text)
from api.verification.llm_web_verifier import llm_web_search_verify

router = APIRouter()
logger = logging.getLogger(__name__)


def log_check_to_db(request_id: str, trust_index: float, decision: str) -> None:
    """
    Background task: persist check result to analytics DB.

    Args:
        request_id: Unique identifier for this check
        trust_index: Trust score (0-1)
        decision: Final decision (SAFE, FLAGGED, ABSTAIN)
    """
    session = SessionLocal()
    try:
        log_entry = CheckLog(
            request_id=request_id,
            trust_index=trust_index,
            decision=decision,
        )
        session.add(log_entry)
        session.commit()
        logger.info(f"Logged check {request_id} to analytics DB")
    except sqlalchemy_exc.SQLAlchemyError as e:
        logger.error(f"Failed to log check {request_id}: {e}")
        session.rollback()
    except Exception as e:
        logger.error(f"Unexpected error logging check {request_id}: {e}")
    finally:
        session.close()


# ── Trust index / decision helpers (not needed with stub, but kept for reference) ───
_LABEL_SCORES: dict[VerdictLabel, float] = {
    VerdictLabel.SUPPORTED: 1.0,
    VerdictLabel.ENTAILED: 1.0,
    VerdictLabel.PARTIALLY_SUPPORTED: 0.5,
    VerdictLabel.CONTRADICTED: 0.0,
    VerdictLabel.UNVERIFIABLE: 0.5,
    VerdictLabel.NOT_ENOUGH_INFO: 0.5,
    VerdictLabel.LOW_RISK_SKIP: None,   # excluded from trust average
}


def _compute_trust(verdicts: list[Verdict]) -> tuple[float, Decision]:
    """Compute trust_index and Decision from a list of verdicts with enhanced logic."""
    scores = [
        _LABEL_SCORES[v.label]
        for v in verdicts
        if _LABEL_SCORES.get(v.label) is not None
    ]
    if not scores:
        return 0.5, Decision.ABSTAIN
    
    trust = sum(scores) / len(scores)
    
    # Analyze verdict patterns for smarter decisions
    labels = [v.label for v in verdicts]
    has_contradicted = VerdictLabel.CONTRADICTED in labels
    has_supported = any(label in [VerdictLabel.SUPPORTED, VerdictLabel.ENTAILED] for label in labels)
    has_partial = VerdictLabel.PARTIALLY_SUPPORTED in labels
    has_unverifiable = VerdictLabel.UNVERIFIABLE in labels
    
    contradiction_ratio = labels.count(VerdictLabel.CONTRADICTED) / len(labels)
    support_ratio = sum(1 for label in labels if label in [VerdictLabel.SUPPORTED, VerdictLabel.ENTAILED]) / len(labels)
    
    # Enhanced decision logic with better partial hallucination handling
    if contradiction_ratio >= 0.4:  # 40%+ contradicted → Flag (lowered from 50%)
        decision = Decision.FLAGGED
    elif has_contradicted and not has_supported:  # Only contradictions, no support
        decision = Decision.FLAGGED
    elif has_contradicted and has_supported and contradiction_ratio >= 0.2:  # Mixed with significant contradictions
        decision = Decision.ABSTAIN
    elif support_ratio >= 0.6 and not has_contradicted:  # Good support without contradictions
        decision = Decision.SAFE
    elif has_supported and trust >= 0.75 and not has_contradicted:  # High trust with some support, no contradictions
        decision = Decision.SAFE
    elif has_partial and not has_contradicted:  # Partial but not contradicted
        decision = Decision.ABSTAIN
    elif has_contradicted and has_supported:  # Any mixed evidence → abstain
        decision = Decision.ABSTAIN
    elif trust >= 0.8:  # Very high trust (lowered from 0.85)
        decision = Decision.SAFE
    elif trust <= 0.3:  # Very low trust (raised from 0.25)
        decision = Decision.FLAGGED
    else:  # Uncertain middle ground
        decision = Decision.ABSTAIN
    
    return round(trust, 4), decision


def _unverifiable(claim: Claim, note: str) -> Verdict:
    """Shorthand: return an UNVERIFIABLE verdict with a note."""
    return Verdict(
        claim_id=claim.id,
        label=VerdictLabel.UNVERIFIABLE,
        evidence=[],
        stage_reached=2,
        reasoning=note,
    )


# ── KB direct verdict helpers ─────────────────────────────────────────────────

def _detect_contradiction(claim_text: str, passage_text: str) -> bool:
    """Heuristic check: does the passage contradict the claim?

    Looks for negation-flip patterns — e.g., the claim asserts something
    positively that the passage negates, or vice versa.
    This is intentionally conservative (requires clear flip signals) to avoid
    false CONTRADICTED verdicts on genuinely related but imprecise matches.

    Returns True only if an obvious contradiction signal is found.
    """
    claim_lower = claim_text.lower()
    passage_lower = passage_text.lower()

    # Negative phrases that reverse the meaning of an assertion
    negative_phrases = [
        "does not apply", "shall not apply", "not applicable",
        "no liability", "not liable", "no obligation",
        "shall not be", "not required", "need not",
        "no compensation", "cannot be held", "not punishable",
        "not an offence", "no penalty", "does not include",
    ]
    positive_phrases = [
        "does apply", "shall apply", "applicable",
        "liability", "liable", "obligation",
        "shall be", "is required", "must",
        "compensation", "punishable", "is an offence",
        "penalty", "includes",
    ]

    claim_is_negative = any(ph in claim_lower for ph in negative_phrases)
    passage_is_negative = any(ph in passage_lower for ph in negative_phrases)
    claim_is_positive = any(ph in claim_lower for ph in positive_phrases)
    passage_is_positive = any(ph in passage_lower for ph in positive_phrases)

    # Case 1: Claim says NOT X, passage says X (without negation)
    if claim_is_negative and passage_is_positive and not passage_is_negative:
        logger.debug("_detect_contradiction: claim negates, passage affirms — CONTRADICTED")
        return True

    # Case 2: Claim says X, passage says NOT X
    if claim_is_positive and passage_is_negative and not claim_is_negative:
        logger.debug("_detect_contradiction: claim affirms, passage negates — CONTRADICTED")
        return True

    return False


def _has_relevant_info(claim: Claim, kb_result: KBLookupResult) -> bool:
    """Check whether the KB passage is actually relevant to this specific claim.

    Returns False when kb_lookup technically returned hit=True but the best
    passage is about a *different* section or concept than what the claim
    asserts.  In that case the caller falls through to LLM web search.

    Decision logic
    --------------
    - Exact Postgres match                    → always relevant
    - Semantic score >= 0.70                  → assume relevant (strong similarity)
    - 0.45 <= score < 0.70 (borderline hit):
        * If claim mentions specific section numbers (e.g., "Section 66A"):
          check that the passage mentions those sections.  If not → irrelevant.
        * Otherwise trust the semantic score.
    """
    import re as _re

    best = kb_result.passages[0]

    # Exact match from Postgres is always relevant
    if best.metadata.get("match_type") == "exact":
        return True

    # Strong semantic similarity → assume relevant
    if best.score >= 0.70:
        return True

    # Borderline hit: verify section-level relevance
    claim_text_lower = claim.text.lower()
    citation_lower = (claim.citation or "").lower()
    passage_lower = best.text.lower()

    # Extract section numbers like "66", "43A", "66B" from claim
    section_nums = _re.findall(
        r'section\s+(\d+[a-z]?)',
        claim_text_lower + " " + citation_lower
    )

    if section_nums:
        # Claim references specific sections — passage must mention at least one
        for sec in section_nums:
            if sec in passage_lower or f"section {sec}" in passage_lower:
                return True
        # Passage doesn't mention the claimed sections → not relevant
        logger.info(
            "check._has_relevant_info | claim_id=%s | sections=%s not in passage | "
            "score=%.3f — treating as no relevant info, falling back to web search",
            claim.id, section_nums, best.score
        )
        return False

    # No specific section reference — trust the borderline semantic score
    return True


def _kb_direct_verdict(claim: Claim, kb_result: KBLookupResult) -> Verdict | None:
    """Convert a KBLookupResult directly into a Verdict — without calling the LLM.

    Called only when kb_result.hit is True.

    Returns
    -------
    Verdict
        When the KB passage is relevant to the claim.
        Label is one of SUPPORTED, CONTRADICTED, or PARTIALLY_SUPPORTED.
    None
        When the KB passage is off-topic for this claim (e.g., wrong section
        retrieved due to borderline semantic similarity).  The caller should
        fall through to LLM autonomous web search.

    Labelling rules (no LLM involved)
    ----------------------------------
    ┌─────────────────────────────────────┬───────────────────────────────────┐
    │ Condition                           │ Label                             │
    ├─────────────────────────────────────┼───────────────────────────────────┤
    │ No relevant info in passage         │ None  (→ web search fallback)     │
    │ Contradiction signals detected      │ CONTRADICTED                      │
    │ score ≥ 0.90 or exact match         │ SUPPORTED                         │
    │ 0.70 ≤ score < 0.90                 │ PARTIALLY_SUPPORTED               │
    │ 0.45 ≤ score < 0.70 (still relevant)│ PARTIALLY_SUPPORTED               │
    └─────────────────────────────────────┴───────────────────────────────────┘
    """
    if not _has_relevant_info(claim, kb_result):
        return None  # Signal: fall through to LLM web search

    best = kb_result.passages[0]
    score = best.score
    is_exact = best.metadata.get("match_type") == "exact"

    # ── Contradiction check (heuristic, no LLM) ───────────────────────────────
    # Only run contradiction detection on high-confidence matches to avoid
    # false negatives on borderline semantic matches.
    if score >= 0.70 or is_exact:
        if _detect_contradiction(claim.text, best.text):
            logger.info(
                "check._kb_direct_verdict | claim_id=%s | label=CONTRADICTED | "
                "score=%.3f | source=%s",
                claim.id, score, best.source
            )
            return Verdict(
                claim_id=claim.id,
                label=VerdictLabel.CONTRADICTED,
                evidence=[best.text[:600]],
                stage_reached=2,
                confidence=round(score, 3),
                reasoning=(
                    f"KB passage contradicts the claim (heuristic negation detection). "
                    f"Source: {best.source} (score={score:.3f})"
                ),
                evidence_span=best.text[:300] if best.text else None,
                unsupported_detail="Claim assertion is negated by the authoritative KB passage.",
                temporal_flag=False,
                temporal_note=None,
            )

    # ── Score-based verdict ───────────────────────────────────────────────────
    if is_exact or score >= 0.90:
        label = VerdictLabel.SUPPORTED
        reasoning = (
            f"KB exact/near-exact match (score={score:.3f}). "
            f"Source: {best.source}. No LLM judge needed."
        )
    else:
        label = VerdictLabel.PARTIALLY_SUPPORTED
        reasoning = (
            f"KB semantic match (score={score:.3f}) — related but not an exact match. "
            f"Source: {best.source}. Claim may have nuances not covered by this passage."
        )

    logger.info(
        "check._kb_direct_verdict | claim_id=%s | label=%s | score=%.3f | source=%s",
        claim.id, label.value, score, best.source
    )

    return Verdict(
        claim_id=claim.id,
        label=label,
        evidence=[best.text[:600]],
        stage_reached=2,
        confidence=round(score, 3),
        reasoning=reasoning,
        evidence_span=best.text[:300] if best.text else None,
        unsupported_detail=None,
        temporal_flag=False,
        temporal_note=None,
    )


# ── Per-claim routing ─────────────────────────────────────────────────────────
def _route_claim(claim: Claim) -> Verdict:
    """
    Route one claim through the modified hybrid pipeline.

    Decision flow
    -------------
    1. kb_lookup — FAISS semantic + Postgres exact search
       a. hit=True AND passage is relevant to this claim
          → _kb_direct_verdict() — NO LLM judge; verdict from KB score/text
            • SUPPORTED       if score ≥ 0.90 or exact match (no contradiction)
            • CONTRADICTED    if contradiction signal detected in passage
            • PARTIALLY_SUPPORTED  otherwise (semantic match, borderline)
       b. hit=True BUT passage is off-topic for the specific claim
          → fall through to step 2
       c. hit=False
          → fall through to step 2

    2. llm_web_search_verify — LLM autonomously searches the web
       Uses OpenAI Responses API with web_search_preview tool.
       LLM finds authoritative Indian legal sources and returns verdict.
       → SUPPORTED / CONTRADICTED / PARTIALLY_SUPPORTED / UNVERIFIABLE

    3. If web search also fails → UNVERIFIABLE

    Never raises — one bad claim must not kill the whole batch.
    """
    # ── Step 1: KB lookup ──────────────────────────────────────────────────────
    try:
        kb_result = kb_lookup(claim)
        if kb_result.hit and kb_result.passages:
            verdict = _kb_direct_verdict(claim, kb_result)
            if verdict is not None:
                # KB had relevant info — return directly, no LLM needed
                return verdict
            # verdict is None → passage was off-topic → fall through to web search
            logger.info(
                "check._route_claim | claim_id=%s | KB hit but irrelevant passage — "
                "falling back to LLM web search",
                claim.id
            )
        else:
            logger.info(
                "check._route_claim | claim_id=%s | KB miss (score=%.3f) — "
                "falling back to LLM web search",
                claim.id, kb_result.best_score
            )
    except Exception as exc:
        logger.error(
            "check._route_claim | claim_id=%s | kb_lookup error: %s — "
            "falling back to LLM web search",
            claim.id, exc
        )

    # ── Step 2: LLM autonomous web search ─────────────────────────────────────
    try:
        return llm_web_search_verify(claim)
    except Exception as exc:
        logger.error(
            "check._route_claim | claim_id=%s | llm_web_search_verify error: %s",
            claim.id, exc
        )

    return _unverifiable(claim, note="all verification methods failed")


@router.post("/check", response_model=CheckResponse)
async def check_hallucination(
    request: CheckRequest,
    background_tasks: BackgroundTasks,
) -> CheckResponse:
    """
    Check LLM output for hallucinations using the modified hybrid pipeline.

    Per-claim routing (modified hybrid approach):
        1. extract_claims   — decompose text into atomic legal claims
        2. kb_lookup        — FAISS semantic search + Postgres exact lookup
           a. hit=True AND relevant passage  → _kb_direct_verdict() (NO LLM judge)
              • SUPPORTED            if score >= 0.90 or exact Postgres match
              • CONTRADICTED         if heuristic negation/flip detected in passage
              • PARTIALLY_SUPPORTED  if semantic match (0.45 <= score < 0.90)
           b. hit=True BUT off-topic passage  OR  hit=False
              → llm_web_search_verify()
                • LLM autonomously searches web (OpenAI Responses API + web_search_preview)
                • Returns SUPPORTED / CONTRADICTED / PARTIALLY_SUPPORTED / UNVERIFIABLE
        3. Aggregate trust_index and Decision across all verdicts

    Background:
        - Logs result to analytics DB (non-blocking)

    Raises:
        HTTPException 500 if claim extraction fails
    """
    try:
        claims: list[Claim] = extract_claims(request.text)
    except Exception as e:
        logger.error(f"Claim extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Claim extraction failed: {str(e)}",
        )

    verdicts: list[Verdict] = [_route_claim(c) for c in claims]
    trust_index, decision = _compute_trust(verdicts)

    response = CheckResponse(
        request_id=request.request_id or str(uuid4()),
        claims=claims,
        verdicts=verdicts,
        trust_index=trust_index,
        decision=decision,
    )

    # Use caller's request_id if provided
    if request.request_id:
        response = CheckResponse(
            request_id=request.request_id,
            claims=response.claims,
            verdicts=response.verdicts,
            trust_index=response.trust_index,
            decision=response.decision,
            created_at=response.created_at,
        )

    background_tasks.add_task(
        log_check_to_db,
        request_id=response.request_id,
        trust_index=response.trust_index,
        decision=response.decision.value,
    )

    return response
