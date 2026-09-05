"""
Database connection and session management for Neon (serverless Postgres).

Loads DATABASE_URL from .env via python-dotenv.
Provides SessionLocal for SQLAlchemy ORM operations and a FastAPI-style get_db() generator.

Raises RuntimeError at import time if DATABASE_URL is missing or empty.
"""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Load environment variables from .env file
load_dotenv()

# Get DATABASE_URL from environment
# Expected format: postgresql://user:password@ep-xxx.neon.tech/dbname?sslmode=require
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    raise RuntimeError(
        "\n"
        "❌ DATABASE_URL environment variable is missing or empty.\n"
        "Please fill in your Neon Postgres connection string in the .env file:\n"
        "\n"
        "  DATABASE_URL=postgresql://user:password@ep-xxx.neon.tech/dbname?sslmode=require\n"
        "\n"
        "Then try again."
    )

# Create SQLAlchemy engine with connection pooling
# For Neon (serverless), use NullPool to avoid connection exhaustion
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging during development
    poolclass=None,  # Neon recommendation: avoid persistent connections
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Usage in a route:
        @app.get("/")
        def some_route(db: Session = Depends(get_db)):
            ...

    Yields a SQLAlchemy session and ensures it's closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
