"""
Initialize the legal knowledge base schema on Neon (serverless Postgres).

Creates statute_sections and case_law tables if they don't exist.
Runnable as: python -m api.kb.init_db

Safe to run multiple times; idempotent via SQLAlchemy's create_all().
Catches connection errors and provides clear guidance on DATABASE_URL configuration.
"""

import sys
from sqlalchemy import text

try:
    from api.kb.db import engine
    from api.kb.models import Base, StatuteSection, CaseLaw
except RuntimeError as e:
    print(f"\n{e}\n")
    sys.exit(1)


def init_db():
    """Create all tables defined in models.Base."""
    print("\n" + "=" * 70)
    print("Initializing IT Act, 2000 Knowledge Base on Neon")
    print("=" * 70)
    print(f"\nConnecting to database...")

    try:
        # Test connection by executing a simple query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            if result:
                print("✓ Connection successful")

        print("\nCreating schema...")
        Base.metadata.create_all(engine)

        print("\n✓ Database schema created successfully!")
        print("\nTables created:")
        for table_name in Base.metadata.tables.keys():
            print(f"  • {table_name}")

        print("\n" + "=" * 70)
        print("Next steps:")
        print("=" * 70)
        print("1. Ingest IT Act sections:")
        print("   python -m api.kb.ingest_statutes")
        print("\n2. Ingest case law:")
        print("   python -m api.kb.ingest_case_law")
        print("\n" + "=" * 70 + "\n")

        return True

    except Exception as e:
        print(f"\n✗ Connection error: {type(e).__name__}")
        print(f"\nDetails: {str(e)}\n")
        print("Troubleshooting:")
        print("  • Check that DATABASE_URL is set in .env")
        print("  • Verify the connection string is correct (format: postgresql://user:password@host/db?sslmode=require)")
        print("  • Ensure your Neon project allows connections from your IP")
        print("  • Check network connectivity to the Neon endpoint\n")
        return False


if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
