"""
PostgreSQL Knowledge Base Implementation

Person B - API and SDK

Implements KnowledgeBase interface using exact SQL queries against statute_sections
and case_law tables in Postgres/Neon, with fallback to vector retrieval.

lookup_section(): exact-match on (act_name, section_number) via SQLAlchemy ORM
retrieve(): delegates to VectorRetriever for semantic search fallback

CRITICAL: Only returns is_verified=true rows to avoid surfacing fabricated test cases as evidence.
"""

from api.kb.kb_interface import KnowledgeBase
from api.kb.db import SessionLocal
from api.kb.models import StatuteSection, CaseLaw

try:
    from api.kb.vector_kb import VectorRetriever
    _vector_retriever = None  # Lazy-loaded
except ImportError:
    _vector_retriever = None


class PostgresKB(KnowledgeBase):
    """
    Postgres-backed knowledge base with vector fallback.
    
    Used by Stage 2 (Ground) to retrieve statute text for grounding claims.
    - lookup_section(): exact match (primary path)
    - retrieve(): semantic search via FAISS (fallback path)
    Only surfaces verified case law (is_verified=true) as evidence.
    """

    def __init__(self, index_dir: str = None):
        """Initialize KB with optional vector index."""
        self.index_dir = index_dir
        self._vector_retriever = None

    def _get_vector_retriever(self):
        """Lazy-load vector retriever on first use."""
        if self._vector_retriever is None:
            try:
                self._vector_retriever = VectorRetriever(self.index_dir)
            except FileNotFoundError:
                raise FileNotFoundError(
                    "\nVector index not found. Build it first:\n"
                    "  python -m api.kb.build_index\n"
                )
        return self._vector_retriever

    def lookup_section(self, section_ref: str, act_name: str) -> str | None:
        """
        Retrieve the full text of a statute section by exact match.

        Args:
            section_ref: Section identifier (e.g., "66A", "43A")
            act_name: Name of the act (e.g., "Information Technology Act, 2000")

        Returns:
            Full section text if found, else None.
            All statute sections are verified (sourced from official PDFs).
        """
        session = SessionLocal()
        try:
            result = (
                session.query(StatuteSection)
                .filter(
                    StatuteSection.act_name == act_name,
                    StatuteSection.section_number == section_ref,
                )
                .first()
            )
            if result:
                return result.section_text
            return None
        finally:
            session.close()

    def lookup_case_law(self, section_ref: str, verified_only: bool = True) -> list[dict]:
        """
        Retrieve case law related to a statute section.

        Args:
            section_ref: Section identifier (e.g., "66A")
            verified_only: If True, only return is_verified=true cases (default: True for production)

        Returns:
            List of case dicts with name, citation, holding_summary, is_verified, entry_type
        """
        session = SessionLocal()
        try:
            query = (
                session.query(CaseLaw)
                .filter(CaseLaw.related_section == section_ref)
            )

            if verified_only:
                query = query.filter(CaseLaw.is_verified == True)

            cases = query.all()

            return [
                {
                    "case_name": case.case_name,
                    "citation": case.citation,
                    "holding_summary": case.holding_summary,
                    "related_section": case.related_section,
                    "is_verified": case.is_verified,
                    "entry_type": case.entry_type,
                }
                for case in cases
            ]
        finally:
            session.close()

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """
        Semantic/lexical search for relevant statute passages via FAISS vector index.

        Used by Stage 2 (Ground) when exact section lookup doesn't match.
        Returns top_k most relevant chunks ranked by relevance.

        Args:
            query: Natural language query (e.g., "data breach compensation")
            top_k: Number of results to return (default: 5)

        Returns:
            List of text chunks (statute section text or case holding_summary),
            ranked by relevance, highest first. Only verified rows included.
        """
        try:
            retriever = self._get_vector_retriever()
            return retriever.retrieve(query, top_k)
        except FileNotFoundError:
            raise
