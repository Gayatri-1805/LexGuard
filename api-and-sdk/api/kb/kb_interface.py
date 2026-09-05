"""
Knowledge Base Interface (Abstract Base)

Person B - API and SDK
PRIORITY: Build this FIRST — it is the contract for Person A's Stage 2 (grounding).

Abstract base class defining the KB API that Stage 2 (Ground) depends on:
  - lookup_section(section_ref: str, act_name: str) -> str | None
    Used for exact-match citation checking against statute sections.
    Called when Stage 0 (Decompose) identifies a section reference (e.g., "Section 66A").
    Returns the full section text if found, else None.

  - retrieve(query: str, top_k: int = 5) -> list[str]
    Used for content/holding fallback search via semantic or BM25 methods.
    Called when exact lookup fails or for broader grounding.
    Implemented separately in vector_kb.py (raises NotImplementedError here).

Implementations:
  - postgres_kb.py: lookup_section() via exact SQL query; retrieve() raises NotImplementedError
  - vector_kb.py: retrieve() via Qdrant vector DB and BM25 (not part of this task)
"""

from abc import ABC, abstractmethod


class KnowledgeBase(ABC):
    """
    Abstract interface for legal knowledge base retrieval.
    
    Implementations must provide exact-match lookup (Stage 2: Ground)
    and semantic/BM25 retrieval for claim grounding.
    """

    @abstractmethod
    def lookup_section(self, section_ref: str, act_name: str) -> str | None:
        """
        Retrieve the full text of a statute section by exact match.

        Args:
            section_ref: Section identifier (e.g., "66A", "43A")
            act_name: Name of the act (e.g., "Information Technology Act, 2000")

        Returns:
            Full section text if found, else None.
            
        Used by Stage 2 (Ground) to verify claims against statute text.
        """
        pass

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """
        Retrieve relevant statute/case law passages via semantic or lexical search.

        Args:
            query: Natural language query or claim text to ground
            top_k: Number of top results to return

        Returns:
            List of retrieved passages/sections ranked by relevance.
            Empty list if no results found.
            
        Used by Stage 2 (Ground) as fallback when exact section lookup fails,
        or for general content-based grounding of holdings and legal principles.
        """
        pass

