"""
Check which sections are missing from the KB that caused test failures.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api.kb.postgres_kb import PostgresKB
from api.kb.db import SessionLocal
from api.kb.models import StatuteSection

print("=" * 80)
print("CHECKING MISSING SECTIONS FROM TEST FAILURES")
print("=" * 80)

# Sections that failed exact lookup during tests
failed_sections = ["70A", "3A", "72A", "84A", "66G", "68A", "71A", "44A", "75A", "82A", "66H"]

kb = PostgresKB()
session = SessionLocal()

try:
    print("\n📋 Checking sections...")
    
    for section_num in failed_sections:
        # Try exact lookup
        result = kb.lookup_section(section_num, "Information Technology Act, 2000")
        
        if result:
            print(f"✅ Section {section_num:4s} - FOUND ({len(result)} chars)")
        else:
            # Check if it exists with different formatting
            alt_results = session.query(StatuteSection).filter(
                StatuteSection.act_name == "Information Technology Act, 2000",
                StatuteSection.section_number.ilike(f"%{section_num}%")
            ).all()
            
            if alt_results:
                print(f"⚠️  Section {section_num:4s} - Found with different format:")
                for r in alt_results:
                    print(f"     → Stored as: '{r.section_number}'")
            else:
                print(f"❌ Section {section_num:4s} - MISSING (should be FLAGGED if claim references it)")
    
    # Summary
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print("""
Sections 70A, 3A, 72A, 84A:
  - These exist in IT Act 2000
  - If MISSING → need to be added to KB
  - If FOUND → check section number formatting in DB

Sections 66G, 68A, 71A, 44A, 75A, 82A, 66H:
  - These are HALLUCINATIONS (don't exist in IT Act)
  - Missing from KB is CORRECT
  - System should detect as FLAGGED
""")

finally:
    session.close()
