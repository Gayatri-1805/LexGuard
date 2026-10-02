"""
Add more missing legitimate IT Act sections identified from test failures.
Section 3A (electronic signature) and verify Section 79 exists.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api.kb.db import SessionLocal
from api.kb.models import StatuteSection

# Additional missing sections
ADDITIONAL_SECTIONS = {
    "3A": """Electronic signature.—For the purposes of this Act, the expression "electronic signature" means authentication of any electronic record by a subscriber by means of an electronic technique specified in the Second Schedule and includes digital signature.""",
}

def add_sections():
    session = SessionLocal()
    try:
        print("=" * 80)
        print("ADDING ADDITIONAL MISSING SECTIONS")
        print("=" * 80)
        
        # Check Section 79 first
        sec79 = session.query(StatuteSection).filter(
            StatuteSection.act_name == "Information Technology Act, 2000",
            StatuteSection.section_number == "79"
        ).first()
        
        if sec79:
            print(f"\n✅ Section 79 already exists ({len(sec79.section_text)} chars)")
        else:
            print(f"\n❌ Section 79 is MISSING - need to add it")
            ADDITIONAL_SECTIONS["79"] = """Exemption from liability of intermediary in certain cases.—(1) Notwithstanding anything contained in any law for the time being in force but subject to the provisions of sub-sections (2) and (3), an intermediary shall not be liable for any third party information, data, or communication link made available or hosted by him."""
        
        # Add missing sections
        for section_num, section_text in ADDITIONAL_SECTIONS.items():
            existing = session.query(StatuteSection).filter(
                StatuteSection.act_name == "Information Technology Act, 2000",
                StatuteSection.section_number == section_num
            ).first()
            
            if existing:
                print(f"\n⚠️  Section {section_num} already exists (skipping)")
            else:
                print(f"\n✅ Adding Section {section_num}")
                new_section = StatuteSection(
                    act_name="Information Technology Act, 2000",
                    section_number=section_num,
                    section_text=section_text,
                    status="active"
                )
                session.add(new_section)
                print(f"   Text length: {len(section_text)} chars")
                print(f"   Preview: {section_text[:80]}...")
        
        session.commit()
        print("\n" + "=" * 80)
        print("✅ SUCCESSFULLY ADDED SECTIONS")
        print("=" * 80)
        
        # Verify
        print("\n📊 Verification:")
        for section_num in ADDITIONAL_SECTIONS.keys():
            result = session.query(StatuteSection).filter(
                StatuteSection.act_name == "Information Technology Act, 2000",
                StatuteSection.section_number == section_num
            ).first()
            if result:
                print(f"✅ Section {section_num} - Confirmed in DB")
            else:
                print(f"❌ Section {section_num} - Still missing!")
        
        # Show total section count
        total = session.query(StatuteSection).filter(
            StatuteSection.act_name == "Information Technology Act, 2000"
        ).count()
        print(f"\n📊 Total IT Act sections in KB: {total}")
                
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    add_sections()
