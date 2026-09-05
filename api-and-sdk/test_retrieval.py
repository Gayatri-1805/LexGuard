"""Quick test of vector retrieval."""

from api.kb.vector_kb import VectorRetriever

vr = VectorRetriever()
results = vr.retrieve_with_metadata('data breach compensation', top_k=3)

print("\n" + "="*70)
print("Vector Retrieval Test: 'data breach compensation'")
print("="*70 + "\n")

for i, result in enumerate(results, 1):
    print(f"{i}. Score: {result.get('score', 0):.4f}")
    print(f"   Type: {result.get('source_type', 'unknown')}")
    if result.get('source_type') == 'statute':
        print(f"   Section: {result.get('section_number', 'N/A')}")
        print(f"   Act: {result.get('act_name', 'N/A')}")
    else:
        print(f"   Case: {result.get('case_name', 'N/A')}")
    print(f"   Preview: {result.get('text', '')[:80]}...")
    print()

print("="*70)
