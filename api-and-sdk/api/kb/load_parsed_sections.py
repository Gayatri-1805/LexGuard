"""
Load parsed IT Act, 2000 sections from JSON into the Postgres knowledge base.

This script reads the intermediate JSON file (created by scrape_it_act.py)
and calls the existing ingest_sections() function to insert into the
StatuteSection table.

Runnable as: python -m api.kb.load_parsed_sections
"""

import sys
import json
from pathlib import Path

try:
    from api.kb.ingest_statutes import ingest_sections
    from api.kb.db import SessionLocal
    from api.kb.models import StatuteSection
except RuntimeError as e:
    print(f"\n{e}\n")
    sys.exit(1)
except ImportError as e:
    print(f"\n✗ Import error: {e}\n")
    sys.exit(1)


KB_RAW_DIR = Path(__file__).parent / "kb_raw"
JSON_PATH = KB_RAW_DIR / "it_act_2000_parsed.json"


def load_sections_from_json(json_path: str) -> list[dict]:
    """
    Load parsed sections from JSON file.

    Args:
        json_path: Path to the JSON file

    Returns:
        List of section dicts with keys: number, text, status
    """
    print(f"\nLoading sections from: {json_path}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            sections = json.load(f)

        print(f"✓ Loaded {len(sections)} sections from JSON")
        return sections

    except FileNotFoundError:
        print(f"✗ File not found: {json_path}")
        print(f"\nRun scrape_it_act.py first to generate the JSON:")
        print(f"  python -m api.kb.scrape_it_act")
        return []
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")
        return []


def verify_sections(sections: list[dict]) -> bool:
    """
    Verify sections have required fields and expected structure.

    Args:
        sections: List of section dicts

    Returns:
        True if all sections are valid, False otherwise
    """
    print("\nVerifying section structure...")

    required_fields = ["number", "text"]
    optional_fields = ["status"]

    for idx, section in enumerate(sections):
        for field in required_fields:
            if field not in section:
                print(f"✗ Section {idx} missing required field: {field}")
                return False

        if "status" not in section:
            section["status"] = "active"

    print(f"✓ All {len(sections)} sections have required fields")
    return True


def main():
    """Load parsed sections into Postgres."""
    print("\n" + "=" * 70)
    print("Loading Parsed IT Act, 2000 Sections into Postgres KB")
    print("=" * 70)

    # Load JSON
    sections = load_sections_from_json(str(JSON_PATH))
    if not sections:
        print("\n✗ No sections loaded. Exiting.")
        return False

    # Verify structure
    if not verify_sections(sections):
        print("\n✗ Section verification failed. Exiting.")
        return False

    # Ingest into DB
    print("\n--- INGESTING INTO POSTGRES ---")
    act_name = "Information Technology Act, 2000"

    try:
        count = ingest_sections(act_name, sections)
        print(f"✓ Successfully ingested/updated {count} sections")

        # Database verification
        print("\n--- DATABASE VERIFICATION ---")
        session = SessionLocal()
        try:
            total = (
                session.query(StatuteSection)
                .filter(StatuteSection.act_name == act_name)
                .count()
            )
            active = (
                session.query(StatuteSection)
                .filter(
                    StatuteSection.act_name == act_name,
                    StatuteSection.status == "active",
                )
                .count()
            )
            struck_down = (
                session.query(StatuteSection)
                .filter(
                    StatuteSection.act_name == act_name,
                    StatuteSection.status == "struck_down",
                )
                .count()
            )
            omitted = (
                session.query(StatuteSection)
                .filter(
                    StatuteSection.act_name == act_name,
                    StatuteSection.status == "omitted",
                )
                .count()
            )

            print(f"\nDatabase counts:")
            print(f"  • Total sections: {total}")
            print(f"  • Active: {active}")
            print(f"  • Struck down: {struck_down}")
            print(f"  • Omitted: {omitted}")

            # Critical verification: Section 66A must be struck_down
            section_66a = (
                session.query(StatuteSection)
                .filter(
                    StatuteSection.act_name == act_name,
                    StatuteSection.section_number == "66A",
                )
                .first()
            )

            if section_66a:
                print(f"\n✓ Section 66A found:")
                print(f"  • Status: {section_66a.status}")
                if section_66a.status == "struck_down":
                    print(f"  • ✓ Correctly marked as struck_down")
                else:
                    print(f"  • ⚠ WARNING: Expected status='struck_down', got '{section_66a.status}'")
                    print(f"  • Text preview: {section_66a.section_text[:100]}...")
            else:
                print(f"\n⚠ Section 66A not found in database!")

            # Sample key sections
            print(f"\nKey sections in database:")
            key_sections = ["43A", "66", "66A", "69", "79"]
            for sec_num in key_sections:
                sec = (
                    session.query(StatuteSection)
                    .filter(
                        StatuteSection.act_name == act_name,
                        StatuteSection.section_number == sec_num,
                    )
                    .first()
                )
                if sec:
                    status_label = f" [{sec.status}]" if sec.status != "active" else ""
                    print(f"  • Section {sec_num}{status_label}: ✓")
                else:
                    print(f"  • Section {sec_num}: ✗ NOT FOUND")

        finally:
            session.close()

        print("\n" + "=" * 70)
        print("LOADING COMPLETE")
        print("=" * 70)

        if total >= 85:
            print(f"\n✓ Successfully loaded {total} sections into Postgres")
        else:
            print(f"\n⚠ WARNING: Only {total} sections loaded (expected ~85+)")
            print("  The scraper may have missed some sections.")
            print("  Please review the parsed JSON and/or regex pattern.")

        return True

    except Exception as e:
        print(f"\n✗ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
