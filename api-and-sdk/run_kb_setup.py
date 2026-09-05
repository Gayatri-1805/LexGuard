#!/usr/bin/env python
"""
Quick KB setup runner - installs deps, initializes DB, ingests sample data
"""

import subprocess
import sys
import os

# Change to api-and-sdk directory
os.chdir(os.path.dirname(__file__))

print("=" * 70)
print("KB SETUP RUNNER")
print("=" * 70)

# Step 1: Install dependencies
print("\n[1/4] Installing dependencies...")
try:
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-q",
        "requests", "pdfplumber", "sqlalchemy", "psycopg2-binary", "python-dotenv"
    ])
    print("✓ Dependencies installed")
except Exception as e:
    print(f"✗ Dependency installation failed: {e}")
    sys.exit(1)

# Step 2: Initialize database
print("\n[2/4] Initializing database schema...")
try:
    from api.kb.init_db import init_db
    if init_db():
        print("✓ Database schema initialized")
    else:
        print("✗ Database initialization failed")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error during init_db: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Ingest sample statutes
print("\n[3/4] Ingesting sample IT Act sections...")
try:
    from api.kb.ingest_statutes import main as ingest_main
    if ingest_main():
        print("✓ Sample statutes ingested")
    else:
        print("✗ Statute ingestion failed")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error during statute ingestion: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Ingest sample cases
print("\n[4/4] Ingesting sample case law...")
try:
    from api.kb.ingest_case_law import main as cases_main
    if cases_main():
        print("✓ Sample case law ingested")
    else:
        print("✗ Case law ingestion failed")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error during case law ingestion: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Verification
print("\n" + "=" * 70)
print("VERIFICATION")
print("=" * 70)
try:
    from api.kb.postgres_kb import PostgresKB
    kb = PostgresKB()
    
    print("\nTesting PostgresKB lookups...")
    
    # Test Section 66A
    s66a_text = kb.lookup_section("66A", "Information Technology Act, 2000")
    if s66a_text:
        print(f"✓ Section 66A: {s66a_text[:80]}...")
    else:
        print("✗ Section 66A not found")
    
    # Test Section 66
    s66_text = kb.lookup_section("66", "Information Technology Act, 2000")
    if s66_text:
        print(f"✓ Section 66: {s66_text[:80]}...")
    else:
        print("✗ Section 66 not found")
    
    # Test non-existent
    s999 = kb.lookup_section("999", "Information Technology Act, 2000")
    if s999 is None:
        print(f"✓ Non-existent section (999) correctly returns None")
    
    print("\n" + "=" * 70)
    print("✓ KB SETUP COMPLETE")
    print("=" * 70)
    print("\nYour knowledge base is ready!")
    print("Tables created:")
    print("  • statute_sections (5 IT Act sections)")
    print("  • case_law (1 landmark case)")
    
except Exception as e:
    print(f"✗ Verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
