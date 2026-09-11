"""
Stage 2: KB Lookup
==================
Grounds a single Claim against the FAISS-backed legal knowledge base
by calling VectorRetriever.retrieve_with_metadata() — the richer variant
that returns scores alongside passage text and source metadata.

Public API
----------
    kb_lookup(claim, top_k=3, threshold=KB_HIT_THRESHOLD) -> KBLookupResult

KBLookupResult
--------------
A small Pydantic model (defined here) containing:
    hit          – True if best_score >= threshold
    passages     – top_k results regardless of hit/miss (near-misses visible for debugging)
    best_score   – cosine similarity of the top result (0.0 if no results)

Threshold constant
------------------
KB_HIT_THRESHOLD is defined at module level with an explicit comment.
Tune it against the gold evaluation set — do NOT embed a magic number inline.

Logging
-------
Uses the same pattern as api/routes/analytics.py and api/routes/check.py:
    logger = logging.getLogger(__name__)
    logger.info(...)
No custom handlers, no DB writes — plain structured log line per lookup.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ── resolve project root so shared/ is importable regardless of cwd ──────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_API_ROOT = _PROJECT_ROOT / "api-and-sdk"
for _p in (_PROJECT_ROOT, _API_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from shared.schemas import Claim  # noqa: E402

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Module-level cache for vector retriever to avoid reloading FAISS index
_cached_retriever = None

# ─────────────────────────────────────────────────────────────────────────────
# Hit threshold — tune this against the gold evaluation set.
# A cosine similarity score of 1.0 = identical vectors; 0.0 = orthogonal.
# Current default based on all-MiniLM-L6-v2 geometry; re-calibrate after
# running eval/scoring.py on the annotated gold set.
# ─────────────────────────────────────────────────────────────────────────────
KB_HIT_THRESHOLD: float = 0.45


# ─────────────────────────────────────────────────────────────────────────────
# Result model
# ─────────────────────────────────────────────────────────────────────────────
class KBPassage(BaseModel):
    """A single retrieved KB passage with its score and provenance."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(..., description="Full text of the retrieved statute section or case holding.")
    source: str = Field(
        ...,
        description="Human-readable provenance string, e.g. "
                    "'statute:43A' or 'case:K.S. Puttaswamy v. Union of India'.",
    )
    score: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Cosine similarity between the claim embedding and this passage (0–1).",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw metadata dict from the FAISS index (source_type, ref_id, act_name, etc.).",
    )


class KBLookupResult(BaseModel):
    """Result of a single KB grounding lookup for one Claim."""

    model_config = ConfigDict(frozen=True)

    hit: bool = Field(
        ...,
        description="True if best_score >= KB_HIT_THRESHOLD — i.e., the KB contains "
                    "sufficiently relevant evidence to ground this claim.",
    )
    passages: list[KBPassage] = Field(
        ...,
        description="Top-k retrieved passages, always returned regardless of hit/miss. "
                    "Near-misses are preserved here for debugging and logging by downstream stages.",
    )
    best_score: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Cosine similarity of the top-ranked passage. 0.0 if the KB returned no results.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Source string builder
# ─────────────────────────────────────────────────────────────────────────────
def _build_source(meta: dict[str, Any]) -> str:
    """Construct a human-readable source label from a FAISS metadata dict.

    The metadata schema comes from build_index.py / fetch_indexable_rows():

    Statute rows have:  source_type, ref_id, section_number, act_name, status
    Case law rows have: source_type, ref_id, case_name, citation, related_section

    Returns a string like 'statute:43A' or 'case:K.S. Puttaswamy v. UoI'.
    Falls back to 'unknown' if neither shape is recognised.
    """
    source_type = meta.get("source_type", "unknown")
    if source_type == "statute":
        section = meta.get("section_number") or meta.get("ref_id", "?")
        return f"statute:{section}"
    if source_type == "case":
        name = meta.get("case_name") or meta.get("citation") or meta.get("ref_id", "?")
        return f"case:{name}"
    return f"{source_type}:{meta.get('ref_id', 'unknown')}"


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def kb_lookup(
    claim: Claim,
    top_k: int = 5,  # Increased from 3 to 5 for better coverage
    threshold: float = KB_HIT_THRESHOLD,
    *,
    retriever: Any = None,
) -> KBLookupResult:
    """Ground *claim* against the legal knowledge base.

    Uses a hybrid approach:
    1. If claim references a specific section (e.g., "Section 66"), try exact lookup first
    2. Fall back to semantic vector search for all claims

    Args:
        claim:      The Claim to ground (from shared/schemas.py).
        top_k:      Number of passages to retrieve (default: 3).
        threshold:  Cosine similarity cutoff for hit=True (default: KB_HIT_THRESHOLD).
                    Override in tests or calibration runs without touching the constant.
        retriever:  Pre-built VectorRetriever instance. If None, one is constructed
                    from the default FAISS index path. Inject a mock in tests.

    Returns:
        KBLookupResult with hit, passages (always top_k), and best_score.

    Raises:
        FileNotFoundError: If no retriever is injected and the FAISS index has
                           not been built yet (run python -m api.kb.build_index).
        ImportError:       If faiss-cpu or sentence-transformers are not installed.
    """
    # Use a module-level cached retriever to avoid reloading FAISS index
    global _cached_retriever
    if retriever is None:
        if '_cached_retriever' not in globals() or _cached_retriever is None:
            from api.kb.vector_kb import VectorRetriever
            _cached_retriever = VectorRetriever()
            logger.info("kb_lookup | initialized cached vector retriever")
        retriever = _cached_retriever

    # Try exact section lookup first if claim has a section reference
    exact_match_passages = []
    
    # Enhanced section detection - check both citation and claim text
    section_patterns = [
        r'(?:section|sec\.?)\s*(\d+[A-Za-z]?)',  # "Section 66", "Sec 43A", "Section 10A"
        r'(\d+[A-Za-z]?)\s*(?:of\s+(?:the\s+)?(?:information\s+technology|IT)\s+act)',  # "66 of IT Act"
    ]
    
    section_num = None
    search_text = f"{claim.citation or ''} {claim.text}"  # Keep original case
    
    for pattern in section_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            section_num = match.group(1).upper()  # Normalize to uppercase for DB lookup
            break
    
    if section_num:
        try:
            from api.kb.postgres_kb import PostgresKB
            
            logger.info("kb_lookup | attempting exact lookup for section=%s", section_num)
            postgres_kb = PostgresKB()
            section_text = postgres_kb.lookup_section(section_num, "Information Technology Act, 2000")
            
            if section_text and len(section_text.strip()) > 50:  # Ensure we got real content
                # Found exact section - add as a high-confidence passage
                exact_match_passages.append(
                    KBPassage(
                        text=section_text,
                        source=f"statute:{section_num}",
                        score=0.95,  # High score for exact match
                        metadata={"source_type": "statute", "section_number": section_num, "match_type": "exact"}
                    )
                )
                logger.info(
                    "kb_lookup | claim_id=%s | exact_match=SUCCESS | section=%s | text_length=%d",
                    claim.id,
                    section_num,
                    len(section_text)
                )
            else:
                logger.warning("kb_lookup | claim_id=%s | exact_match=FAILED | section=%s | no_content", claim.id, section_num)
                
        except Exception as e:
            logger.error("kb_lookup | claim_id=%s | exact_lookup_error: %s", claim.id, e)

    # Enhanced semantic search with multiple strategies
    all_results = []
    search_strategies = [
        claim.text,  # Original claim text
        claim.citation if claim.citation else claim.text,  # Citation if available
        f"Section {section_num}" if section_num else claim.text,  # Section-focused
    ]
    
    # Try multiple search strategies and combine results
    seen_texts = set()
    for strategy_query in search_strategies[:2]:  # Use top 2 strategies
        try:
            strategy_results = retriever.retrieve_with_metadata(strategy_query, top_k=3)
            for result in strategy_results:
                result_text = result.get('text', '')[:100]  # First 100 chars for dedup
                if result_text not in seen_texts:
                    all_results.append(result)
                    seen_texts.add(result_text)
        except Exception as e:
            logger.warning("kb_lookup | search strategy failed: %s", e)
    
    # Take top results across all strategies
    raw_results = all_results[:top_k]

    # Build KBPassage list from semantic search
    semantic_passages: list[KBPassage] = []
    for item in raw_results:
        score = float(item.get("score", 0.0))
        # Clamp to [0, 1] — FAISS inner-product on normalised vectors should
        # already be in this range, but guard against floating-point edge cases.
        score = max(0.0, min(1.0, score))
        meta = {k: v for k, v in item.items() if k != "text"}
        meta["match_type"] = "semantic"
        semantic_passages.append(
            KBPassage(
                text=str(item.get("text", "")),
                source=_build_source(item),
                score=score,
                metadata=meta,
            )
        )

    # Combine exact matches (if any) with semantic matches
    passages = exact_match_passages + semantic_passages
    
    # Limit to top_k total
    passages = passages[:top_k]

    best_score: float = passages[0].score if passages else 0.0
    hit: bool = best_score >= threshold

    # Structured log line — same pattern as api/routes/analytics.py and check.py
    logger.info(
        "kb_lookup | claim_id=%s | top_score=%.4f | threshold=%.4f | hit=%s | "
        "exact_matches=%d | claim_text=%.80r",
        claim.id,
        best_score,
        threshold,
        hit,
        len(exact_match_passages),
        claim.text,
    )

    return KBLookupResult(hit=hit, passages=passages, best_score=best_score)
