"""
Analytics ORM models for persisting check results.

CheckLog: records each hallucination detection check for dashboard analytics.
Minimal schema for MVP (Person C owns the full analytics design).

Columns:
  - id: Primary key
  - request_id: Foreign key to CheckResponse.request_id (tracing)
  - trust_index: Score from Stage 4 (0-1, 0=risky, 1=safe)
  - decision: Final verdict (SAFE, FLAGGED, ABSTAIN)
  - created_at: Timestamp when check completed (UTC)
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Index

from api.kb.models import Base  # Reuse KB's Base declarative


class CheckLog(Base):
    """
    Analytics log for each hallucination detection check.

    Used by /check endpoint to record results for dashboard.
    Queried by /analytics/* endpoints.
    """
    __tablename__ = "check_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(255), nullable=False, unique=True, index=True)
    trust_index = Column(Float, nullable=False)  # 0-1
    decision = Column(String(50), nullable=False)  # SAFE, FLAGGED, ABSTAIN
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_created_at", "created_at"),
        Index("ix_decision", "decision"),
    )

    def __repr__(self):
        return (
            f"<CheckLog(request_id={self.request_id!r}, "
            f"trust_index={self.trust_index}, decision={self.decision})>"
        )
