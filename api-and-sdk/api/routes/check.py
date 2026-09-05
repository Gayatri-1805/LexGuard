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

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.schemas import CheckRequest, CheckResponse
from api.kb.db import SessionLocal
from api.analytics.models import CheckLog

# Import pipeline (swap with real pipeline when ready)
from api.pipeline_stub import check as PIPELINE_CHECK_FN

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


@router.post("/check", response_model=CheckResponse)
async def check_hallucination(
    request: CheckRequest,
    background_tasks: BackgroundTasks,
) -> CheckResponse:
    """
    Check LLM output for hallucinations using multi-stage pipeline.

    Request:
        - text (required): LLM output to analyze
        - context (optional): prompt or framing context
        - request_id (optional): caller's request identifier

    Response:
        CheckResponse with claims, verdicts, trust_index, and decision

    Background:
        - Logs result to analytics DB for dashboard consumption
        - Does not block response to caller

    Raises:
        HTTPException 500 if pipeline fails (with error details)
    """
    try:
        # Call pipeline
        response = PIPELINE_CHECK_FN(text=request.text, context=request.context)

        # Use caller's request_id if provided, otherwise use response's generated ID
        if request.request_id:
            # Create a new response with the caller's request_id
            response = CheckResponse(
                request_id=request.request_id,
                claims=response.claims,
                verdicts=response.verdicts,
                trust_index=response.trust_index,
                decision=response.decision,
                created_at=response.created_at,
            )

        # Queue background task to log to DB
        background_tasks.add_task(
            log_check_to_db,
            request_id=response.request_id,
            trust_index=response.trust_index,
            decision=response.decision.value,
        )

        return response

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Hallucination detection failed: {str(e)}",
        )
