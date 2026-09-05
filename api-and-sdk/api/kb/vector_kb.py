"""
Vector-based retrieval for KB (semantic search fallback).

Uses FAISS index built by build_index.py.
Implements the retrieve() method for Stage 2 (Ground) when exact lookup fails.

Only returns is_verified=true results.
"""

import sys
import json
from pathlib import Path

try:
    import faiss
    import numpy as np
except ImportError:
    raise ImportError("faiss-cpu and numpy required. Run: pip install faiss-cpu numpy")

from api.kb.embeddings import embed_query
from api.kb.kb_interface import KnowledgeBase


class VectorRetriever(KnowledgeBase):
    """
    Vector-based semantic search over KB using FAISS.

    Implements retrieve() for fallback search when exact section lookup doesn't match.
    """

    def __init__(self, index_dir: str = None):
        """
        Initialize the vector retriever.

        Args:
            index_dir: Path to directory containing it_act.faiss and it_act_metadata.json
                      (default: api/kb/index relative to this file)

        Raises:
            FileNotFoundError: If index files don't exist
            RuntimeError: If DATABASE_URL not set
        """
        if index_dir is None:
            index_dir = Path(__file__).parent / "index"
        else:
            index_dir = Path(index_dir)

        self.index_dir = index_dir
        self.index_path = index_dir / "it_act.faiss"
        self.metadata_path = index_dir / "it_act_metadata.json"

        # Load index and metadata
        if not self.index_path.exists() or not self.metadata_path.exists():
            raise FileNotFoundError(
                f"\n✗ Index files not found at {index_dir}\n"
                f"Run this first to build the index:\n"
                f"  python -m api.kb.build_index\n"
                f"This will create:\n"
                f"  - {self.index_path}\n"
                f"  - {self.metadata_path}\n"
            )

        print(f"Loading FAISS index from {self.index_path}...")
        self.index = faiss.read_index(str(self.index_path))

        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        print(f"✓ Loaded index with {self.index.ntotal} vectors")
        print(f"✓ Loaded {len(self.metadata)} metadata entries")

    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        """
        Retrieve top-k most relevant KB chunks for a query via semantic search.

        Args:
            query: Query text (e.g., "data breach compensation")
            top_k: Number of top results to return (default: 5)

        Returns:
            List of strings (chunk texts) ranked by relevance, highest first.
            Only includes is_verified=true chunks.
        """
        if not query or not query.strip():
            return []

        # Embed query
        query_embedding = embed_query(query)
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)

        # Search FAISS index
        distances, indices = self.index.search(query_embedding, top_k)

        # Extract results with scores
        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.metadata):
                result_dict = self.metadata[int(idx)].copy()
                result_dict["score"] = float(distances[0][i])
                results.append(result_dict)

        # Return just the text strings (matching kb_interface.py return type: list[str])
        return [result["text"] for result in results]

    def retrieve_with_metadata(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Retrieve with full metadata and scores (useful for debugging/evaluation).

        Args:
            query: Query text
            top_k: Number of top results

        Returns:
            List of dicts with text, score, source_type, ref_id, etc.
        """
        if not query or not query.strip():
            return []

        query_embedding = embed_query(query)
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)

        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.metadata):
                result_dict = self.metadata[int(idx)].copy()
                result_dict["score"] = float(distances[0][i])
                results.append(result_dict)

        return results

    def lookup_section(self, section_ref: str, act_name: str) -> str | None:
        """
        VectorRetriever does not implement exact section lookup.
        Use PostgresKB.lookup_section() instead.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError(
            "VectorRetriever does not implement exact section lookup. "
            "Use PostgresKB.lookup_section() for exact matches, or "
            "VectorRetriever.retrieve() for semantic search."
        )
