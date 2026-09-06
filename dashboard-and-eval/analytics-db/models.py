"""
SQLAlchemy ORM Models for Analytics DB — Person C

Provides:
  - CheckLog: mirrors Person B's check_logs table (same schema, same table name).
              Used here to query existing data for the dashboard and eval harness.
  - engine / SessionLocal: connect to the Neon PostgreSQL instance via DATABASE_URL.

Design decision: We do NOT define a second Base with duplicate table definitions.
Instead we declare our own engine + session that point at the same Neon DB so that
Person C can query `check_logs` independently (e.g., seed_demo_data.py, run_eval.py)
without importing Person B's internal modules.
"""

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# ── Load env ──────────────────────────────────────────────────────────────────
# Walk up to find .env (supports running from any sub-directory)
_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_HERE, "..", ".env"))
load_dotenv(os.path.join(_HERE, "..", "..", ".env"))  # repo root fallback

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Add it to dashboard-and-eval/.env or the repo root .env"
    )

# ── Engine & Session ──────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # detect stale connections (important for Neon serverless)
    pool_size=5,
    max_overflow=10,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ── ORM Base ──────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── CheckLog ──────────────────────────────────────────────────────────────────
class CheckLog(Base):
    """
    Analytics log for each hallucination detection check.

    Mirrors Person B's api/analytics/models.py:CheckLog (same table, same columns).
    Person C reads/seeds this table; Person B writes to it via the /check endpoint.

    Columns:
      id          — auto-increment primary key
      request_id  — unique trace ID from CheckResponse.request_id
      trust_index — Stage 4 aggregate score (0 = risky, 1 = safe)
      decision    — SAFE | FLAGGED | ABSTAIN
      created_at  — UTC timestamp of the check
    """

    __tablename__ = "check_logs"
    __table_args__ = (
        Index("ix_created_at", "created_at"),
        Index("ix_decision", "decision"),
        {"extend_existing": True},  # allow re-definition if Person B already created it
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(255), nullable=False, unique=True, index=True)
    trust_index = Column(Float, nullable=False)
    decision = Column(String(50), nullable=False)  # SAFE | FLAGGED | ABSTAIN
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<CheckLog(request_id={self.request_id!r}, "
            f"trust_index={self.trust_index:.3f}, decision={self.decision})>"
        )
