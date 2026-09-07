"""
POST /check endpoint for hallucination detection.

Accepts a CheckRequest, calls the pipeline, logs results to analytics DB,
and returns the CheckResponse.

Background task logs to DB async (doesn't block response to caller).
"""

import logging
import sys
from pathlib import Path
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
from stages.kb_lookup import kb_lookup
from stages.verdict import get_verdict

# Verification fallback
# from api.verification.fallback_search import fallback_search

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


# ── Trust index / decision helpers ───────────────────────────────────────────
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
    """Compute trust_index and Decision from a list of verdicts."""
    scores = [
        _LABEL_SCORES[v.label]
        for v in verdicts
        if _LABEL_SCORES.get(v.label) is not None
    ]
    if not scores:
        return 1.0, Decision.ABSTAIN
    trust = sum(scores) / len(scores)
    if trust >= 0.7:
        decision = Decision.SAFE
    elif trust <= 0.35:
        decision = Decision.FLAGGED
    else:
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


# ── Per-claim routing ─────────────────────────────────────────────────────────
def _route_claim(claim: Claim) -> Verdict:
    """
    Route one claim through KB → fallback → get_verdict.

    1. kb_lookup: FAISS semantic search
       - hit=True  → get_verdict on the best KB passage
    2. fallback_search: LawCite / Indian Kanoon / Google CSE
       - found=True → get_verdict on the first fallback passage
    3. Neither found   → UNVERIFIABLE ("no source found")

    Never raises — one bad claim must not kill the whole batch.
    """
    try:
        kb_result = kb_lookup(claim)
        if kb_result.hit and kb_result.passages:
            best = kb_result.passages[0]
            return get_verdict(
                claim,
                excerpt_text=best.text,
                source_name=best.source,
                source_url=best.metadata.get("url", best.source),
            )
    except Exception as exc:
        logger.error("check._route_claim: kb_lookup error for claim_id=%s — %s",
                     claim.id, exc)

    # try:
    #     fb_result = fallback_search(claim)
    #     if fb_result.found and fb_result.passages:
    #         first = fb_result.passages[0]
    #         return get_verdict(
    #             claim,
    #             excerpt_text=first.text,
    #             source_name=first.source,
    #             source_url=first.url,
    #         )
    # except Exception as exc:
    #     logger.error("check._route_claim: fallback_search error for claim_id=%s — %s",
    #                  claim.id, exc)

    return _unverifiable(claim, note="no source found")


@router.post("/check", response_model=CheckResponse)
async def check_hallucination(
    request: CheckRequest,
    background_tasks: BackgroundTasks,
) -> CheckResponse:
    """
    Check LLM output for hallucinations using multi-stage pipeline.

    Per-claim routing:
        1. extract_claims   — decompose text into atomic legal claims
        2. kb_lookup        — FAISS semantic search against local KB
           └ hit:   get_verdict(claim, best KB passage)
           └ miss:  fallback_search (LawCite / Indian Kanoon / Google CSE)
              └ found:  get_verdict(claim, first fallback passage)
              └ empty:  UNVERIFIABLE, note="no source found"
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
        request_id=request.request_id or None,
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
