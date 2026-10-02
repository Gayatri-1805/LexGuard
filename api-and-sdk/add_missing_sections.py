"""
Add missing legitimate IT Act sections to the PostgreSQL KB.
Sections 70A, 72A, 84A are real but missing from the KB.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api.kb.db import SessionLocal
from api.kb.models import StatuteSection

# Missing sections from IT Act 2000 (confirmed real sections)
MISSING_SECTIONS = {
    "70A": """National nodal agency.—(1) The Central Government may, by notification published in the Official Gazette, designate any organization of the Government as the national nodal agency in respect of Critical Information Infrastructure Protection.
(2) The national nodal agency designated under sub-section (1) shall be responsible for all measures including Research and Development relating to protection of Critical Information Infrastructure.
(3) The manner of performing functions and duties of the agency referred to in sub-section (1) shall be such as may be prescribed.""",
    
    "72A": """Punishment for disclosure of information in breach of lawful contract.—Save as otherwise provided in this Act or any other law for the time being in force, any person including an intermediary who, while providing services under the terms of lawful contract, has secured access to any material containing personal information about another person, with the intent to cause or knowing that he is likely to cause wrongful loss or wrongful gain discloses, without the consent of the person concerned, or in breach of a lawful contract, such material to any other person, shall be punished with imprisonment for a term which may extend to three years, or with fine which may extend to five lakh rupees, or with both.""",
    
    "84A": """Punishment for abetment of offences.—Whoever abets any offence shall, if the act abetted is committed in consequence of the abetment, and no express provision is made by this Act for the punishment of such abetment, be punished with the punishment provided for the offence under this Act.
Explanation.—An act or offence is said to be committed in consequence of abetment, when it is committed in consequence of the instigation, or in pursuance of the conspiracy, or with the aid which constitutes the abetment.""",
}

def add_sections():
    session = SessionLocal()
    try:
        print("=" * 80)
        print("ADDING MISSING IT ACT SECTIONS TO KB")
        print("=" * 80)
        
        for section_num, section_text in MISSING_SECTIONS.items():
            # Check if already exists
            existing = session.query(StatuteSection).filter(
                StatuteSection.act_name == "Information Technology Act, 2000",
                StatuteSection.section_number == section_num
            ).first()
            
            if existing:
                print(f"\n⚠️  Section {section_num} already exists (updating text)")
                existing.section_text = section_text
            else:
                print(f"\n✅ Adding Section {section_num}")
                new_section = StatuteSection(
                    act_name="Information Technology Act, 2000",
                    section_number=section_num,
                    section_text=section_text,
                    status="active"  # All these are active sections
                )
                session.add(new_section)
            
            print(f"   Text length: {len(section_text)} chars")
            print(f"   Preview: {section_text[:100]}...")
        
        session.commit()
        print("\n" + "=" * 80)
        print("✅ SUCCESSFULLY ADDED/UPDATED SECTIONS")
        print("=" * 80)
        
        # Verify
        print("\n📊 Verification:")
        for section_num in MISSING_SECTIONS.keys():
            result = session.query(StatuteSection).filter(
                StatuteSection.act_name == "Information Technology Act, 2000",
                StatuteSection.section_number == section_num
            ).first()
            if result:
                print(f"✅ Section {section_num} - Confirmed in DB")
            else:
                print(f"❌ Section {section_num} - Still missing!")
                
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    add_sections()
