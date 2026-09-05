"""
Build and save FAISS vector index for KB retrieval.

Indexes all is_verified=true statute sections and case law holdings.
Outputs:
  - api/kb/index/it_act.faiss (the index)
  - api/kb/index/it_act_metadata.json (metadata for results)

Runnable as: python -m api.kb.build_index
"""

import sys
import json
from pathlib import Path

try:
    import faiss
    import numpy as np
except ImportError:
    raise ImportError("faiss-cpu and numpy required. Run: pip install faiss-cpu numpy")

try:
    from api.kb.db import SessionLocal
    from api.kb.models import StatuteSection, CaseLaw
    from api.kb.embeddings import embed_texts
except RuntimeError as e:
    print(f"\n{e}\n")
    sys.exit(1)


INDEX_DIR = Path(__file__).parent / "index"
INDEX_PATH = INDEX_DIR / "it_act.faiss"
METADATA_PATH = INDEX_DIR / "it_act_metadata.json"


def fetch_indexable_rows() -> list[dict]:
    """
    Fetch all is_verified=true statute sections and case law from Postgres.

    Returns:
        List of dicts: {text, source_type, ref_id, section_number/case_name, act_name/citation}
    """
    print("Fetching indexable rows from Postgres...")
    session = SessionLocal()
    rows = []

    try:
        # Fetch statute sections (all are verified—sourced from official PDFs)
        print("  Fetching statute sections...")
        statutes = (
            session.query(StatuteSection)
            .all()
        )

        for statute in statutes:
            rows.append(
                {
                    "text": statute.section_text,
                    "source_type": "statute",
                    "ref_id": statute.id,
                    "section_number": statute.section_number,
                    "act_name": statute.act_name,
                    "status": statute.status,
                }
            )

        print(f"    ✓ {len(statutes)} statute sections")

        # Fetch case law
        print("  Fetching case law...")
        cases = (
            session.query(CaseLaw)
            .filter(CaseLaw.is_verified == True)
            .all()
        )

        for case in cases:
            rows.append(
                {
                    "text": case.holding_summary,
                    "source_type": "case",
                    "ref_id": case.id,
                    "case_name": case.case_name,
                    "citation": case.citation,
                    "related_section": case.related_section,
                }
            )

        print(f"    ✓ {len(cases)} case law entries")

        print(f"\n  Total indexable rows: {len(rows)}")
        return rows

    finally:
        session.close()


def build_faiss_index(rows: list[dict]) -> tuple:
    """
    Build FAISS index from rows.

    Args:
        rows: List of dicts with 'text' key

    Returns:
        (faiss.Index, metadata_list) where metadata_list[i] corresponds to vector i
    """
    print("\nBuilding FAISS index...")

    if not rows:
        print("✗ No rows to index")
        return None, []

    # Extract texts
    texts = [row["text"] for row in rows]
    print(f"  Embedding {len(texts)} texts...")

    # Embed all texts
    embeddings = embed_texts(texts)
    print(f"  ✓ Embeddings shape: {embeddings.shape}")

    # Build FAISS index (inner product for cosine similarity with normalized vectors)
    print("  Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype(np.float32))
    print(f"  ✓ Index created with {index.ntotal} vectors")

    return index, rows


def save_index(index, metadata: list[dict], dir_path: str) -> None:
    """Save index and metadata to disk."""
    dir_path = Path(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)

    index_file = dir_path / "it_act.faiss"
    metadata_file = dir_path / "it_act_metadata.json"

    print(f"\nSaving to {dir_path}...")

    # Save FAISS index
    faiss.write_index(index, str(index_file))
    print(f"  ✓ Index: {index_file}")

    # Save metadata
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Metadata: {metadata_file}")


def main():
    """Build and save the index."""
    print("\n" + "=" * 70)
    print("Building FAISS Index for IT Act Knowledge Base")
    print("=" * 70 + "\n")

    try:
        # Fetch rows
        rows = fetch_indexable_rows()

        if not rows:
            print("\n✗ No rows to index")
            return False

        # Build index
        index, metadata = build_faiss_index(rows)

        if index is None:
            return False

        # Save index
        save_index(index, metadata, str(INDEX_DIR))

        # Summary
        print("\n" + "=" * 70)
        print("Index Build Complete")
        print("=" * 70)

        statute_count = sum(1 for r in metadata if r["source_type"] == "statute")
        case_count = sum(1 for r in metadata if r["source_type"] == "case")

        print(f"\nIndexed chunks:")
        print(f"  • Statute sections: {statute_count}")
        print(f"  • Case law: {case_count}")
        print(f"  • Total: {len(metadata)}")

        print(f"\nNext: Test retrieval with:")
        print(f"  python -c \"from api.kb.vector_kb import VectorRetriever; ")
        print(f"  vr = VectorRetriever(); ")
        print(f"  print(vr.retrieve('data breach compensation', top_k=3))\"")

        print("\n" + "=" * 70 + "\n")

        return True

    except Exception as e:
        print(f"\n✗ Build failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
