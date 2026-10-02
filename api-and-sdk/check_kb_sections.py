import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.kb.postgres_kb import PostgresKB
from api.kb.db import SessionLocal
from api.kb.models import StatuteSection

print("🔍 Checking KB sections...")

# Check database directly
session = SessionLocal()
try:
    # Count total sections
    total = session.query(StatuteSection).filter(
        StatuteSection.act_name == "Information Technology Act, 2000"
    ).count()
    
    print(f"\n✅ Total sections in KB: {total}")
    
    if total > 0:
        # Get all section numbers
        sections = session.query(StatuteSection.section_number).filter(
            StatuteSection.act_name == "Information Technology Act, 2000"
        ).order_by(StatuteSection.section_number).all()
        
        section_nums = [s[0] for s in sections]
        print(f"   Range: Section {section_nums[0]} to Section {section_nums[-1]}")
        print(f"\n📋 All sections: {section_nums[:20]}...")  # Show first 20
        
        # Test exact lookup for Section 66
        kb = PostgresKB()
        section_66 = kb.lookup_section("66", "Information Technology Act, 2000")
        if section_66:
            print(f"\n✅ Section 66 lookup SUCCESS: {len(section_66)} chars")
            print(f"   Preview: {section_66[:150]}...")
        else:
            print("\n❌ Section 66 lookup FAILED")
            
        # Test Section 66A
        section_66a = kb.lookup_section("66A", "Information Technology Act, 2000")
        if section_66a:
            print(f"\n✅ Section 66A lookup SUCCESS: {len(section_66a)} chars")
        else:
            print("\n⚠️  Section 66A not found (expected if struck down)")
    else:
        print("\n❌ No sections found in database!")
        print("   Run: python api/kb/ingest_statutes.py")
        
finally:
    session.close()

