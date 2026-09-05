"""
Ingest IT Act, 2000 (India) Statute Sections into the Knowledge Base.

Person B - API and SDK

Uses db.merge() for upsert behavior — safe to re-run without creating duplicates.
Keyed on (act_name, section_number) unique constraint.

Runnable as: python -m api.kb.ingest_statutes
"""

import sys

try:
    from api.kb.db import SessionLocal
    from api.kb.models import StatuteSection
except RuntimeError as e:
    print(f"\n{e}\n")
    sys.exit(1)


def ingest_sections(act_name: str, sections: list[dict]) -> int:
    """
    Ingest statute sections into the knowledge base.

    Args:
        act_name: Name of the act (e.g., "Information Technology Act, 2000")
        sections: List of dicts with keys:
            - "number": Section identifier (e.g., "43A", "66")
            - "text": Full section text
            - "status": Optional lifecycle status (default: "active")

    Returns:
        Number of sections inserted or updated.
    """
    session = SessionLocal()
    count = 0

    try:
        for section_dict in sections:
            section_number = section_dict.get("number")
            section_text = section_dict.get("text")
            status = section_dict.get("status", "active")

            if not section_number or not section_text:
                print(f"  ⚠ Skipping malformed section: {section_dict}")
                continue

            # Upsert using merge(): will insert or update based on unique constraint
            # First, try to find existing record
            existing = (
                session.query(StatuteSection)
                .filter(
                    StatuteSection.act_name == act_name,
                    StatuteSection.section_number == section_number,
                )
                .first()
            )

            if existing:
                # Update existing record
                existing.section_text = section_text
                existing.status = status
            else:
                # Create new record
                statute = StatuteSection(
                    act_name=act_name,
                    section_number=section_number,
                    section_text=section_text,
                    status=status,
                )
                session.add(statute)

            count += 1

        session.commit()
        return count

    except Exception as e:
        session.rollback()
        print(f"✗ Error during ingestion: {e}")
        raise
    finally:
        session.close()


# Placeholder data: Real IT Act, 2000 sections
# Note: These are simplified summaries; verify against official bare act before final deployment
IT_ACT_2000_SECTIONS = [
    {
        "number": "43A",
        "text": (
            "Compensation for failure to protect data. Where a person (including a "
            "body corporate) causes loss or damage by engaging in unfair or deceptive "
            "practice or knowingly placing reliance on false information, the person "
            "shall be liable to pay compensation. The compensation shall not be less "
            "than five hundred thousand rupees and may extend to ten crore rupees."
        ),
        "status": "active",
    },
    {
        "number": "66",
        "text": (
            "Computer-related offences / Hacking. Whoever, with intent to cause or "
            "knowing that he is likely to cause wrongful loss or damage to the public "
            "or any person, by entering any computer system or network without authority, "
            "or exceeding authorized access, or introducing any computer contaminant, "
            "shall be punished with imprisonment of not more than three years and also "
            "be liable to fine which may extend to five lakh rupees."
        ),
        "status": "active",
    },
    {
        "number": "66A",
        "text": (
            "Punishment for sending offensive messages through communication service. "
            "Whoever sends, by means of a computer resource or a communication device, "
            "any information that is grossly offensive or has menacing character; "
            "or knowingly sends false information for the purpose of causing annoyance, "
            "inconvenience, danger, obstruction, insult, injury, criminal intimidation, "
            "enmity, hatred, or ill will; shall be punished with imprisonment for a term "
            "which may extend to three years and also be liable to fine."
        ),
        "status": "struck_down",  # Struck down by Supreme Court in 2015
    },
    {
        "number": "69",
        "text": (
            "Power to intercept, monitor, or decrypt information. The Centre or a State "
            "Government or a Union Territory may, in the interest of sovereignty or "
            "integrity of India, defence of India, security of the State, or public "
            "order, by order, direct any agency of the Government to intercept, monitor, "
            "or decrypt any information transmitted, received, or stored in any computer "
            "resource. No such direction shall be given except by an officer not below "
            "the rank of Secretary to the Government."
        ),
        "status": "active",
    },
    {
        "number": "79",
        "text": (
            "Exemption from liability of intermediaries in certain cases / Safe Harbor. "
            "An intermediary shall not be liable for any third party information, data, "
            "or communication link made available or hosted by the intermediary if: "
            "(1) the intermediary does not have actual knowledge that such information "
            "is illegal; (2) upon obtaining such knowledge, the intermediary acts "
            "expeditiously to disable access to such information; (3) the intermediary "
            "provides information, facilities, or assistance when required by any court, "
            "lawful authority, or in the interest of national security."
        ),
        "status": "active",
    },
]


def main():
    """Ingest placeholder IT Act, 2000 sections."""
    print("\n" + "=" * 70)
    print("Ingesting IT Act, 2000 Statute Sections")
    print("=" * 70 + "\n")

    act_name = "Information Technology Act, 2000"
    print(f"Act: {act_name}")
    print(f"Sections: {len(IT_ACT_2000_SECTIONS)}\n")

    try:
        count = ingest_sections(act_name, IT_ACT_2000_SECTIONS)
        print(f"\n✓ Successfully ingested/updated {count} sections")

        # Verify by querying the database
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

            print("\nDatabase verification:")
            print(f"  • Total sections in DB: {total}")
            print(f"  • Active sections: {active}")
            print(f"  • Struck down sections: {struck_down}")

            # List sections
            print("\nSections:")
            sections = (
                session.query(StatuteSection)
                .filter(StatuteSection.act_name == act_name)
                .order_by(StatuteSection.section_number)
                .all()
            )
            for section in sections:
                status_label = f" [{section.status}]" if section.status != "active" else ""
                print(f"  • Section {section.section_number}{status_label}")

        finally:
            session.close()

        print("\n" + "=" * 70 + "\n")
        return True

    except Exception as e:
        print(f"\n✗ Ingestion failed: {e}\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
