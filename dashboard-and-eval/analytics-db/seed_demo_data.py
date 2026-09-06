"""
Demo data seeder for the analytics dashboard.

Seeds ~200 CheckLog rows spanning the last 30 days into the Neon PostgreSQL DB
so the dashboard has realistic data to display without needing the live pipeline.

Trust index distribution:
  - SAFE:    trust_index ~ Beta(8, 2) → skewed toward 1.0  (~70% of checks)
  - FLAGGED: trust_index ~ Beta(2, 8) → skewed toward 0.0  (~20% of checks)
  - ABSTAIN: trust_index ~ Uniform(0.35, 0.55)             (~10% of checks)

Usage:
    cd dashboard-and-eval
    pip install -r requirements.txt
    python analytics-db/seed_demo_data.py
    python analytics-db/seed_demo_data.py --rows 500  # more rows
    python analytics-db/seed_demo_data.py --clear      # wipe + reseed
"""

import argparse
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

# Allow running from repo root or dashboard-and-eval/
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Base, CheckLog, SessionLocal, engine  # noqa: E402


def _beta_sample(alpha: float, beta: float, low: float = 0.0, high: float = 1.0) -> float:
    """Sample from a beta distribution clipped to [low, high]."""
    val = np.random.beta(alpha, beta)
    return float(np.clip(val, low, high))


def _generate_rows(n: int) -> list[CheckLog]:
    """Generate n realistic CheckLog rows across the last 30 days."""
    now = datetime.now(timezone.utc)
    rows: list[CheckLog] = []

    for _ in range(n):
        # Random timestamp across last 30 days, weighted toward recent
        days_ago = random.betavariate(1.5, 5) * 30  # more recent checks are denser
        created_at = now - timedelta(days=days_ago, seconds=random.randint(0, 86400))

        # Decision distribution: 70% SAFE, 20% FLAGGED, 10% ABSTAIN
        roll = random.random()
        if roll < 0.70:
            decision = "SAFE"
            trust_index = _beta_sample(8, 2, low=0.60, high=1.0)
        elif roll < 0.90:
            decision = "FLAGGED"
            trust_index = _beta_sample(2, 8, low=0.0, high=0.45)
        else:
            decision = "ABSTAIN"
            trust_index = random.uniform(0.35, 0.55)

        rows.append(
            CheckLog(
                request_id=f"req-{uuid.uuid4()}",
                trust_index=round(trust_index, 4),
                decision=decision,
                created_at=created_at,
            )
        )

    return rows


def seed(n_rows: int = 200, clear_first: bool = False) -> None:
    """Seed the check_logs table with demo data."""
    # Ensure table exists
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        if clear_first:
            deleted = session.query(CheckLog).delete()
            session.commit()
            print(f"[clear] Cleared {deleted} existing rows.")

        existing = session.query(CheckLog).count()
        print(f"[info] Existing rows: {existing}")

        rows = _generate_rows(n_rows)
        session.bulk_save_objects(rows)
        session.commit()

        total = session.query(CheckLog).count()
        safe = session.query(CheckLog).filter(CheckLog.decision == "SAFE").count()
        flagged = session.query(CheckLog).filter(CheckLog.decision == "FLAGGED").count()
        abstain = session.query(CheckLog).filter(CheckLog.decision == "ABSTAIN").count()

        print(f"[done] Seeded {n_rows} rows -> total={total}  (SAFE={safe}, FLAGGED={flagged}, ABSTAIN={abstain})")
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed analytics demo data")
    parser.add_argument("--rows", type=int, default=200, help="Number of rows to insert (default: 200)")
    parser.add_argument("--clear", action="store_true", help="Clear existing rows before seeding")
    args = parser.parse_args()

    seed(n_rows=args.rows, clear_first=args.clear)
