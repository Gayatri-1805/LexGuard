"""
SQLAlchemy ORM models for the legal knowledge base.

Models:
  - StatuteSection: parsed statute sections from IT Act, 2000 (all from official source, always verified)
  - CaseLaw: case law references related to IT Act sections (may include fabricated test cases)

Both inherit from Base (declarative_base) for easy schema creation.
"""

from sqlalchemy import Column, Integer, String, Text, UniqueConstraint, Index, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class StatuteSection(Base):
    """
    A section of the Information Technology Act, 2000 (India).

    Used by Stage 2 (Ground) to retrieve exact-match statute text for grounding claims.
    
    All sections are sourced from official PDFs, so verification is implicit.
    
    Columns:
      - id: Primary key (auto-increment)
      - act_name: Name of the act (e.g., "Information Technology Act, 2000")
      - section_number: Section identifier (e.g., "43A", "66", "66A", "69", "79")
      - section_text: The full text of the section
      - status: Lifecycle status ("active", "struck_down", "amended", default "active")
    """
    __tablename__ = "statute_sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    act_name = Column(String(255), nullable=False)
    section_number = Column(String(50), nullable=False)
    section_text = Column(Text, nullable=False)
    status = Column(String(50), nullable=True, default="active")

    # Unique constraint: no duplicate (act_name, section_number) pairs
    __table_args__ = (
        UniqueConstraint("act_name", "section_number", name="uq_act_section"),
        Index("ix_act_section", "act_name", "section_number"),
    )

    def __repr__(self):
        return (
            f"<StatuteSection(act_name={self.act_name!r}, "
            f"section_number={self.section_number!r}, status={self.status!r})>"
        )


class CaseLaw(Base):
    """
    A case law reference or court decision related to IT Act sections.

    Used by Stage 2 (Ground) to retrieve case holdings for comparison/grounding.
    
    CRITICAL: is_verified and entry_type columns distinguish real cases from fabricated test cases.
    Only is_verified=true rows should be surfaced as evidence for Stage 2 verdicts.
    Fabricated rows (is_verified=false, entry_type='fabricated_test_case') are for evaluation only.
    
    Columns:
      - id: Primary key (auto-increment)
      - case_name: Name of the case (e.g., "Shreya Singhal v. Union of India")
      - citation: Official citation (e.g., "(2015) 5 SCC 1"), nullable
      - holding_summary: Brief summary of the holding or key legal principle
      - full_text: Optional full text of the decision
      - related_section: Optional section reference (e.g., "66A") for linking cases to statute sections
      - is_verified: Boolean flag - true if case is verified to exist in real law; false if fabricated/uncertain
      - entry_type: 'real' (verified case law) | 'fabricated_test_case' (for evaluation testing)
    """
    __tablename__ = "case_law"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_name = Column(String(255), nullable=False)
    citation = Column(String(100), nullable=True)
    holding_summary = Column(Text, nullable=False)
    full_text = Column(Text, nullable=True)
    related_section = Column(String(50), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=True)
    entry_type = Column(String(50), nullable=False, default='real')  # 'real' | 'fabricated_test_case'

    def __repr__(self):
        return (
            f"<CaseLaw(case_name={self.case_name!r}, "
            f"citation={self.citation!r}, related_section={self.related_section!r}, "
            f"is_verified={self.is_verified}, entry_type={self.entry_type!r})>"
        )

