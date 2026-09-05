"""
GET endpoints for analytics dashboard (Person C).

Endpoints:
  GET /analytics/summary - aggregate stats over N days
  GET /analytics/checks - paginated list of recent checks
  GET /analytics/flagged - checks where decision != SAFE
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query
from sqlalchemy import func, and_

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.kb.db import SessionLocal
from api.analytics.models import CheckLog

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/analytics/summary")
async def get_summary(days: int = Query(30, ge=1, le=365)):
    """
    Get aggregate statistics over the last N days.

    Query params:
        days: number of days to look back (default: 30, max: 365)

    Returns:
        {
            "total_checks": 1234,
            "checks_safe": 1000,
            "checks_flagged": 200,
            "checks_abstain": 34,
            "avg_trust_index": 0.81,
            "date_range": {"from": "2026-08-05", "to": "2026-09-04"}
        }
    """
    session = SessionLocal()
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

        # Count checks by decision
        total = session.query(func.count(CheckLog.id)).filter(
            CheckLog.created_at >= cutoff_time
        ).scalar() or 0

        safe_count = session.query(func.count(CheckLog.id)).filter(
            and_(CheckLog.created_at >= cutoff_time, CheckLog.decision == "SAFE")
        ).scalar() or 0

        flagged_count = session.query(func.count(CheckLog.id)).filter(
            and_(CheckLog.created_at >= cutoff_time, CheckLog.decision == "FLAGGED")
        ).scalar() or 0

        abstain_count = session.query(func.count(CheckLog.id)).filter(
            and_(CheckLog.created_at >= cutoff_time, CheckLog.decision == "ABSTAIN")
        ).scalar() or 0

        # Average trust_index
        avg_trust = session.query(func.avg(CheckLog.trust_index)).filter(
            CheckLog.created_at >= cutoff_time
        ).scalar()
        avg_trust = float(avg_trust) if avg_trust else 0.0

        return {
            "total_checks": total,
            "checks_safe": safe_count,
            "checks_flagged": flagged_count,
            "checks_abstain": abstain_count,
            "avg_trust_index": round(avg_trust, 2),
            "date_range": {
                "from": cutoff_time.date().isoformat(),
                "to": datetime.now(timezone.utc).date().isoformat(),
            },
        }
    finally:
        session.close()


@router.get("/analytics/checks")
async def get_checks(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Get paginated list of recent checks.

    Query params:
        limit: max results per page (default: 50, max: 500)
        offset: pagination offset (default: 0)

    Returns:
        {
            "total": 1234,
            "checks": [
                {
                    "request_id": "req-xxx",
                    "trust_index": 0.92,
                    "decision": "SAFE",
                    "created_at": "2026-09-04T15:30:45Z"
                },
                ...
            ]
        }
    """
    session = SessionLocal()
    try:
        total = session.query(func.count(CheckLog.id)).scalar() or 0

        logs = session.query(CheckLog).order_by(
            CheckLog.created_at.desc()
        ).limit(limit).offset(offset).all()

        checks = [
            {
                "request_id": log.request_id,
                "trust_index": round(log.trust_index, 2),
                "decision": log.decision,
                "created_at": log.created_at.isoformat() + "Z",
            }
            for log in logs
        ]

        return {
            "total": total,
            "checks": checks,
        }
    finally:
        session.close()


@router.get("/analytics/flagged")
async def get_flagged(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Get paginated list of flagged checks (decision != SAFE) for review.

    Query params:
        limit: max results per page (default: 50)
        offset: pagination offset (default: 0)

    Returns:
        {
            "total": 234,
            "flagged_checks": [
                {
                    "request_id": "req-xxx",
                    "trust_index": 0.18,
                    "decision": "FLAGGED",
                    "created_at": "2026-09-04T10:20:15Z"
                },
                ...
            ]
        }
    """
    session = SessionLocal()
    try:
        total = session.query(func.count(CheckLog.id)).filter(
            CheckLog.decision != "SAFE"
        ).scalar() or 0

        logs = session.query(CheckLog).filter(
            CheckLog.decision != "SAFE"
        ).order_by(
            CheckLog.created_at.desc()
        ).limit(limit).offset(offset).all()

        checks = [
            {
                "request_id": log.request_id,
                "trust_index": round(log.trust_index, 2),
                "decision": log.decision,
                "created_at": log.created_at.isoformat() + "Z",
            }
            for log in logs
        ]

        return {
            "total": total,
            "flagged_checks": checks,
        }
    finally:
        session.close()
