"""
Migration script: Add is_verified and entry_type columns to case_law table.

Labels the 4 fabricated/incorrect cases as test data.
Fixes Puttaswamy's citation.

Runnable as: python -m api.kb.migrate_add_verification
"""

import sys
from sqlalchemy import text

try:
    from api.kb.db import engine, SessionLocal
    from api.kb.models import CaseLaw
except RuntimeError as e:
    print(f"\n{e}\n")
    sys.exit(1)


def migrate():
    """Add verification columns and label fabricated cases."""
    print("\n" + "=" * 70)
    print("Migration: Add Verification Columns to case_law")
    print("=" * 70)

    session = SessionLocal()

    try:
        # Step 1: Add columns (if they don't exist)
        print("\n[1/3] Adding is_verified and entry_type columns...")
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE case_law ADD COLUMN is_verified BOOLEAN DEFAULT true"))
                conn.commit()
                print("  ✓ Added is_verified column")
            except Exception as e:
                if "already exists" in str(e):
                    print("  ℹ is_verified column already exists")
                else:
                    print(f"  ⚠ Error adding is_verified: {e}")

            try:
                conn.execute(text("ALTER TABLE case_law ADD COLUMN entry_type TEXT DEFAULT 'real'"))
                conn.commit()
                print("  ✓ Added entry_type column")
            except Exception as e:
                if "already exists" in str(e):
                    print("  ℹ entry_type column already exists")
                else:
                    print(f"  ⚠ Error adding entry_type: {e}")

        # Step 2: Mark fabricated cases
        print("\n[2/3] Marking fabricated/incorrect test cases...")
        fabricated_cases = [
            {
                "case_name": "Wireless Telegraphy v. The State",
                "reason": "Case does not exist (conflation of statute name)"
            },
            {
                "case_name": "Ravi Shankar Prasad v. Union of India",
                "reason": "Case does not exist (fabricated citation)"
            },
            {
                "case_name": "R v. Anupam Verma",
                "reason": "Wrong jurisdiction format (India uses State v., not R v. since 1950)"
            },
            {
                "case_name": "Microsoft Ireland Operations Limited v. Union of India",
                "reason": "Generic fabricated case (no such landmark decision with this citation)"
            }
        ]

        for fab_case in fabricated_cases:
            case = (
                session.query(CaseLaw)
                .filter(CaseLaw.case_name == fab_case["case_name"])
                .first()
            )
            if case:
                case.is_verified = False
                case.entry_type = 'fabricated_test_case'
                print(f"  ✓ {fab_case['case_name']}")
                print(f"    Reason: {fab_case['reason']}")

        session.commit()

        # Step 3: Fix Puttaswamy citation
        print("\n[3/3] Fixing Puttaswamy citation...")
        puttaswamy = (
            session.query(CaseLaw)
            .filter(CaseLaw.case_name.like("K.S. Puttaswamy%"))
            .first()
        )
        if puttaswamy:
            old_citation = puttaswamy.citation
            puttaswamy.citation = "(2017) 10 SCC 1"
            puttaswamy.is_verified = True
            puttaswamy.entry_type = 'real'
            session.commit()
            print(f"  ✓ Updated Puttaswamy citation:")
            print(f"    Old: {old_citation}")
            print(f"    New: (2017) 10 SCC 1")
            print(f"    Status: is_verified=true, entry_type='real'")

        # Step 4: Summary
        print("\n" + "=" * 70)
        print("Verification Status Summary")
        print("=" * 70)
        all_cases = session.query(CaseLaw).all()
        verified = sum(1 for c in all_cases if c.is_verified)
        fabricated = sum(1 for c in all_cases if not c.is_verified)
        
        print(f"\nTotal cases: {len(all_cases)}")
        print(f"  ✓ Verified (is_verified=true): {verified}")
        print(f"  ℹ Fabricated test cases (is_verified=false): {fabricated}")

        print("\nFabricated cases (for evaluation testing only):")
        for case in all_cases:
            if not case.is_verified:
                print(f"  • {case.case_name} [{case.entry_type}]")

        print("\n" + "=" * 70)
        print("✓ Migration Complete")
        print("=" * 70)
        print("\nUsage in Stage 2 (Ground):")
        print("  kb.lookup_case_law(section_ref, verified_only=True)  # Only verified cases")
        print("  kb.lookup_case_law(section_ref, verified_only=False) # All cases (eval only)")
        print("\n" + "=" * 70 + "\n")

        return True

    except Exception as e:
        session.rollback()
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
