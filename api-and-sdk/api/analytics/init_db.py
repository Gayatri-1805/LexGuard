"""
Initialize analytics database schema.

Creates the check_logs table if it doesn't exist.
Runnable as: python -m api.analytics.init_db
"""

from api.kb.db import engine
from api.analytics.models import Base


def init_db():
    """Create all analytics tables."""
    print("Creating analytics tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized")


if __name__ == "__main__":
    init_db()
